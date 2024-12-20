import uuid
import openai
import streamlit as st
import streamlit_antd_components as sac
from streamlit_chatbox import *
from streamlit_extras.bottom_container import bottom
from streamlit_paste_button import paste_image_button

from zchat.settings import Settings
from zchat.server.utils import api_address, get_default_llm
from zchat.webui_pages.utils import *


chat_box = ChatBox()


def save_session(conv_name: str = None):
    """save session state to chat context"""
    chat_box.context_from_session(
        conv_name, exclude=["selected_page", "prompt", "cur_conv_name", "upload_image"]
    )


def restore_session(conv_name: str = None):
    """restore sesstion state from chat context"""
    chat_box.context_to_session(
        conv_name, exclude=["selected_page", "prompt", "cur_conv_name", "upload_image"]
    )


def rerun():
    """
    save chat context before rerun
    """
    save_session()
    st.rerun()


def get_messages_history(
    history_len: int, content_in_expander: bool = False
) -> List[Dict]:
    """
    返回消息历史。
    content_in_expander控制是否返回expander元素中的内容，一般导出的时候可以选上，传入LLM的history不需要
    """

    def filter(msg):
        content = [
            x for x in msg["elements"] if x._output_method in ["markdown", "text"]
        ]
        if not content_in_expander:
            content = [x for x in content if not x._in_expander]
        content = [x.content for x in content]

        return {
            "role": msg["role"],
            "content": "\n\n".join(content),
        }

    messages = chat_box.filter_history(history_len=history_len, filter=filter)
    if sys_msg := chat_box.context.get("system_message"):
        messages = [{"role": "system", "content": sys_msg}] + messages

    return messages


@st.cache_data
def upload_temp_docs(files, _api: ApiRequest) -> str:
    """
    将文件上传到临时目录，用于文件对话
    返回临时向量库ID
    """
    return _api.upload_temp_docs(files).get("data", {}).get("id")


@st.cache_data
def upload_image_file(file_name: str, content: bytes) -> dict:
    '''upload image for vision model using openai sdk'''
    client = openai.Client(base_url=f"{api_address()}/v1", api_key="NONE")
    return client.files.create(file=(file_name, content), purpose="assistants").to_dict()


def get_image_file_url(upload_file: dict) -> str:
    file_id = upload_file.get("id")
    return f"{api_address(True)}/v1/files/{file_id}/content"


def add_conv(name: str = ""):
    conv_names = chat_box.get_chat_names()
    if not name:
        i = len(conv_names) + 1
        while True:
            name = f"会话{i}"
            if name not in conv_names:
                break
            i += 1
    if name in conv_names:
        sac.alert(
            "创建新会话出错",
            f"该会话名称 “{name}” 已存在",
            color="error",
            closable=True,
        )
    else:
        chat_box.use_chat_name(name)
        st.session_state["cur_conv_name"] = name


def del_conv(name: str = None):
    conv_names = chat_box.get_chat_names()
    name = name or chat_box.cur_chat_name

    if len(conv_names) == 1:
        sac.alert(
            "删除会话出错", f"这是最后一个会话，无法删除", color="error", closable=True
        )
    elif not name or name not in conv_names:
        sac.alert(
            "删除会话出错", f"无效的会话名称：“{name}”", color="error", closable=True
        )
    else:
        chat_box.del_chat_name(name)
        # restore_session()
    st.session_state["cur_conv_name"] = chat_box.cur_chat_name


def clear_conv(name: str = None):
    chat_box.reset_history(name=name or None)
    

def list_tools(_api: ApiRequest):
    return _api.list_tools() or {}


def dialogue_page(api: ApiRequest):
    ctx = chat_box.context
    ctx.setdefault("uid", uuid.uuid4().hex)
    ctx.setdefault("file_chat_id", None)
    ctx.setdefault("llm_model", get_default_llm())
    ctx.setdefault("temperature", Settings.model_settings["TEMPERATURE"])
    
    with st.sidebar:
        tab1, tab2 = st.tabs(["工具设置", "会话设置"])

        with tab1:
            use_agent = st.checkbox("启用Agent", help="请确保选择的模型具备Agent能力", key="use_agent")
            output_agent = st.checkbox("显示 Agent 过程", key="output_agent")

            # 选择工具
            tools = list_tools(api)
            tool_names = ["None"] + list(tools)
            if use_agent:
                # selected_tools = sac.checkbox(list(tools), format_func=lambda x: tools[x]["title"], label="选择工具",
                # check_all=True, key="selected_tools")
                selected_tools = st.multiselect(
                    "选择工具",
                    list(tools),
                    format_func=lambda x: tools[x]["title"],
                    key="selected_tools",
                )
            else:
                # selected_tool = sac.buttons(list(tools), format_func=lambda x: tools[x]["title"], label="选择工具",
                # key="selected_tool")
                selected_tool = st.selectbox(
                    "选择工具",
                    tool_names,
                    format_func=lambda x: tools.get(x, {"title": "None"})["title"],
                    key="selected_tool",
                )
                selected_tools = [selected_tool]
            selected_tool_configs = {
                name: tool["config"]
                for name, tool in tools.items()
                if name in selected_tools
            }

            if "None" in selected_tools:
                selected_tools.remove("None")
            # 当不启用Agent时，手动生成工具参数
            # TODO: 需要更精细的控制控件
            tool_input = {}
            if not use_agent and len(selected_tools) == 1:
                with st.expander("工具参数", True):
                    for k, v in tools[selected_tools[0]]["args"].items():
                        if choices := v.get("choices", v.get("enum")):
                            tool_input[k] = st.selectbox(v["title"], choices)
                        else:
                            if v["type"] == "integer":
                                tool_input[k] = st.slider(
                                    v["title"], value=v.get("default")
                                )
                            elif v["type"] == "number":
                                tool_input[k] = st.slider(
                                    v["title"], value=v.get("default"), step=0.1
                                )
                            else:
                                tool_input[k] = st.text_input(
                                    v["title"], v.get("default")
                                )

            # uploaded_file = st.file_uploader("上传附件", accept_multiple_files=False)
            # files_upload = process_files(files=[uploaded_file]) if uploaded_file else None
            files_upload = None

            # 用于图片对话、文生图的图片
            upload_image = None
            def on_upload_file_change():
                if f := st.session_state.get("upload_image"):
                    name = ".".join(f.name.split(".")[:-1]) + ".png"
                    st.session_state["cur_image"] = (name, PILImage.open(f))
                else:
                    st.session_state["cur_image"] = (None, None)
                st.session_state.pop("paste_image", None)

            st.file_uploader("上传图片", ["bmp", "jpg", "jpeg", "png"],
                                            accept_multiple_files=False,
                                            key="upload_image",
                                            on_change=on_upload_file_change)
            paste_image = paste_image_button("黏贴图像", key="paste_image")
            cur_image = st.session_state.get("cur_image", (None, None))
            if cur_image[1] is None and paste_image.image_data is not None:
                name = hashlib.md5(paste_image.image_data.tobytes()).hexdigest()+".png"
                cur_image = (name, paste_image.image_data) 
            if cur_image[1] is not None:
                st.image(cur_image[1])
                buffer = io.BytesIO()
                cur_image[1].save(buffer, format="png")
                upload_image = upload_image_file(cur_image[0], buffer.getvalue())
    
    chat_box.output_messages()
    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter。"
    
    with bottom():
        cols = st.columns([1, 0.2, 15,  1])
        prompt = cols[2].chat_input(chat_input_placeholder, key="prompt")
        
    if prompt:
        chat_box.user_say(prompt)
        chat_box.ai_say("正在思考...")
        
        # client = openai.Client(base_url="http://192.168.31.114:9997/v1", api_key="NONE")
        client = openai.Client(base_url=f"{api_address()}/chat", api_key="NONE")
        
        messages = [{"role": "user", "content": prompt}]
        
        conversation_id = chat_box.context["uid"]
        extra_body = dict(
            conversation_id=conversation_id,
        )
        
        params = dict(
            messages=messages,
            model="Qwen2.5-1.5B-Instruct-local",
            extra_body=extra_body,
        )
        
        try:
            d = client.chat.completions.create(**params)
            chat_box.update_msg(d.choices[0].message.content or "", streaming=False)
        except Exception as e:
            st.error(e.body)
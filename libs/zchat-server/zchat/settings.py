import yaml


XF_MODELS_TYPES = {
    "text2image": {"model_family": ["stable_diffusion"]},
    "image2image": {"model_family": ["stable_diffusion"]},
    "speech2text": {"model_family": ["whisper"]},
    "text2speech": {"model_family": ["ChatTTS"]},
}


# yaml文件加载
def load_yaml(path: str):
    with open(path, "r", encoding='utf-8') as f:
        data = f.read()
        
    yaml_data = yaml.safe_load(data)
    return yaml_data


class SettingsContainer:
    
    def __init__(self):
        self.load_all_settings()
    
    def load_all_settings(self):
        self.basic_settings = load_yaml("./zchat/settings/basic_settings.yaml")
        self.kb_settings = load_yaml("./zchat/settings/kb_settings.yaml")
        self.model_settings = load_yaml("./zchat/settings/model_settings.yaml")
        self.prompt_settings = load_yaml("./zchat/settings/prompt_settings.yaml")
        self.tool_settings = load_yaml("./zchat/settings/tool_settings.yaml")
        
        
Settings = SettingsContainer()
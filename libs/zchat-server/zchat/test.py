import subprocess
import threading
import sys
from pyngrok import ngrok
from rich import print as rprint
from rich.panel import Panel

 
#! SET Ngrok Authtoken Here
ngrok.set_auth_token("2pqO1srnCs9rKjLkXAvfuDCB6mp_41SrvSSbrrkR4C7FLes3U")
 
def print_output(process):
    for line in iter(process.stdout.readline, ''):
        sys.stdout.write(line)
    for line in iter(process.stderr.readline, ''):
        sys.stderr.write(line)
 
# Start Streamlit
streamlit_process = subprocess.Popen(
    ["xinference-local"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
    bufsize=1
)
 
# Create and start the output printing thread
output_thread = threading.Thread(target=print_output, args=(streamlit_process,))
output_thread.start()
 
# Create a tunnel using ngrok
public_url = ngrok.connect(9997)
rprint(Panel(f"Streamlit is available at Ngrok ⬇️", expand=False))
print(f"Click 👉 {public_url}")
 
# Keep the program running
ngrok_process = ngrok.get_ngrok_process()
try:
    streamlit_process.wait()
except KeyboardInterrupt:
    print("Interrupted by user, shutting down...")
finally:
    ngrok.kill()
    streamlit_process.terminate()
    output_thread.join()
import webview
import threading
import uvicorn
from main import app

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == '__main__':
    # बैकग्राउंड में सर्वर स्टार्ट
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    # GUI विंडो बनाएं और वेब ऐप को लोड करें
    webview.create_window(
        title="⚡ Information Chaos Engine // Autonomous Intelligence",
        url="http://127.0.0.1:8000",
        width=1280,
        height=820,
        resizable=True
    )
    webview.start()
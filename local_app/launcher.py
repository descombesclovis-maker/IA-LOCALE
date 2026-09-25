import os, sys, time, threading, json, traceback
from pathlib import Path
from urllib.request import urlopen
from contextlib import redirect_stdout, redirect_stderr

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
os.environ["LOCALVISIONAI_DATA"] = str(DATA)
LOG_DIR = DATA / "logs"
LOG_FILE = LOG_DIR / "startup.log"


def wait_for_server(timeout=900):
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            with urlopen("http://127.0.0.1:3000/api/health",timeout=3) as r:
                if r.status==200:
                    data=json.loads(r.read().decode("utf-8"))
                    if data.get("online") and (data.get("llm") or {}).get("online"):
                        return True
        except Exception:
            pass
        time.sleep(1)
    return False


def show_error(message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "LocalVisionAI", 0x10)
    except Exception:
        pass


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            print("\n=== LocalVisionAI démarrage ===")
            print("Python:", sys.executable)
            print("Root:", ROOT)
            print("Data:", DATA)
            try:
                from local_app import bootstrap_windows
                bootstrap_windows.run()

                import local_app.server as server
                server_thread=threading.Thread(target=server.main,daemon=True)
                server_thread.start()
                if not wait_for_server():
                    raise RuntimeError("Les moteurs locaux n'ont pas répondu dans le délai prévu.")

                import webview
                window=webview.create_window("LocalVisionAI","http://127.0.0.1:3000",width=1440,height=920,
                                              min_size=(1100,700),resizable=True,background_color="#090909")
                webview.start(debug=False)
            except Exception as exc:
                traceback.print_exc()
                message = "LocalVisionAI n’a pas pu démarrer.\n\nConsulte le journal :\n" + str(LOG_FILE) + "\n\nErreur : " + str(exc)
                show_error(message)
                raise


if __name__=="__main__":
    main()

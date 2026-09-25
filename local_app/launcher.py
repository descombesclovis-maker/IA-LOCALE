import os, sys, time, threading, json, traceback
from pathlib import Path
from urllib.request import urlopen
from contextlib import redirect_stdout, redirect_stderr

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
os.environ["LOCALVISIONAI_DATA"] = str(DATA)
LOG_DIR = DATA / "logs"
LOG_FILE = LOG_DIR / "startup.log"


def wait_for_server_interface(timeout=60):
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            with urlopen("http://127.0.0.1:3000/api/health",timeout=3) as r:
                if r.status==200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
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
                # The server/UI must never wait for multi-GB first-run downloads.
                import local_app.server as server
                threading.Thread(target=server.main, daemon=True).start()
                if not wait_for_server_interface():
                    raise RuntimeError("Le serveur LocalVisionAI n'a pas répondu dans le délai prévu.")

                import webview
                webview.create_window(
                    "LocalVisionAI", "http://127.0.0.1:3000",
                    width=1440, height=920, min_size=(1100,700),
                    resizable=True, background_color="#090909"
                )
                webview.start(debug=False)
            except Exception as exc:
                traceback.print_exc()
                show_error("LocalVisionAI n’a pas pu démarrer.\n\nConsulte le journal :\n"
                           + str(LOG_FILE) + "\n\nErreur : " + str(exc))
                raise


if __name__=="__main__":
    main()

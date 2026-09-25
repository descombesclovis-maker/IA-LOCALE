import os, sys, time, subprocess, json, traceback
from pathlib import Path
from urllib.request import urlopen
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
os.environ["LOCALVISIONAI_DATA"] = str(DATA)
LOG_DIR = DATA / "logs"
LOG_FILE = LOG_DIR / "startup.log"


def wait_for_interface(timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen("http://127.0.0.1:3000/api/health", timeout=2) as r:
                if r.status == 200:
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


def run_server():
    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            print("\n=== LocalVisionAI SERVER ===", flush=True)
            try:
                import local_app.server as server
                server.main()
            except Exception:
                traceback.print_exc()
                raise


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    server_process = None
    try:
        # In a frozen EXE the server gets its own process. This prevents
        # background-thread/import failures from silently killing the server.
        executable = Path(sys.executable).resolve()
        if getattr(sys, "frozen", False):
            cmd = [str(executable), "--server"]
        else:
            cmd = [str(executable), str(Path(__file__).resolve()), "--server"]

        DATA.mkdir(parents=True, exist_ok=True)
        server_log = open(LOG_FILE, "a", encoding="utf-8")
        server_process = subprocess.Popen(
            cmd,
            cwd=str(DATA.resolve()),
            executable=str(executable),
            stdout=server_log,
            stderr=server_log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            close_fds=False
        )

        if not wait_for_interface():
            code = server_process.poll()
            raise RuntimeError(
                "Le serveur local n'a pas répondu. "
                + ("Le processus serveur s'est arrêté (code %s)." % code if code is not None
                   else "Le processus serveur est toujours lancé mais le port 3000 ne répond pas.")
            )

        import webview
        window = webview.create_window(
            "LocalVisionAI", "http://127.0.0.1:3000",
            width=1440, height=920, min_size=(1100, 700),
            resizable=True, background_color="#090909"
        )

        def cleanup():
            if server_process and server_process.poll() is None:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except Exception:
                    server_process.kill()
            try:
                server_log.close()
            except Exception:
                pass

        window.events.closed += cleanup
        webview.start(debug=False)

    except Exception as exc:
        traceback_text = traceback.format_exc()
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write("\n=== ERREUR LAUNCHER ===\n" + traceback_text)
        except Exception:
            pass
        show_error(
            "LocalVisionAI n’a pas pu démarrer.\n\n"
            "Journal :\n" + str(LOG_FILE) + "\n\n"
            + str(exc)
        )
        if server_process and server_process.poll() is None:
            server_process.terminate()
        raise


if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    else:
        main()

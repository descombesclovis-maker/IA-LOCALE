import os, sys, time, json, traceback, multiprocessing
from pathlib import Path
from urllib.request import urlopen
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = Path(os.environ.get("LOCALVISIONAI_DATA",
             str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LocalVisionAI")))
os.environ["LOCALVISIONAI_DATA"] = str(DATA)
LOG_DIR = DATA / "logs"
LOG_FILE = LOG_DIR / "startup.log"


def show_error(message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "LocalVisionAI", 0x10)
    except Exception:
        pass


def server_entry():
    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            print("\n=== LocalVisionAI SERVER PROCESS ===", flush=True)
            try:
                from local_app import server
                server.main()
            except BaseException:
                traceback.print_exc()
                raise


def wait_for_interface(process, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not process.is_alive():
            return False, "Le processus serveur s'est arrêté avant d'ouvrir le port 3000."
        try:
            with urlopen("http://127.0.0.1:3000/api/health", timeout=2) as response:
                if response.status == 200:
                    return True, None
        except Exception:
            pass
        time.sleep(0.5)
    return False, "Le serveur local n'a pas répondu sur 127.0.0.1:3000 dans le délai prévu."


def main():
    multiprocessing.freeze_support()
    DATA.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    server_process = None
    try:
        # IMPORTANT: do not launch the EXE recursively with Popen.
        # Windows/PyInstaller can interpret the generated path incorrectly.
        # multiprocessing uses the frozen application bootstrap safely.
        from local_app import server
        server_process = multiprocessing.Process(
            target=server_entry,
            name="LocalVisionAI-Server",
            daemon=False
        )
        server_process.start()

        ok, error = wait_for_interface(server_process)
        if not ok:
            raise RuntimeError(error)

        import webview
        window = webview.create_window(
            "LocalVisionAI",
            "http://127.0.0.1:3000",
            width=1440,
            height=920,
            min_size=(1100, 700),
            resizable=True,
            background_color="#090909"
        )

        def cleanup():
            if server_process and server_process.is_alive():
                server_process.terminate()
                server_process.join(timeout=8)
                if server_process.is_alive():
                    server_process.kill()

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
            "LocalVisionAI n'a pas pu démarrer.\n\n"
            "Journal :\n" + str(LOG_FILE) + "\n\n"
            + str(exc)
        )

        if server_process and server_process.is_alive():
            server_process.terminate()
        raise


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

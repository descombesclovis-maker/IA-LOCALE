import base64, json, mimetypes, os, re, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "local_app" / "web"
IMPORTED = ROOT / "workflows" / "imported"
IMPORTED.mkdir(parents=True, exist_ok=True)
HOST = "127.0.0.1"
PORT = 3000
COMFY = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
_comfy_info_cache = {"time": 0, "data": {}}

IGNORE_JSON = {"package.json", "tsconfig.json", "config.json"}

def http_json(url, method="GET", payload=None, timeout=20, headers=None):
    data = None
    hdr = {"Content-Type": "application/json"}
    if headers:
        hdr.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=hdr, method=method)
    with urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw.decode("utf-8")) if raw else {}

def comfy_get(path):
    return http_json(COMFY + path)

def comfy_post(path, payload):
    return http_json(COMFY + path, "POST", payload, timeout=60)

def _candidate_comfy_roots():
    here = Path(__file__).resolve().parent.parent
    roots = [
        here / "engine" / "ComfyUI",
        here / "ComfyUI",
        Path(os.environ.get("LOCALAPPDATA", "")) / "LocalVisionAI" / "ComfyUI",
        Path.home() / "ComfyUI",
        Path("D:/IA LOCAL/ComfyUI"),
    ]
    seen = set()
    for root in roots:
        try:
            key = str(root.resolve()).lower()
        except Exception:
            key = str(root).lower()
        if key not in seen:
            seen.add(key)
            yield root

def _comfy_launcher(root):
    for name in ("run_nvidia_gpu.bat", "run_cpu.bat", "run_amd_gpu.bat", "run_intel_gpu.bat"):
        p = root / name
        if p.exists():
            return ("bat", p)
    for name in ("main.py",):
        p = root / name
        if p.exists():
            return ("python", p)
    return (None, None)

def ensure_comfyui(timeout=90):
    online, _ = comfy_online()
    if online:
        return True
    for root in _candidate_comfy_roots():
        kind, launcher = _comfy_launcher(root)
        if not launcher:
            continue
        try:
            if kind == "bat":
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", '""', "/b", str(launcher)],
                    cwd=str(root),
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            else:
                py = root / "python_embeded" / "python.exe"
                if not py.exists():
                    py = sys.executable
                subprocess.Popen(
                    [str(py), str(launcher), "--listen", HOST, "--port", "8188"],
                    cwd=str(root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            deadline = time.time() + timeout
            while time.time() < deadline:
                online, _ = comfy_online()
                if online:
                    return True
                time.sleep(1)
        except Exception:
            continue
    return False

def comfy_online():
    try:
        data = comfy_get("/system_stats")
        return True, data
    except Exception as e:
        return False, str(e)

def object_info():
    now = time.time()
    if now - _comfy_info_cache["time"] < 20 and _comfy_info_cache["data"]:
        return _comfy_info_cache["data"]
    try:
        data = comfy_get("/object_info")
        _comfy_info_cache["time"] = now
        _comfy_info_cache["data"] = data
        return data
    except Exception:
        return {}

def scan_workflows():
    out = []
    for p in ROOT.rglob("*.json"):
        if "node_modules" in p.parts or ".git" in p.parts:
            continue
        if p.name in IGNORE_JSON:
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and ("nodes" in raw or all(isinstance(v, dict) and "class_type" in v for v in raw.values())):
                rel = p.relative_to(ROOT).as_posix()
                out.append(workflow_card(rel, raw))
        except Exception:
            pass
    return sorted(out, key=lambda x: x["name"].lower())

def workflow_card(rel, wf):
    name = Path(rel).stem
    low = name.lower()
    if "ltx" in low:
        kind, icon = "video-heavy", "🎞️"
    elif "video" in low or "wan" in low:
        kind, icon = "video", "🎬"
    elif "retouch" in low or "retouche" in low or "inpaint" in low or "img2img" in low:
        kind, icon = "retouch", "✨"
    else:
        kind, icon = "image", "🖼️"
    return {"id": rel, "name": name, "kind": kind, "icon": icon, "node_count": len(wf.get("nodes", wf)) if isinstance(wf, dict) else 0}

def load_workflow(rel):
    p = (ROOT / rel).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise ValueError("Chemin de workflow invalide")
    if p.suffix.lower() != ".json" or not p.exists():
        raise FileNotFoundError(rel)
    return json.loads(p.read_text(encoding="utf-8"))

def is_api_workflow(wf):
    return isinstance(wf, dict) and bool(wf) and all(isinstance(v, dict) and "class_type" in v for v in wf.values())

def is_control_value(v):
    return isinstance(v, str) and v in {"fixed", "randomize", "increment", "decrement"}

def widget_names_from_info(node_type, info):
    spec = info.get(node_type, {}) if isinstance(info, dict) else {}
    order = spec.get("input_order", {}) or {}
    names = []
    for section in ("required", "optional"):
        names.extend(order.get(section, []) or [])
    inputs = spec.get("input", {}) or {}
    result = []
    for n in names:
        definition = None
        for section in ("required", "optional"):
            definition = (inputs.get(section, {}) or {}).get(n)
            if definition is not None:
                break
        if isinstance(definition, list) and definition:
            typ = definition[0]
            is_widget = isinstance(typ, list) or typ in {"INT","FLOAT","STRING","BOOLEAN","COMBO"} or (isinstance(typ, str) and (typ.startswith("COMFY_") or not typ.isupper()))
            if is_widget:
                result.append(n)
    return result

def convert_ui_to_api(wf):
    if is_api_workflow(wf):
        return json.loads(json.dumps(wf))
    nodes = {str(n["id"]): n for n in wf.get("nodes", []) if isinstance(n, dict)}
    info = object_info()
    link_map = {}
    for row in wf.get("links", []) or []:
        if len(row) >= 6:
            link_id, src_id, src_slot, dst_id, dst_slot = row[:5]
            link_map[int(link_id)] = (str(src_id), int(src_slot), str(dst_id), int(dst_slot))
    api = {}
    for nid, node in nodes.items():
        node_type = node.get("type")
        if not node_type or node_type in {"Note", "MarkdownNote", "Reroute", "PrimitiveNode"}:
            continue
        # UI subgraphs/custom nodes are valid if ComfyUI exposes them.
        if node_type not in info and not node.get("inputs"):
            continue
        inputs = {}
        target_inputs = node.get("inputs", []) or []
        for item in target_inputs:
            if not isinstance(item, dict):
                continue
            link = item.get("link")
            if link is not None and int(link) in link_map:
                src, slot, _, _ = link_map[int(link)]
                inputs[item.get("name")] = [src, slot]
        named = node.get("widgets_values_named")
        if isinstance(named, dict):
            for k, v in named.items():
                if k not in inputs and not is_control_value(v):
                    inputs[k] = v
        else:
            vals = node.get("widgets_values")
            if isinstance(vals, list):
                names = widget_names_from_info(node_type, info)
                if not names:
                    names = [x.get("widget",{}).get("name") for x in target_inputs if isinstance(x,dict) and isinstance(x.get("widget"),dict)]
                    names = [x for x in names if x]
                vi = 0
                for val in vals:
                    if is_control_value(val):
                        continue
                    while vi < len(names) and names[vi] in inputs:
                        vi += 1
                    if vi >= len(names):
                        break
                    inputs[names[vi]] = val
                    vi += 1
        api[nid] = {"class_type": node_type, "inputs": inputs, "_meta": {"title": node.get("title") or node.get("properties",{}).get("Node name for S&R", node_type)}}
    return api

def apply_user_inputs(api, prompt="", negative="", image_ref=None, settings=None):
    settings = settings or {}
    text_nodes = []
    for nid, node in api.items():
        if node.get("class_type") == "CLIPTextEncode":
            text_nodes.append((nid, node))
    for nid, node in text_nodes:
        title = (node.get("_meta", {}).get("title") or "").lower()
        if "negative" in title:
            if negative:
                node["inputs"]["text"] = negative
        elif prompt:
            node["inputs"]["text"] = prompt
    # Custom video nodes: use obvious prompt/text inputs when present.
    if prompt:
        for nid, node in api.items():
            if node.get("class_type") == "CLIPTextEncode":
                continue
            for key in list(node.get("inputs", {})):
                k = key.lower()
                if k in {"prompt","text","positive_prompt","prompt_text","description"} or k.endswith("_prompt"):
                    val = node["inputs"][key]
                    if not isinstance(val, list) and isinstance(val, str):
                        node["inputs"][key] = prompt
                        break
    if image_ref:
        for nid, node in api.items():
            ct = node.get("class_type","").lower()
            for key in list(node.get("inputs", {})):
                k = key.lower()
                if k in {"image","start_image","input_image","init_image"} and not isinstance(node["inputs"][key], list):
                    node["inputs"][key] = image_ref["name"]
                    break
    if "seed" in settings:
        for node in api.values():
            if "seed" in node.get("inputs", {}) and not isinstance(node["inputs"]["seed"], list):
                node["inputs"]["seed"] = int(settings["seed"])
    aspect = settings.get("aspect")
    dims = {"1:1": (1024,1024), "16:9": (1344,768), "9:16": (768,1344), "4:3": (1152,864), "3:4": (864,1152)}
    if aspect in dims:
        width, height = dims[aspect]
        for node in api.values():
            inp = node.get("inputs", {})
            if "width" in inp and not isinstance(inp["width"], list): inp["width"] = width
            if "height" in inp and not isinstance(inp["height"], list): inp["height"] = height
    quality = settings.get("quality")
    steps = {"draft": 12, "balanced": 24, "quality": 36}.get(quality)
    if steps:
        for node in api.values():
            inp = node.get("inputs", {})
            if "steps" in inp and not isinstance(inp["steps"], list): inp["steps"] = steps
    return api

def upload_image(filename, data):
    boundary = "----LocalVisionAI" + uuid.uuid4().hex
    body = bytearray()
    def add_field(name, value):
        body.extend((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode())
    body.extend((f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode())
    body.extend(data)
    body.extend(f"\r\n".encode())
    add_field("type","input")
    add_field("overwrite","true")
    body.extend(f"--{boundary}--\r\n".encode())
    req = Request(COMFY + "/upload/image", data=bytes(body), headers={"Content-Type":f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def queue_prompt(api):
    return comfy_post("/prompt", {"prompt": api, "client_id": str(uuid.uuid4())})

def history(prompt_id):
    return comfy_get("/history/" + quote(prompt_id))

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_bytes(self, data, content_type="application/octet-stream", status=200):
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/health":
            ensure_comfyui(timeout=3)
            online, detail = comfy_online()
            self.send_json({"online":online,"detail":detail,"url":COMFY})
            return
        if u.path == "/api/workflows":
            self.send_json({"workflows":scan_workflows()})
            return
        if u.path == "/api/workflow":
            rel = parse_qs(u.query).get("id",[None])[0]
            try: self.send_json({"workflow":load_workflow(rel)})
            except Exception as e: self.send_json({"error":str(e)},400)
            return
        if u.path.startswith("/api/history/"):
            pid = u.path.split("/",3)[3]
            try: self.send_json(history(pid))
            except Exception as e: self.send_json({"error":str(e)},502)
            return
        if u.path == "/api/view":
            q = parse_qs(u.query)
            try:
                filename=q.get("filename",[""])[0]; sub=q.get("subfolder",[""])[0]; typ=q.get("type",["output"])[0]
                params=f"?filename={quote(filename)}&subfolder={quote(sub)}&type={quote(typ)}"
                with urlopen(COMFY+"/view"+params,timeout=60) as r:
                    self.send_bytes(r.read(),r.headers.get_content_type())
            except Exception as e: self.send_json({"error":str(e)},502)
            return
        if u.path.startswith("/api/asset"):
            # Kept as a stable namespace for future local asset management.
            self.send_json({"ok":True})
            return
        if u.path == "/" or u.path.startswith("/assets/"):
            rel = "index.html" if u.path=="/" else u.path[len("/assets/"):]
            p = WEB / rel
            if not p.exists() or not p.is_file():
                self.send_response(404); self.end_headers(); return
            data=p.read_bytes()
            c=mimetypes.guess_type(str(p))[0] or "application/octet-stream"
            self.send_bytes(data,c)
            return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        u=urlparse(self.path)
        length=int(self.headers.get("Content-Length","0"))
        raw=self.rfile.read(length)
        try: body=json.loads(raw.decode())
        except Exception:
            self.send_json({"error":"JSON invalide"},400); return
        if u.path == "/api/import-workflow":
            try:
                name=Path(body.get("name","workflow.json")).name
                if not name.lower().endswith(".json"): name += ".json"
                dest=IMPORTED/name
                dest.write_text(json.dumps(body["workflow"],ensure_ascii=False,indent=2),encoding="utf-8")
                self.send_json({"ok":True,"id":dest.relative_to(ROOT).as_posix()})
            except Exception as e: self.send_json({"error":str(e)},400)
            return
        if u.path == "/api/upload":
            try:
                b64=body["data"].split(",",1)[-1]
                result=upload_image(Path(body.get("name","input.png")).name,base64.b64decode(b64))
                self.send_json({"ok":True,"file":result})
            except Exception as e: self.send_json({"error":str(e)},502)
            return
        if u.path == "/api/generate":
            try:
                ok=ensure_comfyui(timeout=90)
                if not ok: raise RuntimeError("Le moteur local ComfyUI est introuvable. Place le moteur dans LocalVisionAI/ComfyUI ou utilise l'installateur autonome.")
                wf=load_workflow(body["workflow"])
                api=convert_ui_to_api(wf)
                if not api: raise RuntimeError("Workflow vide ou non convertible")
                image_ref=None
                if body.get("image"):
                    b64=body["image"].split(",",1)[-1]
                    image_ref=upload_image(Path(body.get("image_name","input.png")).name,base64.b64decode(b64))
                api=apply_user_inputs(api,body.get("prompt",""),body.get("negative",""),image_ref,body.get("settings"))
                result=queue_prompt(api)
                self.send_json({"ok":True,"prompt_id":result.get("prompt_id"),"queue":result})
            except HTTPError as e:
                try: detail=e.read().decode()
                except: detail=str(e)
                self.send_json({"error":detail},502)
            except Exception as e:
                self.send_json({"error":str(e)},400)
            return
        if u.path == "/api/interrupt":
            try: self.send_json(comfy_post("/interrupt","{}" if False else {}))
            except Exception as e: self.send_json({"error":str(e)},502)
            return
        self.send_response(404); self.end_headers()

def main():
    print(f"LocalVisionAI -> http://{HOST}:{PORT}")
    threading.Thread(target=ensure_comfyui, kwargs={"timeout":90}, daemon=True).start()
    print(f"ComfyUI      -> {COMFY}")
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__":
    main()

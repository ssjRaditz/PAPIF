import os
import sys
import json
import re
import threading
import http.server
import socketserver
import webview  # Run: pip install pywebview

# ── RESOURCE PATH HELPER FOR PYINSTALLER ──
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ── FILE PATH CONFIGURATIONS ──
# We wrap these in get_resource_path so they work seamlessly when bundled
PLANTS_FILE        = get_resource_path("plants.txt")
PLANTS_IMG_DIR     = get_resource_path("plant_images")
PLANTS_CACHE_FILE   = get_resource_path("plant_image_data.js")

PEST_FILE          = get_resource_path("pests.txt")
PESTS_IMG_DIR      = get_resource_path("pest_images")
PESTS_CACHE_FILE   = get_resource_path("pest_image_data.js")


# ── CORE FUNCTIONS FROM YOUR ORIGINAL IMAGE_LOADER ──
def clean_to_common(name):
    return re.sub(r"X |× | cv\.$| subsp\. .+| var\. .+|'[^']*'", "", name).strip()

def load_items_from_file(filepath):
    items = []
    if not os.path.exists(filepath):
        print(f"❌ ERROR: Config file '{filepath}' not found!")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                str_id, name = line.split(",", 1)
                try:
                    items.append((int(str_id.strip()), name.strip()))
                except ValueError:
                    pass
    return items

def find_local_images(item_id, img_dir):
    if not os.path.exists(img_dir):
        return None, None
    str_id = str(item_id)
    try:
        files = os.listdir(img_dir)
    except Exception:
        return None, None

    def match(prefix):
        for f in files:
            name, _ = os.path.splitext(f)
            if name == prefix:
                return f
        return None

    img1 = match(str_id + "a") or match(str_id)
    img2 = match(str_id + "b")
    return img1, img2

def process_cache(items_file, img_dir, cache_file, cache_var, img_subfolder):
    items = load_items_from_file(items_file)
    if not items:
        return

    results = {}
    for item_id, name in items:
        str_id = str(item_id)
        f1, f2 = find_local_images(item_id, img_dir)
        common = clean_to_common(name)

        if f1 or f2:
            results[str_id] = {
                "url":  f"{img_subfolder}/{f1}" if f1 else f"{img_subfolder}/{f2}",
                "url1": f"{img_subfolder}/{f1}" if f1 else None,
                "url2": f"{img_subfolder}/{f2}" if f2 else None,
                "common": common
            }
        else:
            results[str_id] = None

    lines = ["// Auto-generated — do not edit manually", f"window.{cache_var} = {{"]
    for iid, info in sorted(results.items(), key=lambda x: int(x[0])):
        if info:
            entry = {
                "url":    info.get("url1") or info.get("url2"),
                "url1":   info.get("url1"),
                "url2":   info.get("url2"),
                "common": info.get("common", "")
            }
            entry = {k: v for k, v in entry.items() if v is not None}
            lines.append(f"  {iid}: {json.dumps(entry)},")
        else:
            lines.append(f"  {iid}: 'error',")
    lines.append("};")

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── LOCAL HTTP SERVER ──
PORT = 8080
class SafeHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=get_resource_path("."), **kwargs)

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SafeHTTPHandler) as httpd:
        httpd.serve_forever()


# ── MAIN RUNNER ──
if __name__ == "__main__":
    # 1. Generate runtime JS caches directly from your text files
    process_cache(PLANTS_FILE, PLANTS_IMG_DIR, PLANTS_CACHE_FILE, "PLANT_IMAGE_CACHE", "plant_images")
    process_cache(PEST_FILE, PESTS_IMG_DIR, PESTS_CACHE_FILE, "PEST_IMAGE_CACHE", "pest_images")
    
    # 2. Spin up background local server
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 3. Create Desktop Application Window
    webview.create_window(
        "Plant & Pest Identification Flashcards", 
        f"http://localhost:{PORT}/PAPIF.html",
        width=950, 
        height=750
    )
    webview.start()
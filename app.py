import os
import shutil
from flask import Flask, jsonify, request, send_from_directory, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
DEST_DIR = os.path.join(BASE_DIR, "rare class images")

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}

app = Flask(__name__)


def get_images():
    if not os.path.isdir(DATASET_DIR):
        return []
    files = sorted(
        f for f in os.listdir(DATASET_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
    )
    return files


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Image Sorter</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #111;
    color: #eee;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
  }

  #status {
    font-size: 13px;
    color: #888;
    letter-spacing: 0.05em;
  }

  #filename {
    font-size: 14px;
    color: #bbb;
    max-width: 600px;
    text-align: center;
    word-break: break-all;
  }

  #img-container {
    width: min(90vw, 800px);
    height: min(60vh, 550px);
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1a1a1a;
    border-radius: 8px;
    overflow: hidden;
  }

  #img-container img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
  }

  #done-msg {
    font-size: 22px;
    color: #4caf50;
    display: none;
  }

  #controls {
    display: flex;
    gap: 12px;
  }

  button {
    padding: 10px 28px;
    border: none;
    border-radius: 6px;
    font-size: 15px;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
  }

  button:active { transform: scale(0.97); }
  button:disabled { opacity: 0.35; cursor: default; }

  #btn-copy {
    background: #4caf50;
    color: #fff;
    font-weight: 600;
  }

  #btn-copy:hover:not(:disabled) { background: #43a047; }

  #btn-skip {
    background: #333;
    color: #ccc;
  }

  #btn-skip:hover:not(:disabled) { background: #444; }

  #hint {
    font-size: 12px;
    color: #555;
  }
</style>
</head>
<body>

<div id="status">Loading...</div>
<div id="filename"></div>

<div id="img-container">
  <img id="img" src="" alt="">
  <div id="done-msg">All images reviewed!</div>
</div>

<div id="controls">
  <button id="btn-copy" onclick="copyImage()">Add to Rare Class</button>
  <button id="btn-skip" onclick="skipImage()">Skip</button>
</div>

<div id="hint">Keyboard: <strong>C</strong> to copy &nbsp;|&nbsp; <strong>S</strong> or <strong>→</strong> to skip</div>

<script>
let images = [];
let index = 0;
let copied = 0;

async function init() {
  const res = await fetch("/api/images");
  images = await res.json();
  if (images.length === 0) {
    document.getElementById("status").textContent = "No images found in dataset/";
    document.getElementById("controls").style.display = "none";
    document.getElementById("hint").style.display = "none";
    return;
  }
  showImage();
}

function showImage() {
  if (index >= images.length) {
    document.getElementById("img").style.display = "none";
    document.getElementById("done-msg").style.display = "block";
    document.getElementById("controls").style.display = "none";
    document.getElementById("hint").style.display = "none";
    document.getElementById("status").textContent = `Done — ${copied} of ${images.length} copied to "rare class images"`;
    document.getElementById("filename").textContent = "";
    return;
  }
  const name = images[index];
  document.getElementById("img").src = "/dataset/" + encodeURIComponent(name);
  document.getElementById("img").style.display = "block";
  document.getElementById("done-msg").style.display = "none";
  document.getElementById("filename").textContent = name;
  document.getElementById("status").textContent =
    `Image ${index + 1} of ${images.length}  •  ${copied} copied`;
  document.getElementById("btn-copy").disabled = false;
  document.getElementById("btn-skip").disabled = false;
}

async function copyImage() {
  document.getElementById("btn-copy").disabled = true;
  document.getElementById("btn-skip").disabled = true;
  const name = images[index];
  const res = await fetch("/api/copy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: name })
  });
  const data = await res.json();
  if (!data.ok) {
    alert("Error: " + data.error);
    document.getElementById("btn-copy").disabled = false;
    document.getElementById("btn-skip").disabled = false;
    return;
  }
  copied++;
  index++;
  showImage();
}

function skipImage() {
  index++;
  showImage();
}

document.addEventListener("keydown", e => {
  if (e.key === "c" || e.key === "C") copyImage();
  if (e.key === "s" || e.key === "S" || e.key === "ArrowRight") skipImage();
});

init();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/dataset/<path:filename>")
def serve_dataset(filename):
    return send_from_directory(DATASET_DIR, filename)


@app.route("/api/images")
def api_images():
    return jsonify(get_images())


@app.route("/api/copy", methods=["POST"])
def api_copy():
    data = request.get_json()
    filename = data.get("filename", "")
    if not filename or "/" in filename or ".." in filename:
        return jsonify({"ok": False, "error": "Invalid filename"})
    src = os.path.join(DATASET_DIR, filename)
    if not os.path.isfile(src):
        return jsonify({"ok": False, "error": "File not found"})
    os.makedirs(DEST_DIR, exist_ok=True)
    dst = os.path.join(DEST_DIR, filename)
    shutil.copy2(src, dst)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print(f"Dataset:     {DATASET_DIR}")
    print(f"Destination: {DEST_DIR}")
    print("Open http://localhost:5000")
    app.run(debug=True, port=5000)

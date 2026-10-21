"""ScreenArt viewer — Flask server."""
import json
import logging
import shutil
from threading import Lock

from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from config import (
    HEARTED_QUEUE,
    HOST,
    IMAGES_DIR,
    IMAGE_EXTENSIONS,
    PORT,
    SAVED_JSON,
)

app = Flask(__name__)

# Single lock guards saved.json + HeartedQueue mutations.
state_lock = Lock()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def safe_filename(name: str) -> str:
    """Reject path traversal and null bytes. Return name if safe, else abort."""
    if not name:
        abort(400, "no filename")
    if "/" in name or "\\" in name or ".." in name or "\x00" in name:
        abort(400, "invalid filename")
    return name


def read_saved() -> list:
    if not SAVED_JSON.exists():
        return []
    try:
        return json.loads(SAVED_JSON.read_text())
    except Exception:
        log.exception("could not read saved.json, treating as empty")
        return []


def write_saved_atomic(data: list) -> None:
    """Write saved.json atomically — write to tmp, then rename."""
    SAVED_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = SAVED_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(SAVED_JSON)


def list_images() -> list:
    """All images in TransformedImages, newest first by mtime.

    Skips dot-files including iCloud .foo.jpeg.icloud placeholder stubs
    (files that iCloud has evicted from local disk).
    """
    if not IMAGES_DIR.exists():
        log.warning("images dir does not exist: %s", IMAGES_DIR)
        return []
    files = [
        p for p in IMAGES_DIR.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in files]


@app.route("/")
def index():
    files = list_images()
    hearted = read_saved()
    return render_template(
        "index.html",
        files=files,
        hearted=set(hearted),
        count=len(files),
    )


@app.route("/images/<path:filename>")
def serve_image(filename: str):
    safe_filename(filename)
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/api/list")
def api_list():
    return jsonify(read_saved())


@app.route("/api/heart", methods=["POST"])
def api_heart():
    data = request.get_json(silent=True) or {}
    filename = safe_filename(data.get("file", ""))

    src = IMAGES_DIR / filename
    if not src.exists():
        abort(404, "file not in gallery")

    with state_lock:
        saved = read_saved()
        if filename not in saved:
            saved.append(filename)
            write_saved_atomic(saved)

        # Snapshot the file to HeartedQueue so rotation can't kill it
        HEARTED_QUEUE.mkdir(parents=True, exist_ok=True)
        dst = HEARTED_QUEUE / filename
        if not dst.exists():
            shutil.copy2(src, dst)

    log.info("hearted %s (total: %d)", filename, len(saved))
    return jsonify({"ok": True, "saved": filename, "count": len(saved)})


@app.route("/api/unheart", methods=["POST"])
def api_unheart():
    data = request.get_json(silent=True) or {}
    filename = safe_filename(data.get("file", ""))

    with state_lock:
        saved = read_saved()
        if filename in saved:
            saved.remove(filename)
            write_saved_atomic(saved)
        # Remove from queue if still pending import.
        q_path = HEARTED_QUEUE / filename
        if q_path.exists():
            q_path.unlink()

    log.info("unhearted %s (total: %d)", filename, len(saved))
    return jsonify({"ok": True, "cleared": filename, "count": len(saved)})


if __name__ == "__main__":
    log.info("=" * 60)
    log.info("starting ScreenArt viewer on %s:%d", HOST, PORT)
    log.info("images dir:    %s", IMAGES_DIR)
    log.info("hearted queue: %s", HEARTED_QUEUE)
    log.info("saved.json:    %s", SAVED_JSON)
    log.info("=" * 60)
    app.run(host=HOST, port=PORT, debug=False)

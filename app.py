from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import threading
import os
import shutil
from pathlib import Path
import string
import random
import datetime
import tempfile
import zipfile

from doc_convert_service import process_document_async
from utils import gen_unique_dirname, get_status_info

app = Flask(__name__)

EXTRACTED_ROOT = Path(__file__).parent.resolve() / "extracted"

@app.route("/upload", methods=["POST"])
def upload():
    # 1. 產生唯一目錄名稱
    dir_name = gen_unique_dirname()
    dir_path = EXTRACTED_ROOT / dir_name
    print(f"[DEBUG][upload] dir_path={dir_path.resolve()}")
    dir_path.mkdir(parents=True, exist_ok=True)

    # 2. 儲存上傳檔案
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    file_path = dir_path / filename
    file.save(str(file_path))

    # 3. 取得 desc_figure 參數
    desc_figure = False
    if "desc_figure" in request.form:
        desc_figure = request.form.get("desc_figure", "false").lower() == "true"
    elif request.is_json and "desc_figure" in request.json:
        desc_figure = bool(request.json.get("desc_figure"))

    # 4. 啟動背景處理
    threading.Thread(
        target=process_document_async,
        args=(file_path, dir_path, desc_figure),
        daemon=True
    ).start()

    # 5. 立即回傳目錄名稱
    return jsonify({"dir": dir_name})

@app.route("/status/<dir_name>", methods=["GET"])
def status(dir_name):
    dir_path = EXTRACTED_ROOT / dir_name
    print(f"[DEBUG][status] dir_path={dir_path.resolve()}")
    status, content = get_status_info(dir_path)
    return jsonify({"status": status, "content": content})

@app.route("/download", methods=["POST", "GET"])
def download():
    # 支援 POST form/json 或 GET query
    dir_name = request.values.get("dir") or (request.json.get("dir") if request.is_json else None)
    if not dir_name:
        return jsonify({"error": "請提供 dir 參數"}), 400
    dir_path = EXTRACTED_ROOT / dir_name
    print(f"[DEBUG][download] dir_path={dir_path.resolve()}")
    if not dir_path.exists() or not dir_path.is_dir():
        return jsonify({"error": f"找不到目錄: {dir_name}"}), 404

    # 動態壓縮目錄
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmpf:
        zip_path = Path(tmpf.name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in dir_path.rglob("*"):
            zipf.write(file, arcname=file.relative_to(dir_path))
    # 回傳 zip 並刪除臨時檔
    response = send_file(
        str(zip_path),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{dir_name}.zip"
    )
    # 設定回應後自動刪除
    @response.call_on_close
    def cleanup():
        try:
            zip_path.unlink()
        except Exception:
            pass
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

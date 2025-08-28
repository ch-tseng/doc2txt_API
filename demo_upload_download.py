import requests
import time
from pathlib import Path

API_URL = "http://localhost:5000"
TEST_FILE = "xlsx.pdf"  # 請將要上傳的檔案放在同目錄
POLL_INTERVAL = 2  # 秒
TIMEOUT = 300  # 最多等待 5 分鐘

def upload_file(desc_figure=False):
    with open(TEST_FILE, "rb") as f:
        files = {"file": (TEST_FILE, f)}
        data = {"desc_figure": "true" if desc_figure else "false"}
        resp = requests.post(f"{API_URL}/upload", files=files, data=data)
    resp.raise_for_status()
    dir_name = resp.json()["dir"]
    print(f"上傳成功，API 回傳目錄名稱: {dir_name}")
    return dir_name

def wait_for_finished(dir_name):
    status_url = f"{API_URL}/status/{dir_name}"
    print("等待 finished.txt ...")
    start = time.time()
    while True:
        resp = requests.get(status_url)
        resp.raise_for_status()
        status = resp.json()["status"]
        content = resp.json()["content"]
        print(f"查詢狀態: {status}")
        if status == "finished":
            print("finished.txt 內容:")
            print(content)
            return True
        if time.time() - start > TIMEOUT:
            print("等待逾時，請檢查伺服器狀態")
            return False
        time.sleep(POLL_INTERVAL)

def download_zip(dir_name):
    print("下載壓縮檔 ...")
    resp = requests.post(f"{API_URL}/download", data={"dir": dir_name})
    if resp.status_code == 200:
        zip_path = f"{dir_name}.zip"
        with open(zip_path, "wb") as f:
            f.write(resp.content)
        print(f"下載完成，檔案: {zip_path}")
    else:
        try:
            print("下載失敗:", resp.json())
        except Exception:
            print("下載失敗，非 JSON 回應，HTTP code:", resp.status_code)

def show_figure_desc_files(dir_name):
    extracted_dir = Path("extracted") / dir_name
    desc_files = sorted(extracted_dir.glob("*.md"))
    print("=== 圖片描述檔案內容 ===")
    for f in desc_files:
        if f.name == "output_document.md":
            continue
        print(f"\n--- {f.name} ---")
        print(f.read_text(encoding="utf-8")[:500])

def main():
    # 啟用圖片描述功能
    dir_name = upload_file(desc_figure=True)
    ok = wait_for_finished(dir_name)
    if ok:
        download_zip(dir_name)
        show_figure_desc_files(dir_name)

if __name__ == "__main__":
    main()

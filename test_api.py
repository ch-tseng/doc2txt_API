import requests
import time
from pathlib import Path

API_URL = "http://localhost:5000"
TEST_FILE = "test.docx"  # 請放一份測試文件於同目錄
POLL_INTERVAL = 2  # 秒

def main():
    log_lines = []
    # 1. 上傳檔案
    with open(TEST_FILE, "rb") as f:
        files = {"file": (TEST_FILE, f)}
        resp = requests.post(f"{API_URL}/upload", files=files)
    resp.raise_for_status()
    dir_name = resp.json()["dir"]
    log_lines.append(f"API 回傳目錄名稱: {dir_name}")

    # 2. 輪詢狀態
    status_url = f"{API_URL}/status/{dir_name}"
    while True:
        resp = requests.get(status_url)
        resp.raise_for_status()
        status = resp.json()["status"]
        content = resp.json()["content"]
        log_lines.append(f"查詢狀態: {status}")
        if status == "finished":
            log_lines.append(f"finished.txt 內容:\n{content}")
            break
        time.sleep(POLL_INTERVAL)

    # 3. 檢查目錄下檔案
    extracted_dir = Path("extracted") / dir_name
    file_list = [str(p.relative_to(extracted_dir)) for p in extracted_dir.rglob("*") if p.is_file()]
    log_lines.append("目錄下檔案清單:")
    log_lines.extend(file_list)

    # 4. 讀取 output_document.md 內容片段
    md_path = extracted_dir / "output_document.md"
    if md_path.exists():
        with md_path.open("r", encoding="utf-8") as f:
            md_head = f.read(500)
        log_lines.append("output_document.md 內容片段:")
        log_lines.append(md_head)
    else:
        log_lines.append("output_document.md 不存在")

    # 5. 列出 figures 目錄下圖檔
    figures_dir = extracted_dir / "figures"
    if figures_dir.exists():
        figures = [p.name for p in figures_dir.glob("*.png")]
        log_lines.append("figures 圖檔清單:")
        log_lines.extend(figures)
    else:
        log_lines.append("figures 目錄不存在")

    # 6. 輸出 log
    log_path = extracted_dir / "test_log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

if __name__ == "__main__":
    main()

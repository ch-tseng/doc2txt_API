import requests

API_URL = "http://localhost:5000"
TEST_FILE = "test.docx"  # 請將要上傳的檔案放在同目錄

def main():
    with open(TEST_FILE, "rb") as f:
        files = {"file": (TEST_FILE, f)}
        resp = requests.post(f"{API_URL}/upload", files=files)
    resp.raise_for_status()
    dir_name = resp.json()["dir"]
    print(f"回傳的目錄名稱: {dir_name}")

if __name__ == "__main__":
    main()

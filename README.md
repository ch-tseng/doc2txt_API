# Doc2Txt API 系統

## 簡介

本專案為一套支援多格式文件（PDF、DOCX、PPTX、XLSX）自動轉檔與圖片語意描述的 API 系統。  
- 支援將文件轉為 Markdown，並自動將所有圖片送交 OpenAI 進行語意描述，描述內容直接插入 output_document.md。
- 適合知識管理、AI 文件摘要、RAG 前處理等應用。

---

## 特色

- 支援 PDF、Word、PPT、Excel 等多格式上傳
- 圖片描述自動串接 OpenAI Vision（GPT-4 Vision）
- 完全非同步處理，適合大檔與高併發
- Production-ready，Gunicorn 多 worker 部署
- 產出單一 Markdown 檔，所有圖片描述自動插入
- 完整 API、Python/Bash demo、開發與使用文件

---

## 安裝與啟動

1. **Python 3.10+**
2. 安裝依賴
   ```bash
   pip install -r requirements.txt
   ```
3. 設定 .env
   ```
   OPENAI_API_KEY=你的OpenAI金鑰
   ```
4. 設定 config.ini（模型與 context 字數）
5. Production 啟動
   ```bash
   bash run_gunicorn.sh
   ```
   或開發測試
   ```bash
   python app.py
   ```

---

## API 端點

- `POST /upload`  
  參數：file, desc_figure（true/false）  
  回傳：{"dir": 目錄名稱}

- `GET /status/{dir}`  
  查詢處理狀態 finished/processing

- `POST /download`  
  參數：dir  
  回傳：zip 壓縮檔

---

## 使用範例

### Python Demo
```python
import requests
with open("test.docx", "rb") as f:
    files = {"file": ("test.docx", f)}
    data = {"desc_figure": "true"}
    resp = requests.post("http://localhost:5000/upload", files=files, data=data)
dir_name = resp.json()["dir"]
# ...查詢狀態與下載，詳見 demo_upload_download.py
```

### Bash Demo
```bash
curl -F "file=@test.docx" -F "desc_figure=true" http://localhost:5000/upload
curl http://localhost:5000/status/20250828_175404_AWHT
curl -X POST -F "dir=20250828_175404_AWHT" http://localhost:5000/download -o 20250828_175404_AWHT.zip
```

---

## 文件與說明

- [開發文件](docs/開發文件.md)
- [使用說明](docs/使用說明.md)

---

## 目錄結構

- app.py, doc_convert_service.py, utils.py, requirements.txt, config.ini, .env
- run_gunicorn.sh
- demo_upload_download.py
- docs/（開發與使用文件）
- extracted/（所有轉檔與結果目錄）

---

## 貢獻與維護

- 歡迎 issue/PR，請詳閱 docs/開發文件.md
- 若需擴充格式、模型、描述 prompt，皆可自訂

---

## License

MIT License

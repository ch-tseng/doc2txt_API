import traceback
import shutil
from pathlib import Path
import re

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

from utils import replace_md_image_links, get_config
import openai
import base64
import os

def get_openai_api_key():
    # 讀取環境變數，若不存在則嘗試用 dotenv 載入 .env
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.environ.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found in environment variables or .env")
    return key

def call_openai_figure_desc(image_path, context, model):
    """
    真正呼叫 OpenAI API 進行圖片描述 (openai>=1.0.0)
    """
    openai.api_key = get_openai_api_key()
    # 讀取圖片 bytes 並 base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    prompt = f"請根據下方圖片與上下文，產生一段精確的圖片描述（繁體中文）：\n上下文：{context}"
    # openai>=1.0.0 新版 API
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ],
        max_tokens=256,
        temperature=0.2,
    )
    desc = response.choices[0].message.content.strip()
    return desc

def process_document_async(file_path: Path, dir_path: Path, desc_figure: bool = False):
    """
    處理文件轉檔、markdown 置換、(可選)圖檔描述、finished.txt 產生
    """
    try:
        # 1. 轉檔
        doc_converter = DocumentConverter()
        conv_res = doc_converter.convert(str(file_path))

        # 2. 產生 markdown，並將圖片路徑置換為相對路徑
        md_path = dir_path / "output_document.md"
        conv_res.document.save_as_markdown(md_path, image_mode="referenced")
        # 讀取 markdown 並置換
        with md_path.open("r", encoding="utf-8") as f:
            md_content = f.read()
        md_content = replace_md_image_links(md_content)
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md_content)

        # 3. 若 desc_figure，將描述直接插入 output_document.md
        if desc_figure:
            config = get_config()
            model = config["active_model"]
            context_len = config["context_figure"]
            artifacts_dir = next(dir_path.glob("output_document_artifacts"), None)
            if artifacts_dir and artifacts_dir.is_dir():
                images = sorted(artifacts_dir.glob("*.png"))
                # 先建立圖檔 path 到描述的 mapping
                desc_map = {}
                for img_path in images:
                    img_rel = f"output_document_artifacts/{img_path.name}"
                    # 找出所有出現該圖的 markdown 位置
                    for m in re.finditer(rf'!\[.*?\]\({re.escape(img_rel)}\)', md_content):
                        start, end = m.span()
                        ctx_start = max(0, start - context_len)
                        ctx_end = min(len(md_content), end + context_len)
                        context = md_content[ctx_start:ctx_end]
                        break
                    else:
                        context = ""
                    try:
                        desc = call_openai_figure_desc(str(img_path), context, model)
                    except Exception as e:
                        desc = f"【OpenAI API 失敗】{e}"
                    desc_map[img_rel] = desc
                # 置換 markdown 內所有圖片為「圖片markdown+描述」
                def desc_repl(match):
                    alt = match.group(1)
                    img_rel = match.group(2)
                    desc = desc_map.get(img_rel, "")
                    return f"![{alt}]({img_rel})\n描述: {desc}"
                md_content = re.sub(
                    r'!\[([^\]]*)\]\((output_document_artifacts/[^\)]+)\)',
                    desc_repl,
                    md_content
                )
                with md_path.open("w", encoding="utf-8") as f:
                    f.write(md_content)

        # 4. 產生 finished.txt
        with (dir_path / "finished.txt").open("w", encoding="utf-8") as f:
            f.write("done\n")
            f.write("summary: success\n")

    except Exception as e:
        # 產生 finished.txt 並寫入錯誤訊息
        with (dir_path / "finished.txt").open("w", encoding="utf-8") as f:
            f.write("error\n")
            f.write(f"reason: {str(e)}\n")
            f.write("trace:\n")
            f.write(traceback.format_exc())

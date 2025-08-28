import random
import string
import datetime
from pathlib import Path
import re
import configparser

def get_config(config_path="config.ini"):
    """
    讀取 config.ini，回傳 dict
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    result = {}
    # 取得 active_model
    result["active_model"] = config.get("OPENAI", "active_model", fallback="gpt-4.1")
    # 取得 context_figure
    result["context_figure"] = config.getint("FIGURE_DESC", "context_figure", fallback=500)
    return result

def gen_unique_dirname():
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"{now}_{rand}"

def get_status_info(dir_path: Path):
    finished_path = dir_path / "finished.txt"
    if finished_path.exists():
        with finished_path.open("r", encoding="utf-8") as f:
            content = f.read()
        return "finished", content
    else:
        return "processing", ""

def replace_md_image_links(md_content: str) -> str:
    """
    將 markdown 內 ![](/絕對路徑/output_document_artifacts/xxx.png)
    置換為 ![](output_document_artifacts/xxx.png)
    """
    # 只處理 output_document_artifacts 目錄下的圖片
    pattern = r'!\[([^\]]*)\]\([^\)]*?/output_document_artifacts/([^)]+\.png)\)'
    def repl(match):
        alt = match.group(1)
        filename = match.group(2)
        return f"![{alt}](output_document_artifacts/{filename})"
    new_md = re.sub(pattern, repl, md_content)
    return new_md

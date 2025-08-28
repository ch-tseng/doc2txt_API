#!/bin/bash
# 啟動 Gunicorn 適合 production 的 Flask 服務
# 建議於專案根目錄執行: bash run_gunicorn.sh
unset LD_LIBRARY_PATH
export PYTHONUNBUFFERED=1
export FLASK_ENV=production

# Gunicorn 參數可依主機核心數調整 workers
# --bind 0.0.0.0:5000 監聽所有網卡
# --timeout 120 適合長任務
# --access-logfile - 直接輸出 access log 到 stdout
gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 120 --access-logfile -

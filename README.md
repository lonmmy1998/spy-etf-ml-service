# SPY ETF ML Service (1d / 5d / 20d) — XGBoost + FastAPI

這個專案把「訓練模型」和「提供 API 服務」做成一套可交付流程：

- 用 SPY 的歷史特徵（技術指標 + 宏觀因子）訓練 XGBoost
- 產出 3 個 horizon 的模型（1d / 5d / 20d）
- 用 FastAPI 提供推論服務（Swagger UI /docs 可直接測）
- 對輸入做基本防呆：空 rows、缺欄位、日期格式錯、非數值特徵等會回 400 並給明確訊息

---

## 專案結構

spy-etf-ml-service/
├─ app.py # FastAPI 服務（載入三個模型，提供 /predict）
├─ train.py # 訓練並產生 artifacts
├─ predict.py #（可選）本地推論小工具
├─ make_request.py # 從 Excel 產生 examples/request.json
├─ requirements.txt # 套件清單
├─ README.md
├─ examples/
│ └─ request.json # POST /predict 測試用 payload
├─ data/ # 放 data/etf.xlsx
└─ artifacts/ # train.py 產出的 *.joblib

---

## 環境安裝

建議用 venv：

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

資料放置

把資料放到：data/etf.xlsx
並確保 Excel 內有一個 sheet 名為：SPY

訓練模型（產生 artifacts）
python train.py
成功後會產生（在 artifacts/）：
artifacts/model_spy_1d.joblib
artifacts/model_spy_5d.joblib
artifacts/model_spy_20d.joblib

每個 artifact 內含：
model：XGBoost classifier
feature_cols：訓練時特徵欄位順序（線上推論用來對齊欄位）

產生 API 測試用 JSON（可選）
python make_request.py
會產生：examples/request.json
你可以在 make_request.py 裡調整 tail(1) / tail(3) 來控制 rows 筆數。

啟動 API
python -m uvicorn app:app --reload
Swagger UI：http://127.0.0.1:8000/docs
API Endpoints
GET /health

健康檢查：
{"status":"ok"}

GET /predict_last
讀取 data/etf.xlsx（SPY sheet），取最後一筆資料推論，回傳 1/5/20：
{
  "prob_1d": 0.43,
  "label_1d": 0,
  "prob_5d": 0.23,
  "label_5d": 0,
  "prob_20d": 0.32,
  "label_20d": 0
}

POST /predict
Body 格式：
{
  "rows": [
    {
      "日期": "2025-01-28",
      "ETF代碼": "SPY",
      "...feature columns...": 0.0
    }
  ]
}
說明：
rows 可多筆；服務端會依 日期 排序並 ffill()，最後取「最後一筆」做推論
特徵欄位會依 feature_cols 對齊欄位順序
常見 400 錯誤（防呆）
rows 空：rows 不能是空的
缺少 日期：缺少必要欄位：日期
缺少特徵欄：缺少特徵欄位：[ ... ]
日期格式錯：日期格式錯誤，請用 YYYY-MM-DD
特徵非數值：特徵欄位需為數值...

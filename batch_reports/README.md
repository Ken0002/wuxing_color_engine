# Batch Reports

這個資料夾用來批次產生「指定生日 + 指定日期區間」的五行能量 PDF 報告。

## 安裝

如果你要用 `pip` 安裝需要的套件：

```bash
.venv/bin/python -m pip install -r batch_reports/requirements.txt
```

報表使用 `reportlab==4.0.9`，已在專案的 Python 3.8 環境驗證。較新的版本可能在建立 PDF 時發生 `usedforsecurity` 參數錯誤。安裝與執行請使用同一個虛擬環境；此電腦的系統 `python3` 是 Python 3.6，不符合專案需求。

## 執行

直接跑：

```bash
.venv/bin/python batch_reports/generate_date_range_report.py --config batch_reports/config/config.example.json
```

成功後會：

- 在終端列出每天的摘要
- 使用 `config` 內的 `output_pdf` 檔案名稱，輸出 PDF 到 `batch_reports/output/`

## 怎麼改生日與日期區間

打開 [config.example.json](config/config.example.json)，修改下面欄位：

```json
{
  "name": "Ken",
  "birth_datetime": "1996-04-27 17:30",
  "start_date": "2026-04-01",
  "end_date": "2026-04-07",
  "output_pdf": "wuxing_date_range_report.pdf",
  "report_title": "每日五行能量建議書",
  "report_subtitle": "個人化日期範圍報表"
}
```

欄位格式：

- `name`: 報告顯示名稱
- `birth_datetime`: 出生時間，格式 `YYYY-MM-DD HH:MM`
- `start_date`: 開始日期，格式 `YYYY-MM-DD`
- `end_date`: 結束日期，格式 `YYYY-MM-DD`
- `output_pdf`: 只填 PDF 檔案名稱（例如 `阿璇.pdf`），必須以 `.pdf` 結尾，不可包含路徑。輸出固定放在 `batch_reports/output/`，與 config 位置或執行目錄無關。省略時使用 `wuxing_date_range_report.pdf`。
- `report_title`: PDF 標題
- `report_subtitle`: PDF 副標題

## 換別的人或換別的區間

最簡單的方式是複製一份新的 config，例如：

```bash
cp batch_reports/config/config.example.json batch_reports/config/config.chen.json
```

然後改成你要的內容，再執行：

```bash
.venv/bin/python batch_reports/generate_date_range_report.py --config batch_reports/config/config.chen.json
```

## 可調整的檔案

- [templates/explanation_templates.json](templates/explanation_templates.json): 穿搭策略與今日重點文案模板
- [report_layout.py](report_layout.py): PDF 版面
- [report_content.py](report_content.py): 每日內容組裝邏輯

## 目錄

- `config/`：範例與個人報告設定；不同日期區間分別保留
- `templates/`：報告文案模板
- `output/`：產出的 PDF（不納入 Git）
- `generate_date_range_report.py`：執行入口
- `report_content.py`、`report_models.py`：內容組裝與資料模型
- `report_layout.py`、`report_styles.py`：PDF 版面與樣式

阿璇的 135 天報告：

```bash
.venv/bin/python batch_reports/generate_date_range_report.py --config batch_reports/config/config.阿璇.2026-12-01.json
```

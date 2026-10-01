# wuxing_color_engine

這個專案提供八字與日期五行資訊的命令列工具，目前相容 Python 3.8 到 Python 3.12。

## 專案結構

- `main.py`：主要入口，整合八字與日期五行能量計算
- `bazi_calculator.py`：可獨立執行的八字計算模組
- `date_energy_calculator.py`：可獨立執行的日期五行能量計算模組
- `batch_reports/`：批次 PDF 報告、設定、文案與輸出，詳見 [報告說明](batch_reports/README.md)
- `core_scoring.py`：核心 scoring engine，只依靠出生時間與目標日期推導命主喜忌、五行分數與排名

## 環境建立

核心計算使用 Python 標準函式庫；Web 介面需要 Flask，PDF 報告需要 ReportLab。請使用 `venv` 管理環境。

Python 3.12：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Python 3.8：

```bash
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

如果你想維持一致的使用流程，也可以加跑：

```bash
python -m pip install -r requirements.txt
```

## 使用方式

主入口：

```bash
python main.py --birth-datetime "1996-04-27 17:30" --target-date 2026-04-02
```

Web 介面：

```bash
python -m pip install -r requirements.txt
python web.py
```

開啟 `http://0.0.0.0:7788` 或你的機器 IP `:7788`

八字計算：

```bash
python bazi_calculator.py --birth-datetime "1996-04-27 17:30"
```

日期五行計算：

```bash
python date_energy_calculator.py --target-date 2026-04-02
```

查看 `main.py` 參數說明：

```bash
python main.py -h
```

查看單一模組參數說明：

```bash
python bazi_calculator.py -h
python date_energy_calculator.py -h
```

批次生成日期區間報表：

```bash
.venv/bin/python batch_reports/generate_date_range_report.py --config batch_reports/config/config.example.json
```

`config` 範例：

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

- `name`：使用者姓名，會顯示在首頁
- `birth_datetime`：出生時間，格式為 `YYYY-MM-DD HH:MM`
- `start_date` / `end_date`：生成區間，格式為 `YYYY-MM-DD`，包含起訖日
- `output_pdf`：只填以 `.pdf` 結尾的檔案名稱；程式固定輸出到 `batch_reports/output/`
- `report_title`：PDF 首頁主標題
- `report_subtitle`：PDF 首頁副標題

輸出的 PDF 結構為：

- 第 1 頁：使用者總覽頁，包含姓名、出生日期、八字、命主喜忌、日期區間、顏色對應表與閱讀說明
- 第 2 頁起：每日建議頁，包含日期、星期、干支、五行摘要、今日一句話結論、五行排行表、主色/輔助色/避免色/配件色與簡短說明

## 輸出範例

`python date_energy_calculator.py --target-date 2026-04-02`

```text
2026-04-02
丙午年辛卯月丙午日
火年木月(月生年以火算)火日
```

`python main.py --birth-datetime "1996-04-27 17:30" --target-date 2026-04-02`

```text
=== 個人八字 ===
1996-04-27 17:30
丙子年壬辰月甲午日癸酉時

=== 特定日期五行能量 ===
2026-04-02
丙午年辛卯月丙午日
火年木月(月生年以火算)火日

=== 核心算法 ===
命主判定: 身強 (support=7.67, balance=6.33)
命主喜忌: 喜:火、土、金 / 忌:水
命主來源: birth_only_inference
日期 signature: 月=木 / 日=火 / 轉化=火
計分模式: 純輸入推導
五行分數: 木 74 / 火 24 / 土 40 / 金 95 / 水 72
排名: 金 > 木 > 水 > 土 > 火
```

## 核心算法說明

- runtime 不再讀 `dataset.csv`；推論時只需要 `birth_datetime` 與 `target_date`。
- 命主端先由八字推日主強弱，再用扶抑法推喜忌：
  - 身強偏向喜「洩、耗、制」，也就是食傷、財、官殺。
  - 身弱偏向喜「生、扶」，也就是印星、比劫。
- 日期端先把目標日期轉成 `month_element + day_element + 轉化元素`，再用固定係數模型換成五行分數基底。
- `compare_scoring_models.py` 是離線算法比較工具，需要自行提供 `data/dataset.csv`；目前專案未附該資料。
- `web.py` 會沿用目前 `main.py` 的 `v1` 核心算法；`v2` 仍保留作為獨立實驗版，不會自動接到網頁或 CLI。

## 版本與相容性

- 專案版本限制寫在 `pyproject.toml`
- 支援範圍為 `>=3.8,<3.13`
- `requirements.txt`：Web 介面的 Flask 依賴
- `batch_reports/requirements.txt`：PDF 報告依賴

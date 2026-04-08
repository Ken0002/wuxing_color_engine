# wuxing_color_engine

這個專案提供八字與日期五行資訊的命令列工具，目前相容 Python 3.8 到 Python 3.12。

## 專案結構

- `main.py`：主要入口，整合八字與日期五行能量計算
- `bazi_calculator.py`：可獨立執行的八字計算模組
- `date_energy_calculator.py`：可獨立執行的日期五行能量計算模組
- `core_scoring.py`：核心 scoring engine，只依靠出生時間與目標日期推導命主喜忌、五行分數與排名

## 環境建立

這個專案目前只使用 Python 標準函式庫，沒有第三方套件依賴。  
即使如此，仍建議使用 `venv` 管理環境。

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
- `dataset.csv` 目前只保留作為離線校準與驗證資料，不參與 runtime inference。
- `web.py` 會沿用目前 `main.py` 的 `v1` 核心算法；`v2` 仍保留作為獨立實驗版，不會自動接到網頁或 CLI。

## 版本與相容性

- 專案版本限制寫在 `pyproject.toml`
- 支援範圍為 `>=3.8,<3.13`
- 目前 `requirements.txt` 只保留作為統一環境流程用

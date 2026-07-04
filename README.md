# 量化交易工作坊 TASK1 — 数据引擎与可视化看板

> 量化交易初体验：从零搭建数据引擎

## 在线看板

👉 **[点击查看交互式量化看板](https://你的用户名.github.io/quant-task1/)** 

## 项目概述

本项目实现了 A 股量化交易数据引擎，包括：
- 股票日线数据自动获取（Baostock/Tushare）
- 交互式 K 线图及技术分析图表（Plotly.js）
- 数据 CSV 导出
- GitHub Pages 一键部署

## 文件结构

```
TASK1/
├── index.html                  # 交互式量化分析看板（主页面）
├── stock_data_engine.py        # 数据获取引擎
├── generate_report.py          # Word 报告生成脚本
├── generate_html_report.py     # HTML 看板生成脚本
├── 600519_daily.csv            # 贵州茅台日线数据（242个交易日）
├── 600519_close_price.png      # 收盘价走势图
└── 姓名+TASK1.docx             # 完整任务报告
```

## 数据概况

| 指标 | 数值 |
|------|------|
| 股票 | 贵州茅台 (600519) |
| 数据区间 | 2025-07-04 ~ 2026-07-03 |
| 交易日 | 242 天 |
| 价格区间 | ¥1,168 ~ ¥1,519 |
| 区间涨跌 | -12.56% |

## 使用方法

```bash
# 1. 获取数据
python stock_data_engine.py

# 2. 生成 HTML 看板
python generate_html_report.py

# 3. 生成 Word 报告
python generate_report.py

# 4. 本地预览
# 直接用浏览器打开 index.html
```

## 技术栈

- **数据获取**: Python (Baostock / Tushare)
- **可视化**: Plotly.js (交互式), Matplotlib (静态图)
- **报告**: python-docx
- **部署**: GitHub Pages

## 作者

姓名 - 量化交易工作坊学员

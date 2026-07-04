# -*- coding: utf-8 -*-
"""
量化交易工作坊 TASK1 - HTML 看板生成脚本
生成交互式 HTML 量化分析报告，可直接部署至 GitHub Pages

包含：
  - 交互式 K线图（Candlestick Chart）含缩放/平移
  - 每日收盘价走势图（含移动均线）
  - 成交量柱状图
  - 数据摘要统计卡片
  - 交易数据表格预览
"""

import pandas as pd
import json
import os
from datetime import datetime

# ============================================================
# 配置
# ============================================================
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(OUTPUT_DIR, "600519_daily.csv")
HTML_FILE = os.path.join(OUTPUT_DIR, "index.html")
STOCK_CODE = "600519"
STOCK_NAME = "贵州茅台"
AUTHOR_NAME = "姓名"  # <-- 请替换


def load_data(csv_path):
    """加载 CSV 数据"""
    col_map = {
        "交易日期": "date",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "前收盘价": "pre_close",
        "涨跌额": "change",
        "涨跌幅(%)": "pct_chg",
        "成交量(手)": "volume",
        "成交额(元)": "amount",
    }
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df = df.rename(columns=col_map)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").reset_index(drop=True)

    # 计算移动均线
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()

    return df


def prepare_candlestick_data(df):
    """准备K线图数据（OHLC 格式）"""
    records = []
    for _, row in df.iterrows():
        records.append({
            "x": row["date"].strftime("%Y-%m-%d"),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
        })
    return json.dumps(records, ensure_ascii=False)


def prepare_line_data(df, col_name):
    """准备折线图数据"""
    series = df[col_name].dropna()
    return json.dumps([
        {"x": row["date"].strftime("%Y-%m-%d"), "y": round(float(row[col_name]), 2)}
        for _, row in df.loc[series.index].iterrows()
    ], ensure_ascii=False)


def get_summary_stats(df):
    """计算摘要统计"""
    first_close = float(df.iloc[0]["close"])
    last_close = float(df.iloc[-1]["close"])
    change_pct = (last_close - first_close) / first_close * 100
    return {
        "start_date": df.iloc[0]["date"].strftime("%Y-%m-%d"),
        "end_date": df.iloc[-1]["date"].strftime("%Y-%m-%d"),
        "trading_days": len(df),
        "first_close": f"{first_close:.2f}",
        "last_close": f"{last_close:.2f}",
        "change_pct": f"{change_pct:+.2f}",
        "high_max": f"{df['high'].max():.2f}",
        "low_min": f"{df['low'].min():.2f}",
        "avg_volume": f"{df['volume'].mean():.0f}",
        "avg_amount": f"{df['amount'].mean():.0f}",
        "volatility": f"{df['pct_chg'].std():.2f}",
    }


def generate_html(df, stats):
    """生成完整 HTML 页面"""
    # 准备数据
    candlestick_json = prepare_candlestick_data(df)
    close_json = prepare_line_data(df, "close")
    ma5_json = prepare_line_data(df, "ma5")
    ma10_json = prepare_line_data(df, "ma10")
    ma20_json = prepare_line_data(df, "ma20")
    ma60_json = prepare_line_data(df, "ma60")

    # 成交量数据
    volume_data = json.dumps([
        {"x": row["date"].strftime("%Y-%m-%d"),
         "y": int(row["volume"]),
         "color": "#ef5350" if float(row["close"]) >= float(row["open"]) else "#26a69a"}
        for _, row in df.iterrows()
    ], ensure_ascii=False)

    # 数据表格预览（最近20行）
    table_data = []
    for _, row in df.tail(20).iloc[::-1].iterrows():
        table_data.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "open": f"{row['open']:.2f}",
            "high": f"{row['high']:.2f}",
            "low": f"{row['low']:.2f}",
            "close": f"{row['close']:.2f}",
            "change": f"{row['pct_chg']:+.2f}%",
            "volume": f"{int(row['volume']):,}",
        })
    table_json = json.dumps(table_data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{STOCK_NAME}({STOCK_CODE}) 量化分析看板</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #0f1923;
    color: #e0e0e0;
    min-height: 100vh;
}}
.header {{
    background: linear-gradient(135deg, #1a2a3a 0%, #0d1b2a 100%);
    border-bottom: 2px solid #c9a84c;
    padding: 30px 40px;
    text-align: center;
}}
.header h1 {{
    font-size: 1.8em;
    color: #c9a84c;
    margin-bottom: 8px;
}}
.header .subtitle {{
    color: #8899aa;
    font-size: 0.95em;
}}
.stats-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    padding: 24px 40px;
    background: #152230;
    border-bottom: 1px solid #1e3040;
}}
.stat-card {{
    background: #1a2f3f;
    border: 1px solid #2a4050;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}}
.stat-card .label {{ font-size: 0.8em; color: #7a8a9a; margin-bottom: 6px; }}
.stat-card .value {{ font-size: 1.4em; font-weight: 700; }}
.stat-card .value.up {{ color: #ef5350; }}
.stat-card .value.down {{ color: #26a69a; }}
.stat-card .value.neutral {{ color: #e0e0e0; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px 40px; }}
.chart-box {{
    background: #152230;
    border: 1px solid #1e3040;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 24px;
}}
.chart-box h2 {{
    font-size: 1.15em;
    color: #c9a84c;
    margin-bottom: 8px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e3040;
}}
.two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
}}
@media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
.table-wrapper {{ overflow-x: auto; }}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
}}
thead th {{
    background: #1a2f3f;
    color: #c9a84c;
    padding: 10px 12px;
    text-align: right;
    border-bottom: 2px solid #2a4050;
    position: sticky; top: 0;
}}
thead th:first-child {{ text-align: center; }}
tbody td {{
    padding: 8px 12px;
    text-align: right;
    border-bottom: 1px solid #1a2a3a;
    color: #c0c8d0;
}}
tbody td:first-child {{ text-align: center; color: #7a8a9a; }}
tbody tr:hover {{ background: #1a2f3f; }}
td.up {{ color: #ef5350 !important; }}
td.down {{ color: #26a69a !important; }}
.footer {{
    text-align: center;
    padding: 30px;
    color: #556677;
    font-size: 0.82em;
    border-top: 1px solid #1a2a3a;
    margin-top: 20px;
}}
.footer a {{ color: #c9a84c; text-decoration: none; }}
.section-title {{
    color: #c9a84c;
    font-size: 1.3em;
    margin: 32px 0 16px 0;
    padding-left: 12px;
    border-left: 4px solid #c9a84c;
}}
.analysis-text {{
    background: #152230;
    border: 1px solid #1e3040;
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 24px;
    line-height: 1.9;
    font-size: 0.93em;
    color: #bcc8d4;
}}
.analysis-text h3 {{ color: #c9a84c; margin: 16px 0 8px 0; font-size: 1.05em; }}
.analysis-text h3:first-child {{ margin-top: 0; }}
.analysis-text p {{ margin-bottom: 12px; text-indent: 2em; }}
.analysis-text ul {{ margin: 8px 0 8px 2em; }}
.analysis-text li {{ margin-bottom: 6px; }}
</style>
</head>
<body>

<div class="header">
    <h1>{STOCK_NAME} ({STOCK_CODE}) 量化分析看板</h1>
    <div class="subtitle">
        数据范围: {stats['start_date']} ~ {stats['end_date']} |
        交易日: {stats['trading_days']} 天 |
        数据来源: Baostock / Tushare |
        作者: {AUTHOR_NAME}
    </div>
</div>

<div class="stats-row">
    <div class="stat-card">
        <div class="label">区间起始价</div>
        <div class="value neutral">¥{stats['first_close']}</div>
    </div>
    <div class="stat-card">
        <div class="label">区间期末价</div>
        <div class="value neutral">¥{stats['last_close']}</div>
    </div>
    <div class="stat-card">
        <div class="label">区间涨跌幅</div>
        <div class="value {'up' if float(stats['change_pct']) > 0 else 'down'}">{stats['change_pct']}%</div>
    </div>
    <div class="stat-card">
        <div class="label">最高价</div>
        <div class="value up">¥{stats['high_max']}</div>
    </div>
    <div class="stat-card">
        <div class="label">最低价</div>
        <div class="value down">¥{stats['low_min']}</div>
    </div>
    <div class="stat-card">
        <div class="label">日均成交量</div>
        <div class="value neutral">{int(float(stats['avg_volume'])):,}手</div>
    </div>
    <div class="stat-card">
        <div class="label">波动率(std)</div>
        <div class="value neutral">{stats['volatility']}%</div>
    </div>
</div>

<div class="container">

<div class="chart-box">
    <h2>图1: {STOCK_NAME}({STOCK_CODE}) K线图 (Candlestick Chart)</h2>
    <div id="chart-kline" style="height:520px;"></div>
</div>

<div class="two-col">
<div class="chart-box">
    <h2>图2: 每日收盘价 + 移动均线</h2>
    <div id="chart-close" style="height:400px;"></div>
</div>
<div class="chart-box">
    <h2>图3: 每日成交量分布</h2>
    <div id="chart-volume" style="height:400px;"></div>
</div>
</div>

<div class="section-title">量化交易分析报告</div>
<div class="analysis-text">
    <h3>一、量化交易相较于传统手工操作交易的优势</h3>
    <p>量化交易（Quantitative Trading）是指利用数学模型、统计方法和计算机程序，对金融市场数据进行系统化分析，并据此做出交易决策的一种交易方式。相较于传统的手工操作交易方法，量化交易具有以下显著优势：</p>
    <ul>
        <li><b>系统性与纪律性</b>：量化交易基于预先设定的规则进行决策，避免了人类情绪（如恐惧、贪婪）对交易判断的干扰。传统手工交易中，交易者常常因市场短期波动而做出非理性决策。</li>
        <li><b>高效性与实时性</b>：计算机程序可在毫秒级别处理海量市场数据，同时监控数百只甚至数千只股票。传统交易受限于人类信息处理速度。</li>
        <li><b>可回测性与可验证性</b>：量化策略可利用历史数据进行回测（Backtesting），在投入真实资金前评估策略的历史表现和风险收益特征。</li>
        <li><b>风险管理的精细化</b>：可对投资组合进行精确的风险度量（VaR、最大回撤、夏普比率等），并通过程序化方式设置止损和仓位管理。</li>
        <li><b>分散化与规模效应</b>：量化系统可同时管理多个策略、品种和市场，实现真正意义上的分散化投资。</li>
        <li><b>可复制性与可扩展性</b>：成熟的量化策略可在不同市场、不同时间框架下复制和扩展。</li>
    </ul>

    <h3>二、基本概念解释</h3>
    <p><b>K线（Candlestick）</b>：K线又称蜡烛图，起源于18世纪日本的米市交易。每根K线包含四个核心价格信息：开盘价、收盘价、最高价和最低价（OHLC）。K线由实体和影线组成——开盘价与收盘价之间的矩形为实体，实体上下方的细线为上/下影线。收盘价高于开盘价为阳线（通常红色），反之为阴线（通常绿色）。K线是技术分析最重要的基础数据之一。</p>
    <p><b>基本面（Fundamentals）</b>：基本面分析通过评估宏观经济、行业和公司财务等影响内在价值的因素，来判断资产是否被高估或低估。在量化交易中，基本面分析体现为因子投资——将各项指标量化为可计算的因子，构建多因子选股模型。</p>
    <p><b>技术面（Technicals）</b>：技术分析通过研究历史价格和成交量数据来预测未来走势，建立在三大假设之上：市场行为包容消化一切信息、价格以趋势方式演变、历史会重演。技术分析包括趋势分析、形态分析、技术指标分析和成交量分析四大类方法。</p>
    <p>基本面与技术面并非相互排斥而是相辅相成。实际操作中常采用「基本面选股 + 技术面择时」的复合策略框架。</p>

    <h3>三、{STOCK_NAME}({STOCK_CODE}) 走势分析</h3>
    <p>从上方K线图和收盘价走势图中可以看出，{STOCK_NAME}在过去一年（{stats['start_date']} 至 {stats['end_date']}）经历了明显的价格波动。区间起始价为 ¥{stats['first_close']}，期末价为 ¥{stats['last_close']}，区间涨跌幅为 {stats['change_pct']}%。</p>
    <p>移动平均线（MA5/MA10/MA20/MA60）的相对位置关系反映了不同时间维度下的趋势变化。当短期均线上穿长期均线时形成「金叉」看涨信号，反之形成「死叉」看跌信号。成交量在关键价位附近的放大或萎缩，也提供了市场情绪的辅助判断依据。</p>
    <p style="color:#8899aa; margin-top:16px;"><b>数据说明：</b>本报告使用前复权数据，已对股息、送股等因素进行调整，使历史价格具有可比性。复权处理是量化数据清洗的重要步骤——未复权的数据可能因除权除息导致价格跳空，进而使策略回测结果失真。实盘交易中还应注意回测过拟合、未来函数、滑点成本等问题，回测优异的表现不一定能完全在实盘中复现。</p>
</div>

<div class="chart-box">
    <h2>交易数据一览（最近20个交易日）</h2>
    <div class="table-wrapper">
        <table id="data-table">
            <thead><tr>
                <th>日期</th><th>开盘价</th><th>最高价</th><th>最低价</th>
                <th>收盘价</th><th>涨跌幅</th><th>成交量(手)</th>
            </tr></thead>
            <tbody></tbody>
        </table>
    </div>
</div>

</div>

<div class="footer">
    <p>量化交易工作坊 TASK1 | 数据引擎: Python (Baostock/Tushare) | 图表: Plotly.js</p>
    <p>部署于 <a href="https://pages.github.com" target="_blank">GitHub Pages</a> | &copy; 2026 {AUTHOR_NAME}</p>
</div>

<script>
// ===== 图1: K线图 (Candlestick) =====
Plotly.newPlot('chart-kline', [{{
    type: 'candlestick',
    x: {candlestick_json}.map(d => d.x),
    open: {candlestick_json}.map(d => d.open),
    high: {candlestick_json}.map(d => d.high),
    low: {candlestick_json}.map(d => d.low),
    close: {candlestick_json}.map(d => d.close),
    increasing: {{ line: {{ color: '#ef5350', width: 1 }}, fillcolor: '#ef5350' }},
    decreasing: {{ line: {{ color: '#26a69a', width: 1 }}, fillcolor: '#26a69a' }},
    name: 'K线'
}}], {{
    plot_bgcolor: '#152230',
    paper_bgcolor: '#152230',
    font: {{ color: '#8899aa', size: 12 }},
    xaxis: {{
        type: 'date',
        gridcolor: '#1e3040',
        linecolor: '#2a4050',
        rangeslider: {{ visible: false }},
        rangeselector: {{
            buttons: [
                {{ count: 1, label: '1月', step: 'month', stepmode: 'backward' }},
                {{ count: 3, label: '3月', step: 'month', stepmode: 'backward' }},
                {{ count: 6, label: '6月', step: 'month', stepmode: 'backward' }},
                {{ step: 'all', label: '全部' }}
            ],
            bgcolor: '#1a2f3f',
            activecolor: '#c9a84c',
            font: {{ color: '#c0c8d0' }}
        }}
    }},
    yaxis: {{
        title: '价格 (元)',
        gridcolor: '#1e3040',
        linecolor: '#2a4050',
        side: 'right'
    }},
    margin: {{ l: 60, r: 20, t: 10, b: 60 }},
    showlegend: false,
    config: {{ displayModeBar: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] }}
}});

// ===== 图2: 收盘价 + 均线 =====
let traces = [
    {{ x: {close_json}.map(d => d.x), y: {close_json}.map(d => d.y),
       type: 'scatter', mode: 'lines', name: '收盘价',
       line: {{ color: '#e0e0e0', width: 1.5 }} }},
    {{ x: {ma5_json}.map(d => d.x), y: {ma5_json}.map(d => d.y),
       type: 'scatter', mode: 'lines', name: 'MA5',
       line: {{ color: '#42a5f5', width: 1, dash: 'dot' }} }},
    {{ x: {ma10_json}.map(d => d.x), y: {ma10_json}.map(d => d.y),
       type: 'scatter', mode: 'lines', name: 'MA10',
       line: {{ color: '#ff9800', width: 1, dash: 'dot' }} }},
    {{ x: {ma20_json}.map(d => d.x), y: {ma20_json}.map(d => d.y),
       type: 'scatter', mode: 'lines', name: 'MA20',
       line: {{ color: '#ab47bc', width: 1, dash: 'dash' }} }},
];
if ({ma60_json}.length > 0) {{
    traces.push(
        {{ x: {ma60_json}.map(d => d.x), y: {ma60_json}.map(d => d.y),
          type: 'scatter', mode: 'lines', name: 'MA60',
          line: {{ color: '#66bb6a', width: 1.2, dash: 'dash' }} }}
    );
}}
Plotly.newPlot('chart-close', traces, {{
    plot_bgcolor: '#152230', paper_bgcolor: '#152230',
    font: {{ color: '#8899aa', size: 11 }},
    xaxis: {{ gridcolor: '#1e3040', linecolor: '#2a4050' }},
    yaxis: {{ title: '价格 (元)', gridcolor: '#1e3040', linecolor: '#2a4050', side: 'right' }},
    margin: {{ l: 50, r: 10, t: 10, b: 40 }},
    legend: {{ orientation: 'h', y: 1.12, font: {{ size: 10 }} }},
    config: {{ displayModeBar: false }}
}});

// ===== 图3: 成交量 =====
let volColors = {volume_data}.map(d => d.color);
Plotly.newPlot('chart-volume', [{{
    type: 'bar',
    x: {volume_data}.map(d => d.x),
    y: {volume_data}.map(d => d.y),
    marker: {{ color: volColors }},
    name: '成交量'
}}], {{
    plot_bgcolor: '#152230', paper_bgcolor: '#152230',
    font: {{ color: '#8899aa', size: 11 }},
    xaxis: {{ gridcolor: '#1e3040', linecolor: '#2a4050' }},
    yaxis: {{ title: '成交量 (手)', gridcolor: '#1e3040', linecolor: '#2a4050', side: 'right' }},
    margin: {{ l: 50, r: 10, t: 10, b: 40 }},
    showlegend: false,
    config: {{ displayModeBar: false }}
}});

// ===== 数据表格 =====
let tableData = {table_json};
let tbody = document.querySelector('#data-table tbody');
tableData.forEach(row => {{
    let tr = document.createElement('tr');
    let changeClass = row.change.startsWith('+') ? 'up' : (row.change.startsWith('-') ? 'down' : '');
    tr.innerHTML = `
        <td>${{row.date}}</td>
        <td>${{row.open}}</td>
        <td>${{row.high}}</td>
        <td>${{row.low}}</td>
        <td>${{row.close}}</td>
        <td class="${{changeClass}}">${{row.change}}</td>
        <td>${{row.volume}}</td>
    `;
    tbody.appendChild(tr);
}});
</script>

</body>
</html>"""
    return html_content


def main():
    print("=" * 60)
    print("[Start] 生成 HTML 量化分析看板...")
    print("=" * 60)

    # 1. 加载数据
    print(f"\n[Data] 加载 CSV 数据: {CSV_FILE}")
    df = load_data(CSV_FILE)
    print(f"   已加载 {len(df)} 条记录")

    # 2. 计算统计数据
    stats = get_summary_stats(df)
    print(f"   数据区间: {stats['start_date']} ~ {stats['end_date']}")
    print(f"   涨跌幅: {stats['change_pct']}%")

    # 3. 生成 HTML
    print(f"\n[HTML] 生成 HTML 页面...")
    html = generate_html(df, stats)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    file_size_kb = os.path.getsize(HTML_FILE) / 1024
    print(f"[OK] HTML 看板已生成: {HTML_FILE} ({file_size_kb:.0f} KB)")

    print("\n" + "=" * 60)
    print("[Done] 输出文件:")
    print(f"   HTML 看板: {HTML_FILE}")
    print(f"   可直接用浏览器打开，或部署到 GitHub Pages")
    print("=" * 60)


if __name__ == "__main__":
    main()

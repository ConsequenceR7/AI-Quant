# -*- coding: utf-8 -*-
"""
TASK1 HTML看板生成脚本 v2 — 生成完整增强版 ECharts 交互式报告
"""
import pandas as pd
import json
import os
import numpy as np

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(OUTPUT_DIR, "002747_daily.csv")
HTML_FILE = os.path.join(OUTPUT_DIR, "index.html")
STOCK_CODE = "002747"
STOCK_NAME = "埃斯顿"
AUTHOR = "李菓"

# 读取已有的模板 HTML（包含完整结构）
TEMPLATE_PATH = os.path.join(OUTPUT_DIR, "template.html")


def load_data():
    col_map = {
        "交易日期": "date", "开盘价": "open", "最高价": "high",
        "最低价": "low", "收盘价": "close", "成交量(手)": "volume",
        "成交额(元)": "amount", "涨跌幅(%)": "pct_chg",
        "换手率(%)": "turnover_rate",
        "MA5": "ma5", "MA10": "ma10", "MA20": "ma20",
        "MA60": "ma60", "MA120": "ma120", "MA250": "ma250",
        "MACD_DIF": "macd_dif", "MACD_DEA": "macd_dea", "MACD柱": "macd_bar",
        "RSI6": "rsi6", "RSI12": "rsi12", "RSI24": "rsi24",
        "KDJ_K": "kdj_k", "KDJ_D": "kdj_d", "KDJ_J": "kdj_j",
        "BOLL中轨": "boll_mid", "BOLL上轨": "boll_up", "BOLL下轨": "boll_dn",
        "60日波动率": "volatility_60",
    }
    df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
    df = df.rename(columns=col_map)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def build_data_js(df):
    """构建 data.js 文件内容"""
    cols_needed = [
        "open", "high", "low", "close", "volume",
        "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
        "macd_dif", "macd_dea", "macd_bar",
        "rsi6", "rsi12", "rsi24",
        "kdj_k", "kdj_d", "kdj_j",
        "boll_mid", "boll_up", "boll_dn",
    ]
    # 日期
    dates = df["date"].dt.strftime("%Y-%m-%d").tolist()

    data_obj = {"dates": dates}
    for col in cols_needed:
        if col in df.columns:
            series = df[col].dropna()
            # 对齐到完整日期索引
            vals = []
            j = 0
            for i in range(len(df)):
                if pd.isna(df.iloc[i][col]) and col != "volume":
                    vals.append(None)
                else:
                    vals.append(round(float(df.iloc[i][col]), 4))
            data_obj[col] = vals

    # OHLC 数组
    ohlc = []
    for i in range(len(df)):
        ohlc.append([
            round(float(df.iloc[i]["open"]), 2),
            round(float(df.iloc[i]["close"]), 2),
            round(float(df.iloc[i]["low"]), 2),
            round(float(df.iloc[i]["high"]), 2),
        ])
    data_obj["ohlc"] = ohlc

    return "var STOCK_DATA = " + json.dumps(data_obj, ensure_ascii=False) + ";"


def get_stats(df):
    first = float(df.iloc[0]["close"]); last = float(df.iloc[-1]["close"])
    vol_last = df["volatility_60"].dropna()
    return {
        "latest": f"{last:.2f}",
        "change_pct": f"{(last - first) / first * 100:+.2f}",
        "high": f"{df['high'].max():.2f}",
        "low": f"{df['low'].min():.2f}",
        "avg": f"{df['close'].mean():.2f}",
        "avg_vol": f"{df['volume'].mean() / 10000:.2f}万",
        "volatility": f"{vol_last.iloc[-1]:.2f}" if len(vol_last) > 0 else "—",
        "trading_days": len(df),
        "start_date": df.iloc[0]["date"].strftime("%Y-%m-%d"),
        "end_date": df.iloc[-1]["date"].strftime("%Y-%m-%d"),
    }


def build_table_rows(df):
    """最近30天表格"""
    recent = df.tail(30).iloc[::-1]
    rows = ""
    for _, r in recent.iterrows():
        chg = float(r["pct_chg"]) if not pd.isna(r["pct_chg"]) else 0
        cls = "up" if chg > 0 else "down" if chg < 0 else ""
        rows += f"""<tr>
            <td>{r['date'].strftime('%Y-%m-%d')}</td>
            <td>{r['open']:.2f}</td><td>{r['high']:.2f}</td>
            <td>{r['low']:.2f}</td><td>{r['close']:.2f}</td>
            <td class="{cls}">{chg:+.2f}%</td>
            <td>{int(r['volume']):,}</td></tr>"""
    return rows


def build_html(data_js, stats, table_rows):
    """直接拼接完整 HTML"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{STOCK_NAME}({STOCK_CODE}.SZ) 量化研究报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"SimSun","宋体","Microsoft YaHei",serif;background:#f5f5f5;color:#333;line-height:1.8}}
.container{{max-width:1200px;margin:0 auto;padding:20px}}
header{{background:linear-gradient(135deg,#0d47a1,#1565c0);color:#fff;padding:40px 20px;text-align:center;border-radius:8px;margin-bottom:30px}}
header h1{{font-size:30px;margin-bottom:8px}}
header p{{font-size:15px;opacity:.9}}
.section{{background:#fff;border-radius:8px;padding:25px;margin-bottom:25px;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.section h2{{font-size:22px;color:#0d47a1;border-left:5px solid #0d47a1;padding-left:15px;margin-bottom:20px}}
.section h3{{font-size:18px;color:#1565c0;margin:20px 0 15px}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:20px}}
.stat-card{{background:#f8f9fa;border-radius:8px;padding:18px;text-align:center;border:1px solid #e0e0e0}}
.stat-card .value{{font-size:24px;font-weight:bold;color:#0d47a1;margin:6px 0}}
.stat-card .label{{font-size:13px;color:#666}}
.up{{color:#e53935}}.down{{color:#43a047}}
.chart-container{{width:100%;height:500px;margin:20px 0;border:1px solid #e0e0e0;border-radius:4px}}
.chart-tall{{height:600px}}
.analysis-text{{background:#fafafa;border-left:4px solid #0d47a1;padding:15px 20px;margin:15px 0;font-size:15px;color:#444}}
.analysis-text strong{{color:#0d47a1}}
.tag{{display:inline-block;background:#e3f2fd;color:#0d47a1;padding:4px 12px;border-radius:4px;font-size:13px;margin:4px}}
.intro-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:20px 0}}
.intro-card{{background:#f8f9fa;border-radius:8px;padding:20px}}
.intro-card h4{{color:#0d47a1;margin-bottom:10px;font-size:16px}}
.conclusion-box{{background:#e3f2fd;border-radius:8px;padding:20px;margin:15px 0}}
.risk-box{{background:#ffebee;border-radius:8px;padding:20px;margin:15px 0;border:1px solid #ffcdd2}}
.code-block{{background:#263238;color:#aed581;padding:20px;border-radius:8px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.6;white-space:pre-wrap;max-height:500px;overflow-y:auto}}
table{{width:100%;border-collapse:collapse;margin:15px 0;font-size:13px}}
th,td{{border:1px solid #ddd;padding:8px;text-align:center}}
th{{background:#0d47a1;color:#fff}}
tr:nth-child(even){{background:#f8f9fa}}
td.up{{color:#e53935;font-weight:bold}}td.down{{color:#43a047;font-weight:bold}}
.footer{{text-align:center;padding:30px;color:#999;font-size:13px}}
@media(max-width:768px){{.stats-grid,.intro-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>{STOCK_NAME}（{STOCK_CODE}.SZ）量化研究报告</h1>
<p>ECharts交互版 · 数据驱动决策 · 技术面综合分析</p>
<p>报告日期：2026年7月4日 | 数据区间：{stats['start_date']} — {stats['end_date']}（{stats['trading_days']}个交易日）</p>
</header>

<div class="section"><h2>一、数据概览</h2>
<div class="stats-grid">
<div class="stat-card"><div class="label">最新收盘价</div><div class="value">{stats['latest']}元</div></div>
<div class="stat-card"><div class="label">5年累计涨幅</div><div class="value {'up' if stats['change_pct'].startswith('+') else 'down'}">{stats['change_pct']}%</div></div>
<div class="stat-card"><div class="label">5年最高价</div><div class="value">{stats['high']}元</div></div>
<div class="stat-card"><div class="label">5年最低价</div><div class="value">{stats['low']}元</div></div>
<div class="stat-card"><div class="label">5年均价</div><div class="value">{stats['avg']}元</div></div>
<div class="stat-card"><div class="label">日均成交量</div><div class="value">{stats['avg_vol']}手</div></div>
<div class="stat-card"><div class="label">近60日波动率</div><div class="value">{stats['volatility']}%</div></div>
</div></div>

<div class="section"><h2>二、量化交易优势</h2>
<div class="intro-grid">
<div class="intro-card"><h4>数据驱动决策</h4><p>量化交易以海量历史数据为基础，通过数学模型和统计方法发现市场规律，避免人为情绪干扰。</p></div>
<div class="intro-card"><h4>高效执行策略</h4><p>计算机程序可在毫秒级完成交易决策与执行，抓住转瞬即逝的套利机会。</p></div>
<div class="intro-card"><h4>系统性风控</h4><p>量化模型内置严格的风险管理规则，包括止损止盈、仓位控制等。</p></div>
<div class="intro-card"><h4>可回测验证</h4><p>任何策略均可通过历史数据进行回测验证，评估其收益风险特征。</p></div>
</div></div>

<div class="section"><h2>三、基本概念</h2>
<div class="intro-grid">
<div class="intro-card"><h4>K线图（Candlestick）</h4><p>每根K线包含开盘价、最高价、最低价、收盘价四个价格信息。阳线（红色）表示收盘价高于开盘价，阴线（绿色）反之。</p></div>
<div class="intro-card"><h4>移动平均线（MA）</h4><p>MA5/MA10反映短期趋势，MA60反映中期趋势，MA250反映长期趋势。短期均线上穿长期均线为"金叉"买入信号。</p></div>
<div class="intro-card"><h4>MACD指标</h4><p>MACD由DIF线、DEA线和MACD柱组成。DIF上穿DEA为金叉信号，MACD柱由负转正为买入信号。</p></div>
<div class="intro-card"><h4>RSI相对强弱指标</h4><p>RSI>80超买区可能回调，RSI<20超卖区可能反弹。RSI的顶背离是重要的见顶信号。</p></div>
<div class="intro-card"><h4>KDJ随机指标</h4><p>K上穿D为金叉买入信号，K下穿D为死叉卖出信号。J线波动最大，超过100预示极强。</p></div>
<div class="intro-card"><h4>基本面核心指标</h4><p>ROE衡量股东回报效率；毛利率反映产品定价权；EPS是每股收益；营收增速反映成长性。</p></div>
</div></div>

<div class="section"><h2>四、公司概况</h2>
<p><strong>{STOCK_NAME}</strong>（{STOCK_CODE}.SZ）是深交所上市的国产工业机器人及智能制造龙头企业。公司主营业务涵盖工业机器人、运动控制系统、伺服系统及系统集成解决方案，是国内为数不多实现"核心部件+机器人本体+系统集成"全产业链覆盖的企业。</p>
<p style="margin-top:15px;"><strong>核心业务板块：</strong></p>
<p><span class="tag">工业机器人</span><span class="tag">伺服系统</span><span class="tag">运动控制</span><span class="tag">焊接机器人</span><span class="tag">折弯机器人</span><span class="tag">系统集成</span></p>
<p style="margin-top:15px;"><strong>投资亮点：</strong>受益于国产替代加速与智能制造政策推动，公司工业机器人出货量持续增长；核心零部件自研自产能力强，毛利率高于行业平均。但同时也面临行业竞争加剧、下游周期性波动等风险因素。</p>
</div>

<div class="section"><h2>五、技术面分析</h2>

<h3>图1：5年日K线 + 移动平均线（MA5/10/20/60/120/250）+ 成交量</h3>
<div id="chart1" class="chart-container chart-tall"></div>
<div class="analysis-text"><strong>图表解读：</strong>上图展示了{STOCK_NAME}近5年的日K线走势与均线系统。均线系统中MA5/MA10代表短期趋势，MA60代表中期趋势，MA250代表长期趋势。投资者可通过底部dataZoom拖动条选择特定时间区间进行细部观察。成交量在关键突破点位明显放大，表明资金关注度提升。</div>

<h3>图2：近2年日K线 + MACD指标</h3>
<div id="chart2" class="chart-container chart-tall"></div>
<div class="analysis-text"><strong>图表解读：</strong>MACD是判断趋势转折与动能强弱的核心指标。当前需密切关注MACD柱是否由正转负——若出现零轴下方死叉，则需警惕阶段性调整风险；若DIF与DEA均位于零轴上方且MACD柱重新放大，则上涨趋势有望延续。</div>

<h3>图3：近2年日K线 + RSI相对强弱指标</h3>
<div id="chart3" class="chart-container chart-tall"></div>
<div class="analysis-text"><strong>图表解读：</strong>RSI是衡量价格动量的振荡指标。在上涨过程中RSI多次触及80超买线提示短期超买风险。RSI在50上方运行表明市场处于相对强势状态。RSI低于20往往是有效反弹信号。RSI的背离现象（价格新高但RSI未新高）是判断顶部的重要信号。</div>

<h3>图4：近2年日K线 + KDJ随机指标</h3>
<div id="chart4" class="chart-container chart-tall"></div>
<div class="analysis-text"><strong>图表解读：</strong>KDJ指标对价格变化极为敏感。在强势上涨市场中KDJ可能持续在80上方运行呈现"高位钝化"特征。对于趋势投资者，KDJ的高位钝化不必恐慌，但需配合成交量与MACD综合判断。J线若超过100或低于0分别预示极强或极弱状态。</div>

<h3>图5：5年收盘价走势（含布林带BOLL）</h3>
<div id="chart5" class="chart-container chart-tall"></div>
<div class="analysis-text"><strong>图表解读：</strong>布林带（BOLL）由中轨（20日均线）、上轨和下轨组成。股价触及上轨时短期超买可能回调，触及下轨时超卖可能反弹。布林带收窄通常预示变盘窗口临近，布林带扩张则表明趋势行情启动。</div>
</div>

<div class="section"><h2>六、技术面综合研判</h2>
<div class="conclusion-box">
<h4>技术面评分：中性偏积极</h4>
<p>综合MA均线系统、MACD趋势指标、RSI动量指标和KDJ随机指标的多维度分析：</p>
<p style="margin-top:12px;"><strong>积极因素：</strong>（1）中长期均线趋势向好，整体处于上升通道中；（2）MACD指标在多个关键节点给出金叉信号；（3）成交量在上涨波段中配合放大，验证上涨有效性。</p>
<p style="margin-top:8px;"><strong>需关注因素：</strong>（1）短期RSI和KDJ可能进入超买区域；（2）股价距离中期均线较远时有均值回归倾向；（3）布林带开口扩大后可能出现阶段性收敛。</p>
</div></div>

<div class="section"><h2>七、投资建议</h2>
<p><strong>短期（1-3个月）：</strong>关注技术指标超买/超卖信号，RSI>80或KDJ高位死叉时考虑适当减仓；回调至MA60附近且RSI<30时是较好的加仓时机。</p>
<p style="margin-top:12px;"><strong>中期（3-12个月）：</strong>若MACD维持零轴上方运行且均线多头排列不变可保持多头仓位；关注MA60趋势方向，若MA60拐头向下则应降低仓位。</p>
<p style="margin-top:12px;"><strong>长期（1年以上）：</strong>{STOCK_NAME}作为国产工业机器人龙头，受益于智能制造国策和国产替代大趋势，长期成长逻辑清晰。</p>
</div>

<div class="section"><h2>八、风险提示</h2>
<div class="risk-box"><h4 style="color:#c62828">重要风险因素</h4>
<p><strong>1. 行业竞争风险：</strong>工业机器人行业竞争加剧，国内外品牌价格战可能压缩毛利率。</p>
<p><strong>2. 周期风险：</strong>下游制造业投资具有较强周期性，经济下行将导致机器人需求大幅波动。</p>
<p><strong>3. 技术迭代风险：</strong>若公司在AI、协作机器人等新兴方向布局不足，可能丧失竞争优势。</p>
<p><strong>4. 政策风险：</strong>智能制造补贴政策变化可能影响行业景气度。</p>
<p><strong>5. 估值风险：</strong>若未来业绩增速不及预期，高估值面临下杀压力。</p>
<p><strong>6. 数据风险：</strong>本报告基于历史数据，不构成投资建议。过往业绩不代表未来表现。</p>
</div></div>

<div class="section"><h2>九、Python量化分析核心代码</h2>
<p>以下为本报告数据获取与技术指标计算的核心Python代码：</p>
<div class="code-block"># -*- coding: utf-8 -*-
"""量化数据引擎 — 埃斯顿(002747.SZ)"""
import baostock as bs
import pandas as pd, numpy as np

# 1. 获取5年日线数据(前复权)
lg = bs.login()
rs = bs.query_history_k_data_plus("sz.002747",
    "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
    start_date="2021-07-01", end_date="2026-07-04",
    frequency="d", adjustflag="2")
data = []; [data.append(rs.get_row_data()) for _ in iter(lambda: rs.next(), False)]
df = pd.DataFrame(data, columns=rs.fields); bs.logout()
for c in ["open","high","low","close","volume","amount"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# 2. MACD(12,26,9)
e12 = df["close"].ewm(span=12, adjust=False).mean()
e26 = df["close"].ewm(span=26, adjust=False).mean()
df["macd_dif"] = e12 - e26
df["macd_dea"] = df["macd_dif"].ewm(span=9, adjust=False).mean()
df["macd_bar"] = 2 * (df["macd_dif"] - df["macd_dea"])

# 3. RSI(6,12,24)
for p in [6,12,24]:
    d = df["close"].diff(); g = d.clip(lower=0); l = (-d).clip(lower=0)
    rs = g.ewm(alpha=1/p, adjust=False).mean() / l.ewm(alpha=1/p, adjust=False).mean()
    df[f"rsi{{p}}"] = 100 - 100/(1+rs)

# 4. KDJ(9,3,3)
n=9; ln=df["low"].rolling(n).min(); hn=df["high"].rolling(n).max()
rsv=(df["close"]-ln)/(hn-ln+1e-10)*100
k_vals,d_vals=[],[]; kp=dp=50.0
for r in rsv:
    if np.isnan(r): k_vals.append(np.nan); d_vals.append(np.nan)
    else: k=2/3*kp+1/3*r; d=2/3*dp+1/3*k; k_vals.append(k); d_vals.append(d); kp,dp=k,d
df["kdj_k"]=k_vals; df["kdj_d"]=d_vals
df["kdj_j"]=[3*k-2*d for k,d in zip(k_vals,d_vals)]

# 5. BOLL(20,2)
df["boll_mid"]=df["close"].rolling(20).mean()
s=df["close"].rolling(20).std()
df["boll_up"]=df["boll_mid"]+2*s; df["boll_dn"]=df["boll_mid"]-2*s

df.to_csv("002747_daily.csv",index=False,encoding="utf-8-sig")</div>
<p style="margin-top:15px;color:#666;font-size:13px;">代码说明：基于Baostock接口获取A股日线数据（前复权），计算MACD、RSI、KDJ、BOLL等经典技术指标。ECharts交互版HTML使用相同数据，通过JavaScript在前端实现dataZoom缩放、tooltip悬浮提示等交互功能。</p>
</div>

<div class="section"><h2>十、近期交易数据一览（近30个交易日）</h2>
<div style="overflow-x:auto"><table>
<thead><tr><th>日期</th><th>开盘价</th><th>最高价</th><th>最低价</th><th>收盘价</th><th>涨跌幅</th><th>成交量(手)</th></tr></thead>
<tbody>{table_rows}</tbody>
</table></div></div>

<div class="footer"><p>&copy; 2026 量化研究报告 | 数据来源 Baostock / Tushare Pro | 作者：{AUTHOR}</p>
<p>风险提示：股市有风险，投资需谨慎。本报告仅供参考，不构成投资建议。</p></div>
</div>

<script>
{data_js}

(function() {{
var D = STOCK_DATA; // 数据
var n = D.dates.length;
var idx2y = D.ohlc.slice(-250*2).map(function(d){{ return d[1]; }}); // 近2年收盘

// 工具函数: 取数组从 tail 往前 N 个
function tail(arr, N) {{ return arr.slice(Math.max(0, arr.length - N)); }}
function tailD(N) {{ return D.dates.slice(Math.max(0, n - N)); }}
function valOr(arr, i, fallback) {{ var v = arr[i]; return (v == null || isNaN(v)) ? (fallback||0) : v; }}

// ===== 图1: K线+均线+成交量 =====
var c1 = echarts.init(document.getElementById('chart1'));
c1.setOption({{
    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
    grid: [{{ left:'8%', right:'3%', top:'5%', height:'55%' }}, {{ left:'8%', right:'3%', top:'68%', height:'20%' }}],
    xAxis: [{{ type:'category', data:D.dates, gridIndex:0, axisLabel:{{ show:false }} }},
            {{ type:'category', data:D.dates, gridIndex:1, axisLabel:{{ rotate:30, fontSize:10 }} }}],
    yAxis: [{{ type:'value', gridIndex:0, scale:true, splitArea:{{ show:true }}, position:'right' }},
            {{ type:'value', gridIndex:1, scale:true, position:'right' }}],
    series: [
        {{ name:'K线', type:'candlestick', data:D.ohlc,
           itemStyle:{{ color:'#e53935',color0:'#43a047',borderColor:'#e53935',borderColor0:'#43a047' }},
           markPoint:{{ data:[{{ type:'max',name:'最高',symbolSize:50,itemStyle:{{ color:'#e53935' }}}},
                              {{ type:'min',name:'最低',symbolSize:50,itemStyle:{{ color:'#43a047' }}}}] }} }},
        {{ name:'MA5',  type:'line', data:D.ma5,  smooth:true, symbol:'none', lineStyle:{{ color:'#42a5f5',width:1,type:'dashed' }} }},
        {{ name:'MA10', type:'line', data:D.ma10, smooth:true, symbol:'none', lineStyle:{{ color:'#ff9800',width:1,type:'dashed' }} }},
        {{ name:'MA20', type:'line', data:D.ma20, smooth:true, symbol:'none', lineStyle:{{ color:'#ab47bc',width:1,type:'dashed' }} }},
        {{ name:'MA60', type:'line', data:D.ma60, smooth:true, symbol:'none', lineStyle:{{ color:'#66bb6a',width:1,type:'dashed' }} }},
        {{ name:'MA120',type:'line', data:D.ma120,smooth:true, symbol:'none', lineStyle:{{ color:'#ef5350',width:1.2,type:'dotted' }} }},
        {{ name:'MA250',type:'line', data:D.ma250,smooth:true, symbol:'none', lineStyle:{{ color:'#8d6e63',width:1.2,type:'dotted' }} }},
        {{ name:'成交量', type:'bar', xAxisIndex:1, yAxisIndex:1, data:D.volume.map(function(v,i){{
            var o=D.ohlc[i]; return {{ value:v, itemStyle:{{ color: o[1]>=o[0] ? '#e53935' : '#43a047' }} }}; }}) }}
    ],
    dataZoom:[{{ type:'slider',xAxisIndex:[0,1],start:50,end:100,height:24,bottom:20 }},
              {{ type:'inside',xAxisIndex:[0,1],start:50,end:100 }}],
    toolbox:{{ feature:{{ saveAsImage:{{ title:'保存' }} }} }}
}});

// ===== 辅助: K线+副图 =====
function makeSubChart(domId, subSeries, subGridTop, subName) {{
    var chart = echarts.init(document.getElementById(domId));
    var opt = {{
        tooltip: {{ trigger:'axis', axisPointer:{{ type:'cross' }} }},
        grid: [{{ left:'8%', right:'3%', top:'5%', height:'48%' }},
               {{ left:'8%', right:'3%', top: subGridTop||'58%', height:'30%' }}],
        xAxis: [{{ type:'category', data:D.dates, gridIndex:0, axisLabel:{{ show:false }} }},
                {{ type:'category', data:D.dates, gridIndex:1, axisLabel:{{ rotate:30, fontSize:10 }} }}],
        yAxis: [{{ type:'value', gridIndex:0, scale:true, position:'right' }},
                {{ type:'value', gridIndex:1, scale:true, position:'right' }}],
        series: [
            {{ name:'K线', type:'candlestick', data:D.ohlc,
               itemStyle:{{ color:'#e53935',color0:'#43a047',borderColor:'#e53935',borderColor0:'#43a047' }} }},
            {{ name:'MA20', type:'line', data:D.ma20, smooth:true, symbol:'none',
               lineStyle:{{ color:'#ab47bc',width:1,type:'dashed' }} }},
            {{ name:'MA60', type:'line', data:D.ma60, smooth:true, symbol:'none',
               lineStyle:{{ color:'#66bb6a',width:1,type:'dashed' }} }}
        ].concat(subSeries||[]),
        dataZoom:[{{ type:'slider',xAxisIndex:[0,1],start:60,end:100,height:24,bottom:10 }}],
        toolbox:{{ feature:{{ saveAsImage:{{}} }} }}
    }};
    chart.setOption(opt);
    return chart;
}}

// ===== 图2: MACD =====
makeSubChart('chart2', [
    {{ name:'DIF', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.macd_dif,
       symbol:'none', lineStyle:{{ color:'#e53935',width:1.5 }} }},
    {{ name:'DEA', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.macd_dea,
       symbol:'none', lineStyle:{{ color:'#1565c0',width:1.5 }} }},
    {{ name:'MACD柱', type:'bar', xAxisIndex:1, yAxisIndex:1, data:D.macd_bar.map(function(v){{
       return {{ value:v, itemStyle:{{ color: v>=0 ? '#e53935' : '#43a047' }} }}; }}) }}
], '60%', 'MACD');

// ===== 图3: RSI =====
makeSubChart('chart3', [
    {{ name:'RSI6', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.rsi6,
       symbol:'none', lineStyle:{{ color:'#e53935',width:1 }} }},
    {{ name:'RSI12', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.rsi12,
       symbol:'none', lineStyle:{{ color:'#1565c0',width:1 }} }},
    {{ name:'RSI24', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.rsi24,
       symbol:'none', lineStyle:{{ color:'#66bb6a',width:1 }} }},
    {{ name:'超买线(80)', type:'line', xAxisIndex:1, yAxisIndex:1,
       data:new Array(n).fill(80), symbol:'none',
       lineStyle:{{ color:'#e53935',width:1,type:'dashed' }},
       markArea:{{ silent:true, data:[[{{ yAxis:80, itemStyle:{{ color:'rgba(229,57,53,0.05)' }} }},{{ yAxis:100 }}]] }} }},
    {{ name:'超卖线(20)', type:'line', xAxisIndex:1, yAxisIndex:1,
       data:new Array(n).fill(20), symbol:'none',
       lineStyle:{{ color:'#43a047',width:1,type:'dashed' }},
       markArea:{{ silent:true, data:[[{{ yAxis:0 }},{{ yAxis:20, itemStyle:{{ color:'rgba(67,160,71,0.05)' }} }}]] }} }}
], '58%', 'RSI');

// ===== 图4: KDJ =====
makeSubChart('chart4', [
    {{ name:'K', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.kdj_k,
       symbol:'none', lineStyle:{{ color:'#e53935',width:1.2 }} }},
    {{ name:'D', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.kdj_d,
       symbol:'none', lineStyle:{{ color:'#1565c0',width:1.2 }} }},
    {{ name:'J', type:'line', xAxisIndex:1, yAxisIndex:1, data:D.kdj_j,
       symbol:'none', lineStyle:{{ color:'#ff9800',width:0.8,type:'dotted' }} }},
    {{ name:'超买(80)', type:'line', xAxisIndex:1, yAxisIndex:1,
       data:new Array(n).fill(80), symbol:'none',
       lineStyle:{{ color:'#999',width:1,type:'dashed' }} }},
    {{ name:'超卖(20)', type:'line', xAxisIndex:1, yAxisIndex:1,
       data:new Array(n).fill(20), symbol:'none',
       lineStyle:{{ color:'#999',width:1,type:'dashed' }} }}
], '58%', 'KDJ');

// ===== 图5: 收盘价+布林带 =====
(function() {{
    var c5 = echarts.init(document.getElementById('chart5'));
    c5.setOption({{
        tooltip: {{ trigger:'axis' }},
        grid: {{ left:'8%', right:'3%', top:'5%', height:'80%' }},
        xAxis: {{ type:'category', data:D.dates, axisLabel:{{ rotate:30, fontSize:10 }} }},
        yAxis: {{ type:'value', scale:true, position:'right' }},
        series: [
            {{ name:'上轨', type:'line', data:D.boll_up, symbol:'none',
               lineStyle:{{ color:'#90caf9',width:1 }},
               areaStyle:{{ color:'rgba(144,202,249,0.06)' }} }},
            {{ name:'中轨(MA20)', type:'line', data:D.boll_mid, symbol:'none',
               lineStyle:{{ color:'#ff9800',width:1,type:'dashed' }} }},
            {{ name:'下轨', type:'line', data:D.boll_dn, symbol:'none',
               lineStyle:{{ color:'#90caf9',width:1 }},
               areaStyle:{{ color:'rgba(255,255,255,0.8)' }} }},
            {{ name:'收盘价', type:'line', data:D.close, symbol:'none',
               lineStyle:{{ color:'#0d47a1',width:1.8 }} }}
        ],
        dataZoom:[{{ type:'slider',start:20,end:100,height:24,bottom:10 }},
                  {{ type:'inside',start:20,end:100 }}],
        toolbox:{{ feature:{{ saveAsImage:{{}} }} }},
        legend:{{ data:['上轨','中轨(MA20)','下轨','收盘价'], top:5 }}
    }});
}})();

// 响应式
window.addEventListener('resize', function() {{
    [c1].forEach(function(c){{ c.resize(); }});
    ['chart2','chart3','chart4','chart5'].forEach(function(id){{
        var inst = echarts.getInstanceByDom(document.getElementById(id));
        if(inst) inst.resize();
    }});
}});
}})();
</script>
</body>
</html>'''


def main():
    print("=" * 60)
    print("[Start] 生成增强版 HTML 看板 v2...")
    print("=" * 60)

    df = load_data()
    print(f"[Data] 已加载 {len(df)} 条记录")

    stats = get_stats(df)
    print(f"   涨跌幅: {stats['change_pct']}%")

    data_js = build_data_js(df)
    table_rows = build_table_rows(df)
    html = build_html(data_js, stats, table_rows)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(HTML_FILE) / 1024
    print(f"[OK] HTML 已生成: {HTML_FILE} ({size_kb:.0f} KB)")
    print("=" * 60)
    print("[Done] 用浏览器打开 index.html 或部署到 GitHub Pages")


if __name__ == "__main__":
    main()

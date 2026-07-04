"""
量化交易数据引擎 - TASK1
功能：
  1. 获取沪深股市中某一股票多年交易数据
  2. 计算技术指标：MACD, RSI, KDJ, MA
  3. 画出每日收盘价的曲线图
  4. 将数据保存成 csv 格式数据

数据来源：Baostock（免费开源证券数据平台）
"""

import baostock as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ============================================================
# 配置区
# ============================================================
STOCK_CODE_BS = "sz.002747"   # 埃斯顿
STOCK_CODE = "002747"
STOCK_NAME = "埃斯顿"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(OUTPUT_DIR, f"{STOCK_CODE}_daily.csv")
CHART_FILE = os.path.join(OUTPUT_DIR, f"{STOCK_CODE}_close_price.png")


def compute_indicators(df):
    """计算技术指标: MA, MACD, RSI, KDJ"""
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    # ---- 移动均线 ----
    for w in [5, 10, 20, 60, 120, 250]:
        df[f"ma{w}"] = df["close"].rolling(w).mean()

    # ---- MACD (12, 26, 9) ----
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_dif"] = ema12 - ema26
    df["macd_dea"] = df["macd_dif"].ewm(span=9, adjust=False).mean()
    df["macd_bar"] = 2 * (df["macd_dif"] - df["macd_dea"])

    # ---- RSI (6, 12, 24) ----
    for period in [6, 12, 24]:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df[f"rsi{period}"] = 100 - (100 / (1 + rs))

    # ---- KDJ (9, 3, 3) ----
    n = 9
    low_n = df["low"].rolling(n).min()
    high_n = df["high"].rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n + 1e-10) * 100
    k_vals, d_vals, j_vals = [], [], []
    k_prev, d_prev = 50.0, 50.0
    for r in rsv:
        if np.isnan(r):
            k_vals.append(np.nan)
            d_vals.append(np.nan)
            j_vals.append(np.nan)
        else:
            k = 2/3 * k_prev + 1/3 * r
            d = 2/3 * d_prev + 1/3 * k
            j = 3 * k - 2 * d
            k_vals.append(k)
            d_vals.append(d)
            j_vals.append(j)
            k_prev, d_prev = k, d
    df["kdj_k"] = k_vals
    df["kdj_d"] = d_vals
    df["kdj_j"] = j_vals

    # ---- 布林带 (20, 2) ----
    df["boll_mid"] = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["boll_up"] = df["boll_mid"] + 2 * std20
    df["boll_dn"] = df["boll_mid"] - 2 * std20

    # ---- 波动率(60日) ----
    df["volatility_60"] = df["pct_chg"].rolling(60).std()

    return df


def fetch_stock_daily(bs_code, start_date, end_date):
    """获取股票日线数据"""
    print(f"\n[Data] 正在获取 {bs_code} 从 {start_date} 到 {end_date} 的日线数据...")

    lg = bs.login()
    if lg.error_code != "0":
        raise ConnectionError(f"Baostock 登录失败: {lg.error_msg}")
    print("   Baostock 登录成功")

    fields = "date,open,high,low,close,preclose,volume,amount,turn,pctChg,isST"
    rs = bs.query_history_k_data_plus(
        bs_code, fields, start_date=start_date, end_date=end_date,
        frequency="d", adjustflag="2"
    )

    if rs.error_code != "0":
        bs.logout()
        raise ValueError(f"数据查询失败: {rs.error_msg}")

    data_list = []
    while rs.next():
        data_list.append(rs.get_row_data())
    bs.logout()

    if not data_list:
        raise ValueError(f"未获取到 {bs_code} 的数据")

    df = pd.DataFrame(data_list, columns=rs.fields)
    if "isST" in df.columns:
        df = df[df["isST"] != "1"]

    numeric_cols = ["open", "high", "low", "close", "preclose",
                    "volume", "amount", "turn", "pctChg"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["close"]).reset_index(drop=True)

    df = df.rename(columns={
        "date": "trade_date", "preclose": "pre_close",
        "volume": "vol", "pctChg": "pct_chg", "turn": "turnover_rate",
    })
    df["change"] = df["close"] - df["pre_close"]
    df = df.sort_values("trade_date").reset_index(drop=True)
    df["trade_date_dt"] = pd.to_datetime(df["trade_date"])
    df["trade_date"] = df["trade_date_dt"].dt.strftime("%Y%m%d")

    # 计算技术指标
    print("   正在计算技术指标 (MACD, RSI, KDJ, BOLL)...")
    df = compute_indicators(df)

    # 过滤出有效指标区间
    df = df.dropna(subset=["ma20"]).reset_index(drop=True)

    print(f"[OK] 成功获取 {len(df)} 条有效交易日数据")
    print(f"   数据范围：{df['trade_date'].min()} ~ {df['trade_date'].max()}")
    return df


def print_data_summary(df):
    """打印数据摘要"""
    print("\n" + "=" * 60)
    print("[Summary] 数据摘要")
    print("=" * 60)
    print(f"交易日数量: {len(df)} 天")
    print(f"开盘价范围: {df['open'].min():.2f} ~ {df['open'].max():.2f}")
    print(f"收盘价范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
    print(f"最高价范围: {df['high'].min():.2f} ~ {df['high'].max():.2f}")
    print(f"最低价范围: {df['low'].min():.2f} ~ {df['low'].max():.2f}")
    print(f"日均成交量: {df['vol'].mean():.0f} 手")
    print(f"日均成交额: {df['amount'].mean():.0f} 元")
    if "volatility_60" in df.columns and not df["volatility_60"].dropna().empty:
        print(f"近60日波动率: {df['volatility_60'].dropna().iloc[-1]:.2f}%")

    first_close = df.iloc[0]["close"]
    last_close = df.iloc[-1]["close"]
    change_pct = (last_close - first_close) / first_close * 100
    print(f"\n区间涨跌幅: {change_pct:.2f}%")
    print(f"起始收盘价 ({df.iloc[0]['trade_date']}): {first_close:.2f}")
    print(f"期末收盘价 ({df.iloc[-1]['trade_date']}): {last_close:.2f}")

    print("\n前5行数据预览:")
    preview_cols = [c for c in ["trade_date", "open", "close",
                                 "macd_dif", "rsi6", "kdj_k"] if c in df.columns]
    print(df[preview_cols].head())


def plot_close_price(df, stock_code, stock_name, output_path):
    """绘制收盘价曲线图"""
    print(f"\n[Chart] 正在绘制 {stock_name}({stock_code}) 每日收盘价曲线图...")
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 1, figsize=(14, 9),
                             gridspec_kw={"height_ratios": [3, 1]})

    ax1 = axes[0]
    ax1.plot(df["trade_date_dt"], df["close"],
             color="#1f77b4", linewidth=1.2, label="每日收盘价", alpha=0.9)
    for w, c, ls in [(20, "#ff7f0e", "--"), (60, "#2ca02c", "--"),
                      (120, "#d62728", "-.")]:
        col = f"ma{w}"
        if col in df.columns and df[col].notna().any():
            ax1.plot(df["trade_date_dt"], df[col],
                     color=c, linewidth=1.0, linestyle=ls, label=f"{w}日均线")

    ax1.set_title(f"图1：{stock_name}({stock_code}) 每日收盘价走势图",
                  fontsize=14, fontweight="bold")
    ax1.set_ylabel("价格（元）", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

    max_idx = df["close"].idxmax()
    min_idx = df["close"].idxmin()
    for idx, color, label, offset in [
        (max_idx, "red", "最高", 10), (min_idx, "green", "最低", -15)]:
        ax1.annotate(f'{label}: {df.iloc[idx]["close"]:.2f}',
                     xy=(df.iloc[idx]["trade_date_dt"], df.iloc[idx]["close"]),
                     xytext=(10, offset), textcoords="offset points",
                     fontsize=9, color=color,
                     arrowprops=dict(arrowstyle="->", color=color, alpha=0.7))

    ax2 = axes[1]
    colors = ["#d62728" if df.iloc[i]["close"] >= df.iloc[i]["open"]
              else "#1f77b4" for i in range(len(df))]
    ax2.bar(df["trade_date_dt"], df["vol"] / 10000, color=colors, alpha=0.7, width=1)
    ax2.set_title("图2：每日成交量", fontsize=12, fontweight="bold")
    ax2.set_ylabel("成交量（万手）", fontsize=11)
    ax2.set_xlabel("日期", fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 收盘价曲线图已保存至: {output_path}")


def save_to_csv(df, output_path):
    """保存为CSV"""
    save_cols = ["trade_date", "open", "high", "low", "close", "pre_close",
                 "change", "pct_chg", "vol", "amount", "turnover_rate",
                 "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
                 "macd_dif", "macd_dea", "macd_bar",
                 "rsi6", "rsi12", "rsi24",
                 "kdj_k", "kdj_d", "kdj_j",
                 "boll_mid", "boll_up", "boll_dn", "volatility_60"]
    available_cols = [c for c in save_cols if c in df.columns]
    df_save = df[available_cols].copy()
    rename_dict = {
        "trade_date": "交易日期", "open": "开盘价", "high": "最高价", "low": "最低价",
        "close": "收盘价", "pre_close": "前收盘价", "change": "涨跌额",
        "pct_chg": "涨跌幅(%)", "vol": "成交量(手)", "amount": "成交额(元)",
        "turnover_rate": "换手率(%)",
        "ma5": "MA5", "ma10": "MA10", "ma20": "MA20", "ma60": "MA60",
        "ma120": "MA120", "ma250": "MA250",
        "macd_dif": "MACD_DIF", "macd_dea": "MACD_DEA", "macd_bar": "MACD柱",
        "rsi6": "RSI6", "rsi12": "RSI12", "rsi24": "RSI24",
        "kdj_k": "KDJ_K", "kdj_d": "KDJ_D", "kdj_j": "KDJ_J",
        "boll_mid": "BOLL中轨", "boll_up": "BOLL上轨", "boll_dn": "BOLL下轨",
        "volatility_60": "60日波动率",
    }
    df_save = df_save.rename(columns={k: v for k, v in rename_dict.items()
                                       if k in df_save.columns})
    df_save.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] 数据已保存至: {output_path}")


def main():
    print("=" * 60)
    print("[Start] 量化交易数据引擎 v2 (数据来源: Baostock)")
    print("=" * 60)

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365 * 5)  # 5年数据
    end_date = end_dt.strftime("%Y-%m-%d")
    start_date = start_dt.strftime("%Y-%m-%d")

    df = fetch_stock_daily(STOCK_CODE_BS, start_date, end_date)
    print_data_summary(df)
    plot_close_price(df, STOCK_CODE, STOCK_NAME, CHART_FILE)
    save_to_csv(df, CSV_FILE)

    print("\n" + "=" * 60)
    print("[Done] 任务完成！输出文件：")
    print(f"   CSV 数据文件: {CSV_FILE}")
    print(f"   走势图表:     {CHART_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()

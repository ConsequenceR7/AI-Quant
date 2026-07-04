"""
量化交易数据引擎 - TASK1
功能：
  1. 获取沪深股市中某一股票过去一年内每个交易日交易数据
  2. 画出每日收盘价的曲线图
  3. 将数据保存成 csv 格式数据

数据来源：Baostock（免费开源证券数据平台，无需注册和 token）
官网：http://baostock.com

Tushare 注册信息（任务要求平台注册）：
  Token: 请替换为你的真实 token（从 https://www.tushare.pro/ 获取）
  官网: https://www.tushare.pro/
  注: Tushare 免费账户 daily 接口权限有限，故本脚本使用 Baostock 作为数据源
"""

import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys

# 修复 Windows GBK 控制台编码问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ============================================================
# 配置区
# ============================================================
# 股票代码（baostock 格式：sh.600519 或 sz.000001）
STOCK_CODE_BS = "sz.002747"   # 埃斯顿
STOCK_CODE = "002747"
STOCK_NAME = "埃斯顿"

# 输出路径
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(OUTPUT_DIR, f"{STOCK_CODE}_daily.csv")
CHART_FILE = os.path.join(OUTPUT_DIR, f"{STOCK_CODE}_close_price.png")


def fetch_stock_daily(bs_code, start_date, end_date):
    """
    获取股票日线数据（使用 Baostock）

    参数:
        bs_code: Baostock 格式股票代码（如 sh.600519）
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    返回:
        pandas DataFrame，包含每日交易数据
    """
    print(f"\n[Data] 正在获取 {bs_code} 从 {start_date} 到 {end_date} 的日线数据...")

    # 登录 baostock（匿名即可）
    lg = bs.login()
    if lg.error_code != "0":
        raise ConnectionError(f"Baostock 登录失败: {lg.error_msg}")
    print("   Baostock 登录成功")

    # 查询日K线数据
    # 字段: date, open, high, low, close, preclose, volume, amount,
    #       adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM, pcfNcfTTM, isST
    fields = "date,open,high,low,close,preclose,volume,amount,turn,pctChg,isST"
    rs = bs.query_history_k_data_plus(
        bs_code,
        fields,
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"  # 前复权
    )

    if rs.error_code != "0":
        bs.logout()
        raise ValueError(f"数据查询失败: {rs.error_msg}")

    # 将结果转为 DataFrame
    data_list = []
    while rs.next():
        data_list.append(rs.get_row_data())
    bs.logout()

    if not data_list:
        raise ValueError(f"未获取到 {bs_code} 的数据，请检查股票代码是否正确")

    df = pd.DataFrame(data_list, columns=rs.fields)

    # 过滤掉非交易日
    if "isST" in df.columns:
        df = df[df["isST"] != "1"]

    # 转换数据类型
    numeric_cols = ["open", "high", "low", "close", "preclose",
                    "volume", "amount", "turn", "pctChg"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 剔除空值行
    df = df.dropna(subset=["close"]).reset_index(drop=True)

    if df.empty:
        raise ValueError("过滤后无有效数据")

    # 统一列名（与 tushare 兼容）
    df = df.rename(columns={
        "date": "trade_date",
        "preclose": "pre_close",
        "volume": "vol",
        "pctChg": "pct_chg",
        "turn": "turnover_rate",
    })

    # 计算涨跌额
    if "change" not in df.columns:
        df["change"] = df["close"] - df["pre_close"]

    # 按交易日期升序排列
    df = df.sort_values("trade_date").reset_index(drop=True)

    # 将 trade_date 转换为 datetime 格式便于绘图
    df["trade_date_dt"] = pd.to_datetime(df["trade_date"])
    # 确保 trade_date 是 YYYYMMDD 字符串格式
    df["trade_date"] = df["trade_date_dt"].dt.strftime("%Y%m%d")

    print(f"[OK] 成功获取 {len(df)} 条交易日数据")
    print(f"   数据范围：{df['trade_date'].min()} ~ {df['trade_date'].max()}")

    return df


def print_data_summary(df):
    """打印数据摘要信息"""
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

    # 计算收益率
    first_close = df.iloc[0]["close"]
    last_close = df.iloc[-1]["close"]
    change_pct = (last_close - first_close) / first_close * 100
    print(f"\n区间涨跌幅: {change_pct:.2f}%")
    print(f"起始收盘价 ({df.iloc[0]['trade_date']}): {first_close:.2f}")
    print(f"期末收盘价 ({df.iloc[-1]['trade_date']}): {last_close:.2f}")

    # 展示前5行数据
    print("\n前5行数据预览:")
    preview_cols = [c for c in ["trade_date", "open", "high", "low",
                                 "close", "vol", "amount"] if c in df.columns]
    print(df[preview_cols].head())


def plot_close_price(df, stock_code, stock_name, output_path):
    """
    绘制每日收盘价曲线图
    """
    print(f"\n[Chart] 正在绘制 {stock_name}({stock_code}) 每日收盘价曲线图...")

    # 设置中文字体
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 1, figsize=(14, 9),
                             gridspec_kw={"height_ratios": [3, 1]})

    # ---- 子图1：收盘价走势 + 移动均线 ----
    ax1 = axes[0]
    ax1.plot(df["trade_date_dt"], df["close"],
             color="#1f77b4", linewidth=1.2, label="每日收盘价", alpha=0.9)

    # 计算并绘制 20 日/60 日均线
    if len(df) >= 20:
        df["ma20"] = df["close"].rolling(window=20).mean()
        ax1.plot(df["trade_date_dt"], df["ma20"],
                 color="#ff7f0e", linewidth=1.0, linestyle="--", label="20日均线")
    if len(df) >= 60:
        df["ma60"] = df["close"].rolling(window=60).mean()
        ax1.plot(df["trade_date_dt"], df["ma60"],
                 color="#2ca02c", linewidth=1.0, linestyle="--", label="60日均线")

    ax1.set_title(f"图1：{stock_name}({stock_code}) 每日收盘价走势图",
                  fontsize=14, fontweight="bold")
    ax1.set_ylabel("价格（元）", fontsize=11)
    ax1.legend(loc="upper left", fontsize=10)
    ax1.grid(True, alpha=0.3)

    # 格式化 x 轴日期
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

    # 标注最高点和最低点
    max_idx = df["close"].idxmax()
    min_idx = df["close"].idxmin()
    ax1.annotate(f'最高: {df.iloc[max_idx]["close"]:.2f}',
                 xy=(df.iloc[max_idx]["trade_date_dt"], df.iloc[max_idx]["close"]),
                 xytext=(10, 10), textcoords="offset points",
                 fontsize=9, color="red",
                 arrowprops=dict(arrowstyle="->", color="red", alpha=0.7))
    ax1.annotate(f'最低: {df.iloc[min_idx]["close"]:.2f}',
                 xy=(df.iloc[min_idx]["trade_date_dt"], df.iloc[min_idx]["close"]),
                 xytext=(10, -15), textcoords="offset points",
                 fontsize=9, color="green",
                 arrowprops=dict(arrowstyle="->", color="green", alpha=0.7))

    # ---- 子图2：成交量柱状图 ----
    ax2 = axes[1]
    colors = ["#d62728" if df.iloc[i]["close"] >= df.iloc[i]["open"]
              else "#1f77b4" for i in range(len(df))]
    ax2.bar(df["trade_date_dt"], df["vol"] / 10000, color=colors, alpha=0.7, width=1)
    ax2.set_title("图2：每日成交量", fontsize=12, fontweight="bold")
    ax2.set_ylabel("成交量（万手）", fontsize=11)
    ax2.set_xlabel("日期", fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"[OK] 收盘价曲线图已保存至: {output_path}")


def save_to_csv(df, output_path):
    """
    将数据保存为 CSV 文件
    """
    save_cols = ["trade_date", "open", "high", "low", "close",
                 "pre_close", "change", "pct_chg", "vol", "amount"]
    available_cols = [c for c in save_cols if c in df.columns]
    df_save = df[available_cols].copy()

    # 重命名为中文列名
    rename_dict = {
        "trade_date": "交易日期",
        "open": "开盘价",
        "high": "最高价",
        "low": "最低价",
        "close": "收盘价",
        "pre_close": "前收盘价",
        "change": "涨跌额",
        "pct_chg": "涨跌幅(%)",
        "vol": "成交量(手)",
        "amount": "成交额(元)",
    }
    df_save = df_save.rename(columns={k: v for k, v in rename_dict.items()
                                       if k in df_save.columns})

    df_save.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] 数据已保存至: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("[Start] 量化交易数据引擎 (数据来源: Baostock)")
    print("=" * 60)

    # 1. 计算日期范围（过去一年）
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365)
    end_date = end_dt.strftime("%Y-%m-%d")
    start_date = start_dt.strftime("%Y-%m-%d")

    # 2. 获取日线数据
    df = fetch_stock_daily(STOCK_CODE_BS, start_date, end_date)

    # 3. 打印数据摘要
    print_data_summary(df)

    # 4. 绘制收盘价曲线图
    plot_close_price(df, STOCK_CODE, STOCK_NAME, CHART_FILE)

    # 5. 保存为 CSV
    save_to_csv(df, CSV_FILE)

    print("\n" + "=" * 60)
    print("[Done] 任务完成！输出文件：")
    print(f"   CSV 数据文件: {CSV_FILE}")
    print(f"   走势图表:     {CHART_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()

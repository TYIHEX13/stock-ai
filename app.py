import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="多品种多周期分析", layout="wide")
st.title("多品种多时间周期分析 + 模拟盘")

# 初始化模拟盘记录
if "trades" not in st.session_state:
    st.session_state.trades = []

symbol_options = {
    "现货黄金 (XAUUSD)": "GC=F",
    "黄金期货 (GC=F)": "GC=F",
    "比特币 (BTC-USD)": "BTC-USD",
    "欧元美元 (EURUSD=X)": "EURUSD=X",
    "英镑美元 (GBPUSD=X)": "GBPUSD=X",
    "美元日元 (USDJPY=X)": "USDJPY=X",
    "苹果 (AAPL)": "AAPL",
    "特斯拉 (TSLA)": "TSLA"
}

selected_name = st.sidebar.selectbox("选择品种", list(symbol_options.keys()))
symbol = symbol_options[selected_name]
period = st.sidebar.selectbox("历史长度", ["5d", "1mo", "3mo"], index=1)

timeframes = {
    "5分钟": "5m",
    "15分钟": "15m",
    "30分钟": "30m",
    "1小时": "1h",
    "3小时": "1h",
    "4小时": "1h",
    "6小时": "1h",
    "1天": "1d",
    "1周": "1wk"
}

bull_count = 0
bear_count = 0

tabs = st.tabs(list(timeframes.keys()))

for i, (name, interval) in enumerate(timeframes.items()):
    with tabs[i]:
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                st.warning(f"{name} 暂时没有数据")
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            close = df["Close"]
            last_close = float(close.iloc[-1])

            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean() if len(close) >= 60 else None

            rsi_value = None
            if len(close) >= 15:
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_value = float(rsi.iloc[-1])

            macd_signal = "无"
            if len(close) >= 26:
                exp12 = close.ewm(span=12, adjust=False).mean()
                exp26 = close.ewm(span=26, adjust=False).mean()
                macd_line = exp12 - exp26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_val = float(macd_line.iloc[-1])
                signal_val = float(signal_line.iloc[-1])
                macd_signal = "多头" if macd_val > signal_val else "空头"

            bb_status = "中轨附近"
            if len(close) >= 20:
                mid = close.rolling(20).mean()
                std = close.rolling(20).std()
                upper = mid + 2 * std
                lower = mid - 2 * std
                if last_close > float(upper.iloc[-1]):
                    bb_status = "触及上轨（超买）"
                elif last_close < float(lower.iloc[-1]):
                    bb_status = "触及下轨（超卖）"

            score = 0
            if len(close) >= 20:
                ma20_val = float(ma20.iloc[-1])
                if last_close > ma20_val:
                    score += 1
                else:
                    score -= 1
            if rsi_value is not None:
                if rsi_value < 30:
                    score += 1
                elif rsi_value > 70:
                    score -= 1
            if macd_signal == "多头":
                score += 1
            elif macd_signal == "空头":
                score -= 1
            if "超卖" in bb_status:
                score += 1
            elif "超买" in bb_status:
                score -= 1

            signal = "观望"
            if score >= 2:
                signal = "偏多"
                bull_count += 1
            elif score <= -2:
                signal = "偏空"
                bear_count += 1

            trend = "震荡"
            if ma60 is not None:
                ma60_val = float(ma60.iloc[-1])
                if last_close > ma20_val > ma60_val:
                    trend = "多头趋势"
                elif last_close < ma20_val < ma60_val:
                    trend = "空头趋势"

            st.subheader(f"{selected_name} · {name}")
            st.caption(f"最新时间：{df.index[-1]}")
            st.metric("最新价格", f"{last_close:.2f}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**信号**：{signal}")
                st.write(f"**趋势**：{trend}")
            with c2:
                st.write(f"**RSI**：{rsi_value:.1f}" if rsi_value else "**RSI**：-")
                st.write(f"**MACD**：{macd_signal}")
            with c3:
                st.write(f"**布林带**：{bb_status}")

            st.line_chart(close)

        except Exception as e:
            st.error(f"{name} 出错：{e}")

# 共振汇总
st.divider()
st.subheader("多周期共振与操作建议")

col_a, col_b = st.columns(2)
with col_a:
    st.metric("看多周期数", bull_count)
with col_b:
    st.metric("看空周期数", bear_count)

if bull_count >= 6:
    st.success("【强共振偏多】可关注做多机会")
elif bear_count >= 6:
    st.error("【强共振偏空】可关注做空机会")
elif bull_count >= 4:
    st.info("【偏多共振】谨慎看多")
elif bear_count >= 4:
    st.info("【偏空共振】谨慎看空")
else:
    st.warning("【信号分歧】建议观望")

# ========== 模拟盘 ==========
st.divider()
st.subheader("模拟盘记录")

with st.form("trade_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        direction = st.selectbox("方向", ["做多", "做空"])
    with col2:
        entry_price = st.number_input("开仓价格", min_value=0.0, value=0.0, step=0.1)
    with col3:
        exit_price = st.number_input("平仓价格（没平仓填0）", min_value=0.0, value=0.0, step=0.1)
    
    note = st.text_input("备注（可选）")
    submitted = st.form_submit_button("添加记录")

    if submitted and entry_price > 0:
        profit = 0
        if exit_price > 0:
            if direction == "做多":
                profit = exit_price - entry_price
            else:
                profit = entry_price - exit_price
        
        st.session_state.trades.append({
            "时间": datetime.now().strftime("%m-%d %H:%M"),
            "品种": selected_name,
            "方向": direction,
            "开仓价": entry_price,
            "平仓价": exit_price if exit_price > 0 else "持仓中",
            "盈亏": round(profit, 2) if exit_price > 0 else "-",
            "备注": note
        })
        st.success("已添加记录")

if st.session_state.trades:
    st.write("历史记录：")
    st.dataframe(pd.DataFrame(st.session_state.trades))
    
    closed = [t for t in st.session_state.trades if t["盈亏"] != "-"]
    if closed:
        total_profit = sum([t["盈亏"] for t in closed])
        win = len([t for t in closed if t["盈亏"] > 0])
        st.metric("总盈亏", f"{total_profit:.2f}")
        st.write(f"已平仓次数：{len(closed)}，盈利次数：{win}")
else:
    st.info("暂无模拟交易记录")

st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 免费数据，仅供参考")
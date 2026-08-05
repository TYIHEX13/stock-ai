import streamlit as st
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="免费多周期分析", layout="wide")
st.title("免费多时间周期股票/黄金分析")

symbol = st.sidebar.text_input("代码（黄金 GC=F，股票例如 AAPL）", value="GC=F")
period = st.sidebar.selectbox("历史长度", ["5d", "1mo", "3mo"], index=1)

timeframes = {
    "5分钟": "5m",
    "15分钟": "15m",
    "30分钟": "30m",
    "1小时": "1h",
    "1天": "1d",
    "1周": "1wk"
}

tabs = st.tabs(list(timeframes.keys()))

for i, (name, interval) in enumerate(timeframes.items()):
    with tabs[i]:
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if df.empty:
                st.warning(f"{name} 暂时没有数据")
                continue

            st.subheader(f"{symbol} · {name}")
            st.caption(f"最新时间：{df.index[-1]}")

            last_close = float(df["Close"].iloc[-1])
            st.metric("最新收盘价", f"{last_close:.2f}")

            # 简单信号
            if len(df) >= 20:
                ma20 = df["Close"].rolling(20).mean().iloc[-1]
                if last_close > ma20:
                    signal = "偏多（价格在均线上方）"
                else:
                    signal = "偏空（价格在均线下方）"
            else:
                signal = "数据不足，观望"

            st.success(f"**当前信号：{signal}**")
            st.line_chart(df["Close"])

        except Exception as e:
            st.error(f"{name} 出错：{e}")

st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 纯免费数据")
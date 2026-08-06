import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="多品种多周期分析", layout="wide")
st.title("多品种多时间周期分析")

# 品种选择
symbol_options = {
    "黄金 (GC=F)": "GC=F",
    "比特币 (BTC-USD)": "BTC-USD",
    "欧元美元 (EURUSD=X)": "EURUSD=X",
    "英镑美元 (GBPUSD=X)": "GBPUSD=X",
    "美元日元 (USDJPY=X)": "USDJPY=X",
    "苹果 (AAPL)": "AAPL",
    "特斯拉 (TSLA)": "TSLA",
    "纳斯达克100 (QQQ)": "QQQ"
}

selected_name = st.sidebar.selectbox("选择品种", list(symbol_options.keys()))
symbol = symbol_options[selected_name]

period = st.sidebar.selectbox("历史长度", ["5d", "1mo", "3mo"], index=1)

timeframes = {
    "5分钟": "5m",
    "15分钟": "15m",
    "30分钟": "30m",
    "1小时": "1h",
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
            
            # 计算指标
            ma20 = close.rolling(20).mean()
            rsi_value = None
            if len(close) >= 15:
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_value = float(rsi.iloc[-1])

            # 信号判断
            signal = "观望"
            if len(close) >= 20:
                ma20_val = float(ma20.iloc[-1])
                if last_close > ma20_val:
                    signal = "偏多"
                    bull_count += 1
                else:
                    signal = "偏空"
                    bear_count += 1

            st.subheader(f"{selected_name} · {name}")
            st.caption(f"最新时间：{df.index[-1]}")
            st.metric("最新价格", f"{last_close:.2f}")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**信号**：{signal}")
            with col2:
                if rsi_value is not None:
                    st.write(f"**RSI(14)**：{rsi_value:.1f}")

            st.line_chart(close)

        except Exception as e:
            st.error(f"{name} 出错：{e}")

# 多周期共振汇总
st.divider()
st.subheader("多周期共振汇总")
st.write(f"看多周期数量：{bull_count}")
st.write(f"看空周期数量：{bear_count}")

if bull_count >= 4:
    st.success("当前多周期共振偏多")
elif bear_count >= 4:
    st.error("当前多周期共振偏空")
else:
    st.info("目前多周期信号分歧，建议观望")

st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 纯免费数据")
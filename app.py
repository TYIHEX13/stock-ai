import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="多品种多周期分析", layout="wide")
st.title("多品种多时间周期分析")

# 品种选择
symbol_options = {
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
    "1天": "1d",
    "1周": "1wk"
}

bull_count = 0
bear_count = 0
signals = {}

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
            ma60 = close.rolling(60).mean() if len(close) >= 60 else None
            
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

            signals[name] = signal

            # 简单趋势/震荡判断
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

            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**信号**：{signal}")
            with col2:
                if rsi_value is not None:
                    st.write(f"**RSI**：{rsi_value:.1f}")
            with col3:
                st.write(f"**趋势**：{trend}")

            st.line_chart(close)

        except Exception as e:
            st.error(f"{name} 出错：{e}")

# 多周期共振汇总（放在显眼位置）
st.divider()
st.subheader("多周期共振汇总")

col_a, col_b = st.columns(2)
with col_a:
    st.metric("看多周期数", bull_count)
with col_b:
    st.metric("看空周期数", bear_count)

if bull_count >= 4:
    st.success("强共振偏多 → 可关注做多机会")
elif bear_count >= 4:
    st.error("强共振偏空 → 可关注做空机会")
elif bull_count >= 3:
    st.info("偏多共振，谨慎看多")
elif bear_count >= 3:
    st.info("偏空共振，谨慎看空")
else:
    st.warning("多周期信号分歧，建议观望")

st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 免费数据，价格仅供参考")
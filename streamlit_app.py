"""Interactive Streamlit entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gas_monitor.data import generate_synthetic_data  # noqa: E402
from gas_monitor.detector import detect_anomalies  # noqa: E402


st.set_page_config(
    page_title="天然气管道运行健康监测",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def load_demo_data(n_hours: int, anomaly_ratio: float) -> pd.DataFrame:
    return generate_synthetic_data(
        n_hours=n_hours,
        anomaly_ratio=anomaly_ratio,
        seed=42,
    )


def pressure_chart(data: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["inlet_pressure"],
            name="入口压力",
            mode="lines",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["outlet_pressure"],
            name="出口压力",
            mode="lines",
        )
    )
    abnormal = data[data["is_anomaly"] == 1]
    figure.add_trace(
        go.Scatter(
            x=abnormal["timestamp"],
            y=abnormal["outlet_pressure"],
            name="模型异常点",
            mode="markers",
            marker={"color": "#d62728", "size": 9, "symbol": "x"},
        )
    )
    figure.update_layout(
        xaxis_title="时间",
        yaxis_title="压力 / MPa",
        legend_title="变量",
        hovermode="x unified",
    )
    return figure


st.title("天然气管道运行健康监测")
st.caption("基于时序特征与 Isolation Forest 的轻量级异常检测演示")

with st.sidebar:
    st.header("分析参数")
    source = st.radio("数据来源", ["内置合成数据", "上传 CSV"])
    contamination = st.slider("预计异常比例", 0.01, 0.10, 0.03, 0.01)
    rolling_window = st.slider("滚动窗口 / 小时", 4, 48, 12, 2)

if source == "内置合成数据":
    with st.sidebar:
        days = st.slider("模拟天数", 3, 30, 14)
    raw_data = load_demo_data(days * 24, contamination)
else:
    uploaded_file = st.sidebar.file_uploader("上传管道遥测 CSV", type=["csv"])
    if uploaded_file is None:
        st.info("请上传 CSV，或切换到“内置合成数据”直接体验。")
        st.stop()
    raw_data = pd.read_csv(uploaded_file)

try:
    scored, _, metrics = detect_anomalies(
        raw_data,
        contamination=contamination,
        rolling_window=rolling_window,
    )
except ValueError as error:
    st.error(f"数据校验失败：{error}")
    st.stop()

component_options = sorted(scored["component_id"].unique())
selected_component = st.sidebar.selectbox("选择管段", component_options)
view = scored[scored["component_id"] == selected_component].copy()

metric_columns = st.columns(4)
metric_columns[0].metric("记录数", f"{len(view):,}")
metric_columns[1].metric("模型异常点", int(view["is_anomaly"].sum()))
metric_columns[2].metric("平均压降", f"{view['pressure_drop'].mean():.3f} MPa")
metric_columns[3].metric("最高风险分数", f"{view['risk_score'].max():.1f}")

if metrics is not None:
    with st.expander("合成数据离线评估", expanded=True):
        evaluation_columns = st.columns(3)
        evaluation_columns[0].metric("Precision", f"{metrics.precision:.3f}")
        evaluation_columns[1].metric("Recall", f"{metrics.recall:.3f}")
        evaluation_columns[2].metric("F1", f"{metrics.f1:.3f}")
        st.caption("这些指标只用于验证合成数据中的注入异常，不代表真实现场效果。")

pressure_tab, flow_tab, risk_tab, data_tab = st.tabs(
    ["压力趋势", "流量与温度", "风险分析", "数据明细"]
)

with pressure_tab:
    st.plotly_chart(pressure_chart(view), use_container_width=True)

with flow_tab:
    flow_figure = px.line(
        view,
        x="timestamp",
        y=["flow_rate", "temperature"],
        labels={"value": "数值", "timestamp": "时间", "variable": "变量"},
    )
    st.plotly_chart(flow_figure, use_container_width=True)

with risk_tab:
    risk_figure = px.line(
        view,
        x="timestamp",
        y="risk_score",
        color_discrete_sequence=["#d62728"],
        labels={"risk_score": "风险分数", "timestamp": "时间"},
    )
    st.plotly_chart(risk_figure, use_container_width=True)
    st.dataframe(
        view.nlargest(10, "risk_score")[
            [
                "timestamp",
                "component_id",
                "inlet_pressure",
                "outlet_pressure",
                "flow_rate",
                "pressure_drop",
                "risk_score",
                "is_anomaly",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with data_tab:
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button(
        "下载完整检测结果",
        data=scored.to_csv(index=False).encode("utf-8-sig"),
        file_name="pipeline_anomaly_results.csv",
        mime="text/csv",
    )

st.warning(
    "本项目用于学习与算法原型验证。模型异常点必须结合工艺阈值、检修记录和人工复核，"
    "不能直接作为安全生产决策。"
)


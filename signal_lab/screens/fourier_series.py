import numpy as np
import streamlit as st

from signal_lab.core.fourier_series import (
    harmonic_components,
    synthesize_series,
)
from signal_lab.visualization.animation import render_animation_controls
from signal_lab.visualization.plots import create_series_figure


def render() -> None:
    st.title("傅里叶级数合成")
    st.write("逐项增加谐波，观察周期信号如何由有限项正弦级数逼近。")

    series_name = st.selectbox("目标信号", ("方波", "三角波"))
    series_type = "square" if series_name == "方波" else "triangle"
    columns = st.columns(3)
    with columns[0]:
        amplitude = st.slider("目标峰值幅度", 0.2, 3.0, 1.0, 0.1)
    with columns[1]:
        fundamental_frequency = st.slider("基波频率 (Hz)", 1, 20, 2)
    with columns[2]:
        max_harmonic = st.slider("最高谐波次数", 1, 51, 15, 2)

    time = np.linspace(0, 2 / fundamental_frequency, 1600, endpoint=False)
    phase = 2 * np.pi * fundamental_frequency * time
    if series_type == "square":
        reference = amplitude * np.sign(np.sin(phase))
    else:
        reference = amplitude * (2 / np.pi) * np.arcsin(np.sin(phase))

    def render_frame(frame_index: int) -> None:
        harmonic_count = frame_index + 1
        approximation = synthesize_series(
            time,
            series_type,
            fundamental_frequency,
            harmonic_count,
            amplitude,
        )
        orders, _, coefficients = harmonic_components(
            series_type,
            fundamental_frequency,
            harmonic_count,
            amplitude,
        )
        st.pyplot(
            create_series_figure(
                time,
                approximation,
                orders,
                np.abs(coefficients),
                signal_name=series_name,
                harmonic_count=harmonic_count,
                reference=reference,
            ),
            width="stretch",
        )
        st.metric("当前谐波上限", harmonic_count)

    render_animation_controls(max_harmonic, "fourier_series", render_frame)
    st.info(
        "方波理想频谱只包含奇次谐波，幅度按 1/n 衰减；"
        "三角波奇次谐波按 1/n² 衰减。增加项数后，方波跳变附近仍会出现吉布斯过冲。"
    )

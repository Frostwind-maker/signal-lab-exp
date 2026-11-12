import numpy as np
import streamlit as st

from signal_lab.core.filters import FilterType, apply_fir_filter, design_fir_filter
from signal_lab.core.spectrum import compute_amplitude_spectrum
from signal_lab.visualization.plots import create_filter_comparison_figure


def render() -> None:
    st.title("拓展：滤波前后对比")
    st.write("对含有多个频率成分的信号进行 FIR 滤波，观察前后波形和频谱。")

    sampling_rate = 1000
    duration = 2.0
    filter_type = st.selectbox("滤波器", ("低通", "高通", "带通", "带阻"))
    columns = st.columns(2)
    with columns[0]:
        cutoff_low = st.slider("截止频率 / 下限 (Hz)", 10, 450, 120, 5)
    with columns[1]:
        cutoff_high = st.slider("上限频率 (Hz)", 20, 490, 260, 5)
    tap_count = st.select_slider(
        "FIR 阶数（奇数抽头）",
        options=(31, 51, 101, 151),
        value=101,
    )

    if filter_type in ("带通", "带阻") and cutoff_high <= cutoff_low:
        st.error("带通/带阻的上限频率必须大于下限频率。")
        return

    time = np.arange(int(sampling_rate * duration)) / sampling_rate
    generator = np.random.default_rng(42)
    original = (
        np.sin(2 * np.pi * 35 * time)
        + 0.7 * np.sin(2 * np.pi * 180 * time)
        + 0.4 * np.sin(2 * np.pi * 330 * time)
        + 0.12 * generator.normal(size=time.size)
    )
    coefficients = design_fir_filter(
        filter_type,
        sampling_rate,
        cutoff_low,
        cutoff_high if filter_type in ("带通", "带阻") else None,
        int(tap_count),
    )
    filtered = apply_fir_filter(original, coefficients)
    fft_points = 2048
    frequencies, original_magnitude = compute_amplitude_spectrum(
        original,
        sampling_rate,
        fft_points,
        "汉宁窗",
    )
    _, filtered_magnitude = compute_amplitude_spectrum(
        filtered,
        sampling_rate,
        fft_points,
        "汉宁窗",
    )
    st.pyplot(
        create_filter_comparison_figure(
            time,
            original,
            filtered,
            frequencies,
            original_magnitude,
            filtered_magnitude,
            filter_type=filter_type,
            cutoff_low=cutoff_low,
            cutoff_high=cutoff_high
            if filter_type in ("带通", "带阻")
            else None,
        ),
        width="stretch",
    )
    st.caption(
        f"窗函数法 FIR 滤波器，{tap_count} 个抽头。"
        "增加阶数通常能使过渡带更窄，但会增加运算量和边界瞬态。"
    )

import numpy as np
import streamlit as st

from signal_lab.core.spectrum import compute_amplitude_phase_spectrum
from signal_lab.visualization.plots import create_spectral_comparison_figure


def render() -> None:
    st.title("拓展：相位谱与窗函数")
    st.write("观察相位谱，并比较不同窗函数对有限长度信号频谱的影响。")

    columns = st.columns(3)
    with columns[0]:
        sampling_rate = st.selectbox("采样率 (Hz)", (512, 1024, 2048), index=1)
    with columns[1]:
        duration = st.slider("记录时长 (s)", 0.25, 2.0, 1.0, 0.25)
    with columns[2]:
        fft_points = st.selectbox("FFT 点数", (512, 1024, 2048, 4096), index=1)

    frequency = st.slider(
        "信号频率 (Hz)",
        1.0,
        float(sampling_rate / 2 - 1),
        37.5,
        0.5,
    )
    phase_degrees = st.slider("相位 (°)", -180, 180, 35, 1)
    windows = st.multiselect(
        "对比窗函数",
        ("矩形窗", "汉宁窗", "汉明窗"),
        default=["矩形窗", "汉宁窗", "汉明窗"],
    )
    if not windows:
        st.warning("请至少选择一种窗函数。")
        return

    sample_count = int(round(sampling_rate * duration))
    time = np.arange(sample_count) / sampling_rate
    samples = np.sin(
        2 * np.pi * frequency * time + np.deg2rad(phase_degrees)
    )
    spectra = {
        window_name: compute_amplitude_phase_spectrum(
            samples,
            sampling_rate,
            int(fft_points),
            window_name,
        )
        for window_name in windows
    }

    st.pyplot(
        create_spectral_comparison_figure(time, samples, spectra),
        width="stretch",
    )
    st.info(
        "非整周期截断会造成频谱泄漏。汉宁/汉明窗通常降低旁瓣，但会加宽主瓣；"
        "相位仅在幅度足够大的频率点上有意义。"
    )

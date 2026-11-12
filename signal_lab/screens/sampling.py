import numpy as np
import streamlit as st

from signal_lab.core.sampling import (
    alias_frequency,
    is_aliased,
    sample_signal,
)
from signal_lab.core.spectrum import compute_amplitude_spectrum
from signal_lab.visualization.plots import create_sampling_figure


def render() -> None:
    st.title("采样与混叠")
    st.write("改变采样率，比较连续信号和离散采样序列的频谱。")

    columns = st.columns(3)
    with columns[0]:
        first_frequency = st.slider("低频分量 (Hz)", 5, 80, 18)
    with columns[1]:
        second_frequency = st.slider("高频分量 (Hz)", 20, 200, 65)
    with columns[2]:
        sampling_rate = st.slider("采样率 fs (Hz)", 20, 500, 100, 5)

    if second_frequency <= first_frequency:
        st.error("高频分量必须大于低频分量。")
        return

    duration = 1.0
    reference_rate = 4000
    continuous_time = np.arange(int(reference_rate * duration)) / reference_rate
    continuous_samples = (
        np.sin(2 * np.pi * first_frequency * continuous_time)
        + 0.7 * np.sin(2 * np.pi * second_frequency * continuous_time)
    )
    sample_times, sample_values = sample_signal(
        continuous_time,
        continuous_samples,
        sampling_rate,
        duration,
    )
    fft_points = 4096
    original_frequencies, original_magnitude = compute_amplitude_spectrum(
        continuous_samples,
        reference_rate,
        fft_points,
    )
    frequencies, sampled_magnitude = compute_amplitude_spectrum(
        sample_values,
        sampling_rate,
        fft_points,
    )
    display_original = np.interp(frequencies, original_frequencies, original_magnitude)

    maximum_frequency = float(second_frequency)
    aliasing = is_aliased(maximum_frequency, sampling_rate)
    folded_frequency = alias_frequency(maximum_frequency, sampling_rate)
    status_columns = st.columns(4)
    status_columns[0].metric("信号最高频率", f"{maximum_frequency} Hz")
    status_columns[1].metric("当前采样率", f"{sampling_rate} Hz")
    status_columns[2].metric("奈奎斯特频率", f"{sampling_rate / 2:g} Hz")
    status_columns[3].metric("高频分量折叠频率", f"{folded_frequency:g} Hz")

    if aliasing:
        st.error("发生混叠：采样率不满足最高信号频率的奈奎斯特采样条件。")
    else:
        st.success("当前设置满足奈奎斯特采样条件。")

    st.pyplot(
        create_sampling_figure(
            continuous_time,
            continuous_samples,
            sample_times,
            sample_values,
            frequencies,
            display_original,
            sampled_magnitude,
            sampling_rate=sampling_rate,
            maximum_frequency=maximum_frequency,
            aliasing=aliasing,
            alias_frequency=folded_frequency,
        ),
        width="stretch",
    )
    st.caption(
        "采样频谱以离散序列的采样率建立频率轴；原始谱超出显示奈奎斯特区间的分量会被截去，"
        "其能量则在采样后折叠到区间内。"
    )

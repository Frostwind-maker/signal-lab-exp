import numpy as np
import streamlit as st

from signal_lab.core.time_frequency import compute_stft
from signal_lab.visualization.animation import render_animation_player
from signal_lab.visualization.plots import build_stft_animation


def render() -> None:
    st.title("短时傅里叶变换")
    st.write("用滑动时间窗分析线性调频信号，观察频率随时间的变化。")

    sampling_rate = 1000
    duration = 2.0
    columns = st.columns(3)
    with columns[0]:
        start_frequency = st.slider("起始频率 (Hz)", 2, 100, 10)
    with columns[1]:
        end_frequency = st.slider("结束频率 (Hz)", 20, 400, 180)
    with columns[2]:
        window_ms = st.slider("窗长 (ms)", 32, 500, 128, 16)

    if end_frequency <= start_frequency:
        st.error("结束频率必须大于起始频率。")
        return

    samples_count = int(sampling_rate * duration)
    time = np.arange(samples_count) / sampling_rate
    chirp_rate = (end_frequency - start_frequency) / duration
    samples = np.sin(
        2 * np.pi * (start_frequency * time + 0.5 * chirp_rate * time**2)
    )

    window_length = max(32, round(window_ms * sampling_rate / 1000))
    hop_length = max(1, window_length // 8)
    fft_points = 1 << (window_length - 1).bit_length()
    window_name = st.selectbox("分析窗", ("汉宁窗", "汉明窗", "矩形窗"))
    frame_times, frequencies, magnitude = compute_stft(
        samples,
        sampling_rate,
        window_length,
        hop_length,
        fft_points,
        window_name,
    )
    figure = build_stft_animation(
        time,
        samples,
        frame_times,
        frequencies,
        magnitude,
        window_length=window_length,
        sampling_rate=sampling_rate,
    )
    render_animation_player(figure, "stft_animation")
    metrics = st.columns(2)
    metrics[0].metric("窗长", f"{window_length / sampling_rate * 1000:.0f} ms")
    metrics[1].metric("FFT 频率栅格间隔", f"{sampling_rate / fft_points:.2f} Hz")
    st.info(
        "缩短窗长可提高时间定位能力，但频率分辨能力下降；"
        "增加 FFT 补零只让图像栅格更密，不会恢复窗长带来的真实频率分辨率损失。"
    )

import numpy as np
import streamlit as st

from signal_lab.core.signals import SignalType, generate_signal
from signal_lab.core.spectrum import compute_amplitude_spectrum
from signal_lab.visualization.animation import render_animation_player
from signal_lab.visualization.plots import build_time_frequency_animation


SIGNAL_NAMES: dict[str, SignalType] = {
    "正弦波": "sine",
    "方波": "square",
    "三角波": "triangle",
    "矩形脉冲": "pulse",
    "指数衰减": "exponential",
}

SIGNAL_EXPLANATIONS = {
    "正弦波": "理想正弦波的频谱集中在基频；有限时长截取和加窗会影响谱线外观。",
    "方波": "周期方波包含基波和奇次谐波；占空比变化会改变谐波幅值。",
    "三角波": "对称三角波主要包含奇次谐波，谐波幅值比方波衰减更快。",
    "矩形脉冲": "单个矩形脉冲的频谱具有 sinc 形状；脉宽越窄，频谱主瓣越宽。",
    "指数衰减": "指数衰减信号的能量集中在起始时刻，频谱呈连续展宽的形态。",
}


def render() -> None:
    st.title("时域与频域")
    st.write("调整信号参数，观察时域波形与幅度频谱同步更新。")

    signal_name = st.selectbox("信号类型", tuple(SIGNAL_NAMES))
    sampling_rate = st.select_slider(
        "采样率 (Hz)",
        options=[500, 1000, 2000, 4000, 8000],
        value=2000,
    )
    duration = st.slider("显示时长 (s)", 0.25, 2.0, 1.0, 0.25)

    parameter_columns = st.columns(3)
    with parameter_columns[0]:
        amplitude = st.slider("幅值", 0.1, 5.0, 1.0, 0.1)
    with parameter_columns[1]:
        if signal_name in ("正弦波", "方波", "三角波"):
            frequency = st.slider(
                "频率 (Hz)",
                min_value=0.5,
                max_value=float(max(0.5, sampling_rate * 0.45)),
                value=float(min(5, sampling_rate * 0.45)),
                step=0.5,
                key=f"signal_frequency_{sampling_rate}",
            )
        else:
            frequency = 5.0
            st.caption("此信号不使用周期频率参数")
    with parameter_columns[2]:
        if signal_name in ("正弦波", "方波", "三角波"):
            phase_degrees = st.slider("相位 (°)", -180, 180, 0, 1)
        else:
            phase_degrees = 0
            st.caption("此信号不使用相位参数")

    extra_columns = st.columns(3)
    with extra_columns[0]:
        duty_cycle = 0.5
        if signal_name == "方波":
            duty_cycle = st.slider("占空比 (%)", 5, 95, 50, 1) / 100
    with extra_columns[1]:
        pulse_width = min(0.1, duration)
        if signal_name == "矩形脉冲":
            pulse_width = st.slider(
                "脉宽 (s)",
                min_value=0.01,
                max_value=float(duration),
                value=float(min(0.1, duration)),
                step=0.01,
                key=f"pulse_width_{duration}",
            )
    with extra_columns[2]:
        decay_rate = 2.0
        if signal_name == "指数衰减":
            decay_rate = st.slider("衰减系数 a (1/s)", 0.1, 10.0, 2.0, 0.1)

    analysis_columns = st.columns(2)
    with analysis_columns[0]:
        fft_points = st.select_slider(
            "FFT 点数",
            options=[256, 512, 1024, 2048, 4096],
            value=1024,
        )
    with analysis_columns[1]:
        window_name = st.selectbox("窗函数", ("矩形窗", "汉宁窗", "汉明窗"))

    sample_count = int(round(sampling_rate * duration))
    full_time = np.arange(sample_count, dtype=float) / sampling_rate
    initial_samples = generate_signal(
        SIGNAL_NAMES[signal_name],
        full_time,
        amplitude=amplitude,
        frequency=frequency,
        phase_degrees=phase_degrees,
        duty_cycle=duty_cycle,
        pulse_width=pulse_width,
        decay_rate=decay_rate,
    )
    frequencies, initial_magnitude = compute_amplitude_spectrum(
        initial_samples,
        sampling_rate,
        int(fft_points),
        window_name,
    )

    frame_count = 60
    display_step = max(1, int(np.ceil(sample_count / 1200)))
    time = full_time[::display_step]
    wave_frames = np.stack(
        [
            generate_signal(
                SIGNAL_NAMES[signal_name],
                time,
                amplitude=amplitude,
                frequency=frequency,
                phase_degrees=phase_degrees,
                duty_cycle=duty_cycle,
                pulse_width=pulse_width,
                decay_rate=decay_rate,
                time_offset=frame_index * 0.05,
            )
            for frame_index in range(frame_count)
        ]
    )
    frequency_step = max(1, int(np.ceil(frequencies.size / 512)))
    display_frequencies = frequencies[::frequency_step]
    initial_magnitude = initial_magnitude[::frequency_step]
    freq_frames = np.broadcast_to(
        initial_magnitude,
        (frame_count, initial_magnitude.size),
    )
    figure = build_time_frequency_animation(
        time,
        wave_frames,
        freq_frames,
        display_frequencies,
        sampling_rate=sampling_rate,
        fft_points=int(fft_points),
        window_name=window_name,
    )
    render_animation_player(figure, "time_frequency_animation")
    st.info(SIGNAL_EXPLANATIONS[signal_name])
    st.caption(
        f"采样点数：{sample_count} | 动画帧数：{frame_count} | "
        f"频率栅格间隔：{sampling_rate / int(fft_points):.3g} Hz。"
        "动画在浏览器端播放，横轴固定；FFT 仅按当前参数计算一次。"
    )

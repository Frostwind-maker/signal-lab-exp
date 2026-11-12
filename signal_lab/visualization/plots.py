"""时域、频域及时频域图表组件。"""

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def create_time_frequency_figure(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    magnitude: NDArray[np.float64],
    *,
    signal_name: str,
    sampling_rate: float,
    fft_points: int,
    window_name: str,
) -> plt.Figure:
    figure, (time_axis, frequency_axis) = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        gridspec_kw={"height_ratios": [1.1, 1]},
    )

    time_axis.plot(time, samples, color="#1769aa", linewidth=1.4)
    time_axis.set_title(f"{signal_name}：时域波形")
    time_axis.set_xlabel("时间 (s)")
    time_axis.set_ylabel("幅值")
    time_axis.grid(True, alpha=0.3)
    time_axis.margins(x=0.01)

    frequency_axis.plot(frequencies, magnitude, color="#d1495b", linewidth=1.3)
    frequency_axis.set_title(f"单边幅度谱（{window_name}）")
    frequency_axis.set_xlabel("频率 (Hz)")
    frequency_axis.set_ylabel("幅度")
    frequency_axis.set_xlim(0, sampling_rate / 2)
    frequency_axis.grid(True, alpha=0.3)

    figure.suptitle(
        f"采样率 {sampling_rate:g} Hz | FFT 点数 {fft_points} | "
        f"FFT 频率栅格间隔 {sampling_rate / fft_points:.3g} Hz",
        fontsize=10,
    )
    figure.tight_layout()
    return figure


def create_series_figure(
    time: NDArray[np.float64],
    approximation: NDArray[np.float64],
    harmonic_orders: NDArray[np.int64],
    harmonic_amplitudes: NDArray[np.float64],
    *,
    signal_name: str,
    harmonic_count: int,
    reference: NDArray[np.float64],
) -> plt.Figure:
    figure, (wave_axis, spectrum_axis) = plt.subplots(2, 1, figsize=(10, 7))
    wave_axis.plot(time, reference, color="#999999", linewidth=1, label="目标波形")
    wave_axis.plot(
        time,
        approximation,
        color="#1769aa",
        linewidth=1.5,
        label=f"前 {harmonic_count} 次谐波合成",
    )
    wave_axis.set_title(f"{signal_name}傅里叶级数合成")
    wave_axis.set_xlabel("时间 (s)")
    wave_axis.set_ylabel("幅值")
    wave_axis.grid(True, alpha=0.3)
    wave_axis.legend()

    spectrum_axis.stem(harmonic_orders, harmonic_amplitudes, basefmt=" ")
    spectrum_axis.set_title("当前合成所包含的谐波")
    spectrum_axis.set_xlabel("谐波序号")
    spectrum_axis.set_ylabel("峰值幅度")
    spectrum_axis.grid(True, alpha=0.3)
    figure.tight_layout()
    return figure


def create_stft_figure(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    frame_times: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    magnitude: NDArray[np.float64],
    *,
    window_length: int,
    sampling_rate: float,
    current_frame: int,
) -> plt.Figure:
    figure, (wave_axis, spectrum_axis) = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        gridspec_kw={"height_ratios": [1, 1.5]},
    )
    wave_axis.plot(time, samples, linewidth=1, color="#1769aa")
    selected_time = frame_times[current_frame]
    half_window = window_length / (2 * sampling_rate)
    wave_axis.axvspan(
        max(0, selected_time - half_window),
        min(time[-1], selected_time + half_window),
        alpha=0.2,
        color="#f4a261",
        label="当前分析窗",
    )
    wave_axis.set_title("线性调频信号与滑动分析窗")
    wave_axis.set_xlabel("时间 (s)")
    wave_axis.set_ylabel("幅值")
    wave_axis.grid(True, alpha=0.3)
    wave_axis.legend()

    mesh = spectrum_axis.pcolormesh(
        frame_times,
        frequencies,
        20 * np.log10(np.maximum(magnitude.T, 1e-8)),
        shading="auto",
        cmap="magma",
    )
    spectrum_axis.axvline(selected_time, color="cyan", linestyle="--")
    spectrum_axis.set_title("STFT 时频图（相对幅度 dB）")
    spectrum_axis.set_xlabel("时间 (s)")
    spectrum_axis.set_ylabel("频率 (Hz)")
    figure.colorbar(mesh, ax=spectrum_axis, label="幅度 (dB)")
    figure.tight_layout()
    return figure


def create_sampling_figure(
    continuous_time: NDArray[np.float64],
    continuous_samples: NDArray[np.float64],
    sample_times: NDArray[np.float64],
    sample_values: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    original_magnitude: NDArray[np.float64],
    sampled_magnitude: NDArray[np.float64],
    *,
    sampling_rate: float,
    maximum_frequency: float,
    aliasing: bool,
    alias_frequency: float,
) -> plt.Figure:
    figure, (time_axis, frequency_axis) = plt.subplots(2, 1, figsize=(10, 7))
    time_axis.plot(
        continuous_time,
        continuous_samples,
        color="#1769aa",
        linewidth=1.2,
        label="连续参考信号",
    )
    markerline, stemlines, _ = time_axis.stem(
        sample_times,
        sample_values,
        linefmt="r-",
        markerfmt="ro",
        basefmt=" ",
        label="离散采样点",
    )
    markerline.set_color("#d1495b")
    stemlines.set_color("#d1495b")
    time_axis.set_title("连续信号与离散采样")
    time_axis.set_xlabel("时间 (s)")
    time_axis.set_ylabel("幅值")
    time_axis.grid(True, alpha=0.3)
    time_axis.legend()

    frequency_axis.plot(
        frequencies,
        original_magnitude,
        label="原信号频谱",
        linewidth=1.2,
    )
    frequency_axis.plot(
        frequencies,
        sampled_magnitude,
        label="采样序列频谱",
        linewidth=1.2,
    )
    frequency_axis.axvline(
        sampling_rate / 2,
        color="#d1495b",
        linestyle="--",
        label="奈奎斯特频率",
    )
    frequency_axis.set_xlim(0, frequencies[-1])
    frequency_axis.set_title("频谱对比")
    frequency_axis.set_xlabel("频率 (Hz)")
    frequency_axis.set_ylabel("归一化幅度")
    frequency_axis.grid(True, alpha=0.3)
    frequency_axis.legend()
    status = (
        f"发生混叠：最高频率 {maximum_frequency:g} Hz，折叠至 "
        f"{alias_frequency:g} Hz"
        if aliasing
        else f"未发生混叠：最高频率 {maximum_frequency:g} Hz"
    )
    figure.suptitle(status)
    figure.tight_layout()
    return figure


def create_spectral_comparison_figure(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    spectra: dict[str, tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]],
) -> plt.Figure:
    figure, axes = plt.subplots(3, 1, figsize=(10, 9))
    axes[0].plot(time, samples, color="#1769aa", linewidth=1)
    axes[0].set_title("时域信号")
    axes[0].set_xlabel("时间 (s)")
    axes[0].set_ylabel("幅值")
    axes[0].grid(True, alpha=0.3)

    for window_name, (frequencies, magnitude, phase) in spectra.items():
        axes[1].plot(frequencies, magnitude, label=window_name, linewidth=1.1)
        unwrapped_phase = np.unwrap(np.nan_to_num(phase))
        unwrapped_phase[np.isnan(phase)] = np.nan
        axes[2].plot(
            frequencies,
            np.rad2deg(unwrapped_phase),
            label=window_name,
            linewidth=1,
        )

    axes[1].set_title("窗函数对幅度谱的影响")
    axes[1].set_xlabel("频率 (Hz)")
    axes[1].set_ylabel("幅度")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    axes[2].set_title("相位谱（度）")
    axes[2].set_xlabel("频率 (Hz)")
    axes[2].set_ylabel("相位 (°)")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()
    figure.tight_layout()
    return figure


def create_filter_comparison_figure(
    time: NDArray[np.float64],
    original: NDArray[np.float64],
    filtered: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    original_magnitude: NDArray[np.float64],
    filtered_magnitude: NDArray[np.float64],
    *,
    filter_type: str,
    cutoff_low: float,
    cutoff_high: float | None = None,
) -> plt.Figure:
    figure, (time_axis, frequency_axis) = plt.subplots(2, 1, figsize=(10, 7))
    time_axis.plot(time, original, label="滤波前", alpha=0.65, linewidth=1)
    time_axis.plot(time, filtered, label="滤波后", linewidth=1.2)
    time_axis.set_title(f"{filter_type}滤波：时域对比")
    time_axis.set_xlabel("时间 (s)")
    time_axis.set_ylabel("幅值")
    time_axis.grid(True, alpha=0.3)
    time_axis.legend()

    frequency_axis.plot(frequencies, original_magnitude, label="滤波前")
    frequency_axis.plot(frequencies, filtered_magnitude, label="滤波后")
    frequency_axis.axvline(cutoff_low, color="#555555", linestyle="--")
    if cutoff_high is not None:
        frequency_axis.axvline(cutoff_high, color="#555555", linestyle="--")
    frequency_axis.set_title("幅度频谱对比")
    frequency_axis.set_xlabel("频率 (Hz)")
    frequency_axis.set_ylabel("幅度")
    frequency_axis.grid(True, alpha=0.3)
    frequency_axis.legend()
    figure.tight_layout()
    return figure


def create_audio_analysis_figure(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    frame_times: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    magnitude: NDArray[np.float64],
    current_frame: int,
    sampling_rate: float,
) -> plt.Figure:
    figure, (wave_axis, spectrum_axis) = plt.subplots(2, 1, figsize=(10, 7))
    wave_axis.plot(time, samples, linewidth=0.8, color="#1769aa")
    wave_axis.axvline(
        frame_times[current_frame],
        color="#d1495b",
        linestyle="--",
        label="当前分析帧",
    )
    wave_axis.set_title("音频波形与播放位置")
    wave_axis.set_xlabel("时间 (s)")
    wave_axis.set_ylabel("幅值")
    wave_axis.grid(True, alpha=0.3)
    wave_axis.legend()

    spectrum_axis.plot(frequencies, magnitude[current_frame], color="#d1495b")
    spectrum_axis.set_xlim(0, sampling_rate / 2)
    spectrum_axis.set_title(f"第 {current_frame + 1} 帧的幅度谱")
    spectrum_axis.set_xlabel("频率 (Hz)")
    spectrum_axis.set_ylabel("幅度")
    spectrum_axis.grid(True, alpha=0.3)
    figure.tight_layout()
    return figure


def create_live_audio_figure(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    magnitude: NDArray[np.float64],
) -> plt.Figure:
    figure, (wave_axis, spectrum_axis) = plt.subplots(2, 1, figsize=(10, 6))
    wave_axis.plot(time, samples, color="#1769aa", linewidth=0.9)
    wave_axis.set_title("最近 1 秒麦克风波形")
    wave_axis.set_xlabel("时间 (s)")
    wave_axis.set_ylabel("幅值")
    wave_axis.grid(True, alpha=0.3)

    spectrum_axis.plot(frequencies, magnitude, color="#d1495b", linewidth=1)
    spectrum_axis.set_xlim(0, frequencies[-1])
    spectrum_axis.set_title("实时单边幅度谱")
    spectrum_axis.set_xlabel("频率 (Hz)")
    spectrum_axis.set_ylabel("幅度")
    spectrum_axis.grid(True, alpha=0.3)
    figure.tight_layout()
    return figure

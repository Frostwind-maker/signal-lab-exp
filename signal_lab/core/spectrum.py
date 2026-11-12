"""FFT 幅度谱分析。"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray


WindowName = Literal["矩形窗", "汉宁窗", "汉明窗"]


def compute_amplitude_spectrum(
    samples: NDArray[np.float64],
    sampling_rate: float,
    fft_points: int,
    window_name: WindowName = "矩形窗",
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """计算经过单边幅值校正的频率轴与幅度谱。"""
    frequencies, magnitude, _ = compute_amplitude_phase_spectrum(
        samples,
        sampling_rate,
        fft_points,
        window_name,
    )
    return frequencies, magnitude


def compute_amplitude_phase_spectrum(
    samples: NDArray[np.float64],
    sampling_rate: float,
    fft_points: int,
    window_name: WindowName = "矩形窗",
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """计算单边幅度谱和相位谱。

    数据长度超过 FFT 点数时取前 fft_points 个采样点；不足时补零。
    补零只会让频率采样更密，不会增加真实频率分辨率。
    """
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("samples 必须是一维且非空的数组")
    if not np.all(np.isfinite(samples)):
        raise ValueError("samples 必须全部为有限值")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not isinstance(fft_points, int) or fft_points < 2:
        raise ValueError("fft_points 必须是大于等于 2 的整数")

    sample_count = min(samples.size, fft_points)
    segment = samples[:sample_count]
    if window_name == "矩形窗":
        window = np.ones(sample_count, dtype=float)
    elif window_name == "汉宁窗":
        window = np.hanning(sample_count)
    elif window_name == "汉明窗":
        window = np.hamming(sample_count)
    else:
        raise ValueError(f"不支持的窗函数：{window_name}")

    coherent_gain = window.sum()
    if coherent_gain <= 0:
        raise ValueError("窗函数增益为零，无法计算幅度谱")

    spectrum = np.fft.rfft(segment * window, n=fft_points)
    magnitude = np.abs(spectrum) / coherent_gain
    if fft_points % 2 == 0:
        magnitude[1:-1] *= 2
    else:
        magnitude[1:] *= 2

    frequencies = np.fft.rfftfreq(fft_points, d=1.0 / sampling_rate)
    phase = np.angle(spectrum)
    phase[magnitude <= np.max(magnitude) * 1e-8] = np.nan
    return frequencies, magnitude, phase

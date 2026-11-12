"""STFT 和时频分析。"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray


WindowName = Literal["矩形窗", "汉宁窗", "汉明窗"]


def compute_stft(
    samples: NDArray[np.float64],
    sampling_rate: float,
    window_length: int,
    hop_length: int,
    fft_points: int | None = None,
    window_name: WindowName = "汉宁窗",
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """计算居中补零、非中心补零的单边 STFT 幅值谱。"""
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 1 or samples.size == 0 or not np.all(np.isfinite(samples)):
        raise ValueError("samples 必须是一维、非空且全部有限的数组")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not isinstance(window_length, int) or window_length < 2:
        raise ValueError("window_length 必须是大于等于 2 的整数")
    if not isinstance(hop_length, int) or hop_length < 1:
        raise ValueError("hop_length 必须是正整数")
    if fft_points is None:
        fft_points = window_length
    if not isinstance(fft_points, int) or fft_points < window_length:
        raise ValueError("fft_points 必须大于等于 window_length")

    if window_name == "矩形窗":
        window = np.ones(window_length, dtype=float)
    elif window_name == "汉宁窗":
        window = np.hanning(window_length)
    elif window_name == "汉明窗":
        window = np.hamming(window_length)
    else:
        raise ValueError(f"不支持的窗函数：{window_name}")

    starts = np.arange(0, samples.size, hop_length, dtype=np.int64)
    frames = np.zeros((starts.size, window_length), dtype=float)
    for frame_index, start in enumerate(starts):
        segment = samples[start : start + window_length]
        frames[frame_index, : segment.size] = segment

    coherent_gain = window.sum()
    if coherent_gain <= 0:
        raise ValueError("窗函数增益为零，无法计算 STFT")
    transformed = np.fft.rfft(frames * window[None, :], n=fft_points, axis=1)
    magnitude = np.abs(transformed) / coherent_gain
    if fft_points % 2 == 0:
        magnitude[:, 1:-1] *= 2
    else:
        magnitude[:, 1:] *= 2

    frequencies = np.fft.rfftfreq(fft_points, d=1.0 / sampling_rate)
    valid_lengths = np.minimum(window_length, samples.size - starts)
    frame_times = (starts + (valid_lengths - 1) / 2) / sampling_rate
    return frame_times, frequencies, magnitude

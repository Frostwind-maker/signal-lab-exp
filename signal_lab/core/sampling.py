"""信号采样、奈奎斯特判定和混叠分析。"""

import numpy as np
from numpy.typing import NDArray


def sample_signal(
    continuous_time: NDArray[np.float64],
    continuous_samples: NDArray[np.float64],
    sampling_rate: float,
    duration: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """从高密度参考波形中按采样率取样。"""
    continuous_time = np.asarray(continuous_time, dtype=float)
    continuous_samples = np.asarray(continuous_samples, dtype=float)
    if (
        continuous_time.ndim != 1
        or continuous_samples.ndim != 1
        or continuous_time.size != continuous_samples.size
        or continuous_time.size < 2
    ):
        raise ValueError("参考时间和信号必须是一维、等长且至少含两个点")
    if not np.all(np.isfinite(continuous_time)) or not np.all(
        np.isfinite(continuous_samples)
    ):
        raise ValueError("参考信号必须全部为有限值")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration 必须为正")

    sample_times = np.arange(0, duration, 1.0 / sampling_rate)
    sample_values = np.interp(
        sample_times,
        continuous_time,
        continuous_samples,
        left=continuous_samples[0],
        right=continuous_samples[-1],
    )
    return sample_times, sample_values


def alias_frequency(frequency: float, sampling_rate: float) -> float:
    """返回折叠到第一奈奎斯特区间 [0, fs/2] 的混叠频率。"""
    if not np.isfinite(frequency) or frequency < 0:
        raise ValueError("frequency 必须为非负有限值")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    folded = frequency % sampling_rate
    return float(min(folded, sampling_rate - folded))


def is_aliased(maximum_frequency: float, sampling_rate: float) -> bool:
    if not np.isfinite(maximum_frequency) or maximum_frequency < 0:
        raise ValueError("maximum_frequency 必须为非负有限值")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    return maximum_frequency > sampling_rate / 2

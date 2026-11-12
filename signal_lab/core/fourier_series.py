"""方波和三角波的傅里叶级数系数与部分和。"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray


SeriesType = Literal["square", "triangle"]


def harmonic_components(
    series_type: SeriesType,
    fundamental_frequency: float,
    harmonic_count: int,
    amplitude: float = 1.0,
) -> tuple[NDArray[np.int64], NDArray[np.float64], NDArray[np.float64]]:
    """返回非零谐波序号、频率和峰值幅度。"""
    if not np.isfinite(fundamental_frequency) or fundamental_frequency <= 0:
        raise ValueError("fundamental_frequency 必须为正")
    if not isinstance(harmonic_count, int) or harmonic_count < 1:
        raise ValueError("harmonic_count 必须是正整数")
    if not np.isfinite(amplitude) or amplitude < 0:
        raise ValueError("amplitude 必须是非负有限值")
    if series_type not in ("square", "triangle"):
        raise ValueError(f"不支持的级数类型：{series_type}")

    orders = np.arange(1, harmonic_count + 1, dtype=np.int64)
    odd_mask = orders % 2 == 1
    orders = orders[odd_mask]
    if series_type == "square":
        coefficients = 4 * amplitude / (np.pi * orders)
    else:
        alternating_sign = (-1.0) ** ((orders - 1) // 2)
        coefficients = (
            8 * amplitude * alternating_sign / (np.pi**2 * orders**2)
        )
    return orders, orders * fundamental_frequency, coefficients


def synthesize_series(
    time: NDArray[np.float64],
    series_type: SeriesType,
    fundamental_frequency: float,
    harmonic_count: int,
    amplitude: float = 1.0,
    phase_degrees: float = 0.0,
) -> NDArray[np.float64]:
    """合成指定谐波上限的傅里叶级数部分和。"""
    time = np.asarray(time, dtype=float)
    if time.ndim != 1 or time.size == 0 or not np.all(np.isfinite(time)):
        raise ValueError("time 必须是一维、非空且全部有限的数组")
    if not np.isfinite(phase_degrees):
        raise ValueError("phase_degrees 必须为有限值")

    orders, frequencies, coefficients = harmonic_components(
        series_type,
        fundamental_frequency,
        harmonic_count,
        amplitude,
    )
    phase = np.deg2rad(phase_degrees)
    angles = 2 * np.pi * frequencies[:, None] * time[None, :] + phase
    return np.sum(coefficients[:, None] * np.sin(angles), axis=0)

"""基于窗函数法的 FIR 滤波器。"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray


FilterType = Literal["低通", "高通", "带通", "带阻"]


def design_fir_filter(
    filter_type: FilterType,
    sampling_rate: float,
    cutoff_low: float,
    cutoff_high: float | None = None,
    tap_count: int = 101,
) -> NDArray[np.float64]:
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not isinstance(tap_count, int) or tap_count < 3 or tap_count % 2 == 0:
        raise ValueError("tap_count 必须是大于等于 3 的奇数")

    nyquist = sampling_rate / 2
    if not np.isfinite(cutoff_low) or not 0 < cutoff_low < nyquist:
        raise ValueError("cutoff_low 必须位于 0 与奈奎斯特频率之间")
    if filter_type in ("带通", "带阻"):
        if (
            cutoff_high is None
            or not np.isfinite(cutoff_high)
            or not cutoff_low < cutoff_high < nyquist
        ):
            raise ValueError("带通/带阻要求 cutoff_low < cutoff_high < fs/2")
    elif filter_type not in ("低通", "高通"):
        raise ValueError(f"不支持的滤波器类型：{filter_type}")

    normalized_low = cutoff_low / nyquist
    lowpass = _lowpass_kernel(normalized_low, tap_count)
    if filter_type == "低通":
        coefficients = lowpass
    elif filter_type == "高通":
        coefficients = -lowpass
        coefficients[tap_count // 2] += 1
    else:
        normalized_high = cutoff_high / nyquist
        highpass = _lowpass_kernel(normalized_high, tap_count)
        bandpass = highpass - lowpass
        coefficients = bandpass if filter_type == "带通" else -bandpass
        if filter_type == "带阻":
            coefficients[tap_count // 2] += 1

    if filter_type == "低通":
        coefficients /= coefficients.sum()
    elif filter_type == "带通":
        center_frequency = (cutoff_low + cutoff_high) / 2
        indices = np.arange(tap_count)
        response = np.sum(
            coefficients
            * np.exp(-2j * np.pi * center_frequency * indices / sampling_rate)
        )
        coefficients /= abs(response)
    return coefficients


def apply_fir_filter(
    samples: NDArray[np.float64],
    coefficients: NDArray[np.float64],
) -> NDArray[np.float64]:
    samples = np.asarray(samples, dtype=float)
    coefficients = np.asarray(coefficients, dtype=float)
    if samples.ndim != 1 or samples.size == 0 or not np.all(np.isfinite(samples)):
        raise ValueError("samples 必须是一维、非空且全部有限的数组")
    if (
        coefficients.ndim != 1
        or coefficients.size == 0
        or not np.all(np.isfinite(coefficients))
    ):
        raise ValueError("coefficients 必须是一维、非空且全部有限的数组")
    padding = coefficients.size // 2
    padded = np.pad(samples, (padding, padding), mode="edge")
    return np.convolve(padded, coefficients, mode="valid")


def _lowpass_kernel(
    normalized_cutoff: float,
    tap_count: int,
) -> NDArray[np.float64]:
    center = tap_count // 2
    indices = np.arange(tap_count) - center
    ideal = normalized_cutoff * np.sinc(normalized_cutoff * indices)
    coefficients = ideal * np.hamming(tap_count)
    return coefficients / coefficients.sum()

"""常见连续时间信号的离散采样生成函数。"""

from typing import Literal

import numpy as np
from numpy.typing import NDArray


SignalType = Literal["sine", "square", "triangle", "pulse", "exponential"]


def generate_signal(
    signal_type: SignalType,
    time: NDArray[np.float64],
    *,
    amplitude: float = 1.0,
    frequency: float = 5.0,
    phase_degrees: float = 0.0,
    duty_cycle: float = 0.5,
    pulse_width: float = 0.1,
    decay_rate: float = 2.0,
    time_offset: float = 0.0,
) -> NDArray[np.float64]:
    """生成信号；time_offset 推进信号自身，不移动显示坐标轴。"""
    time = np.asarray(time, dtype=float)
    if time.ndim != 1 or time.size == 0:
        raise ValueError("time 必须是一维且非空的数组")
    if not np.all(np.isfinite(time)):
        raise ValueError("time 必须全部为有限值")
    if not np.isfinite(amplitude) or amplitude < 0:
        raise ValueError("amplitude 必须是非负有限值")
    if not np.isfinite(phase_degrees):
        raise ValueError("phase_degrees 必须是有限值")
    if not np.isfinite(time_offset):
        raise ValueError("time_offset 必须是有限值")

    signal_time = time + time_offset
    phase = np.deg2rad(phase_degrees)
    if signal_type in ("sine", "square", "triangle"):
        if not np.isfinite(frequency) or frequency <= 0:
            raise ValueError("周期信号的 frequency 必须为正")
        cycles = np.remainder(
            frequency * signal_time + phase / (2 * np.pi),
            1.0,
        )
        if signal_type == "sine":
            shape = np.sin(2 * np.pi * cycles)
        elif signal_type == "square":
            if not 0 < duty_cycle < 1:
                raise ValueError("duty_cycle 必须在 0 和 1 之间")
            shape = np.where(cycles < duty_cycle, 1.0, -1.0)
        else:
            shape = 1.0 - 4.0 * np.abs(cycles - 0.5)
        return amplitude * shape

    if signal_type == "pulse":
        if not np.isfinite(pulse_width) or pulse_width <= 0:
            raise ValueError("pulse_width 必须为正")
        center = (time[0] + time[-1]) / 2
        shape = np.abs(signal_time - center) < pulse_width / 2
        return amplitude * shape.astype(float)

    if signal_type == "exponential":
        if not np.isfinite(decay_rate) or decay_rate <= 0:
            raise ValueError("decay_rate 必须为正")
        return amplitude * np.exp(-decay_rate * np.maximum(signal_time, 0))

    raise ValueError(f"不支持的信号类型：{signal_type}")

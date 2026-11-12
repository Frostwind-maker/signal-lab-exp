"""时域、频域及时频域图表组件。"""

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from numpy.typing import NDArray


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def _add_animation_controls(
    figure: go.Figure,
    frame_names: list[str],
) -> None:
    play_options = {
        "frame": {"duration": 80, "redraw": True},
        "fromcurrent": True,
        "transition": {"duration": 0},
    }
    immediate_options = {
        "mode": "immediate",
        "frame": {"duration": 0, "redraw": True},
        "transition": {"duration": 0},
    }
    figure.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0,
                "y": 1.16,
                "xanchor": "left",
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "播放",
                        "method": "animate",
                        "args": [None, play_options],
                    },
                    {
                        "label": "暂停",
                        "method": "animate",
                        "args": [[None], immediate_options],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "x": 0.18,
                "len": 0.8,
                "currentvalue": {"prefix": "帧 "},
                "steps": [
                    {
                        "label": str(index + 1),
                        "method": "animate",
                        "args": [[name], immediate_options],
                    }
                    for index, name in enumerate(frame_names)
                ],
            }
        ],
    )


def build_time_frequency_animation(
    time: NDArray[np.float64],
    wave_frames: NDArray[np.float64],
    freq_frames: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    *,
    sampling_rate: float,
    fft_points: int,
    window_name: str,
) -> go.Figure:
    time = np.asarray(time, dtype=float)
    wave_frames = np.asarray(wave_frames, dtype=float)
    freq_frames = np.asarray(freq_frames, dtype=float)
    frequencies = np.asarray(frequencies, dtype=float)
    if time.ndim != 1 or time.size == 0:
        raise ValueError("time 必须是一维非空数组")
    if (
        wave_frames.ndim != 2
        or wave_frames.shape[1] != time.size
        or wave_frames.shape[0] == 0
    ):
        raise ValueError("wave_frames 形状必须为 (帧数, len(time))")
    if (
        frequencies.ndim != 1
        or frequencies.size == 0
        or freq_frames.shape != (wave_frames.shape[0], frequencies.size)
    ):
        raise ValueError("freq_frames 形状必须为 (帧数, len(frequencies))")
    if not np.all(np.isfinite(time)) or not np.all(np.isfinite(wave_frames)):
        raise ValueError("时间和波形帧必须全部为有限值")
    if not np.all(np.isfinite(freq_frames)) or not np.all(np.isfinite(frequencies)):
        raise ValueError("频谱帧和频率必须全部为有限值")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0 or fft_points < 2:
        raise ValueError("sampling_rate 和 fft_points 必须为正")

    frame_names = [str(index) for index in range(wave_frames.shape[0])]
    figure = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.16,
        subplot_titles=("时域波形", f"单边幅度谱（{window_name}）"),
    )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=wave_frames[0],
            mode="lines",
            name="信号",
            line={"color": "#1769aa", "width": 2},
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=frequencies,
            y=freq_frames[0],
            mode="lines",
            name="幅度谱",
            line={"color": "#d1495b", "width": 1.5},
        ),
        row=2,
        col=1,
    )
    figure.frames = tuple(
        go.Frame(
            name=name,
            data=[
                go.Scatter(y=wave_frames[index]),
                go.Scatter(y=freq_frames[index]),
            ],
            traces=[0, 1],
        )
        for index, name in enumerate(frame_names)
    )
    wave_min = float(np.min(wave_frames))
    wave_max = float(np.max(wave_frames))
    padding = max((wave_max - wave_min) * 0.08, 0.05)
    figure.update_layout(
        title=(
            f"采样率 {sampling_rate:g} Hz | FFT 点数 {fft_points} | "
            f"频率栅格间隔 {sampling_rate / fft_points:.3g} Hz"
        ),
        font={"family": "Microsoft YaHei, sans-serif"},
        template="plotly_white",
        height=720,
        margin={"t": 125},
        xaxis={
            "title": "时间 (s)",
            "range": [float(time[0]), float(time[-1])],
            "fixedrange": True,
        },
        yaxis={
            "title": "幅值",
            "range": [wave_min - padding, wave_max + padding],
        },
        xaxis2={
            "title": "频率 (Hz)",
            "range": [0, sampling_rate / 2],
            "fixedrange": True,
        },
        yaxis2={"title": "幅度"},
    )
    for frame in figure.frames:
        frame.layout = go.Layout(
            xaxis={"range": [float(time[0]), float(time[-1])]},
            xaxis2={"range": [0, sampling_rate / 2]},
        )
    _add_animation_controls(figure, frame_names)
    return figure


def build_series_animation(
    time: NDArray[np.float64],
    approximations: NDArray[np.float64],
    orders: NDArray[np.int64],
    amplitudes: NDArray[np.float64],
    *,
    signal_name: str,
    reference: NDArray[np.float64],
) -> go.Figure:
    time = np.asarray(time, dtype=float)
    approximations = np.asarray(approximations, dtype=float)
    orders = np.asarray(orders, dtype=int)
    amplitudes = np.asarray(amplitudes, dtype=float)
    reference = np.asarray(reference, dtype=float)
    if time.ndim != 1 or time.size == 0 or reference.shape != time.shape:
        raise ValueError("time 和 reference 必须是一维等长数组")
    if (
        approximations.ndim != 2
        or approximations.shape[1] != time.size
        or approximations.shape[0] == 0
    ):
        raise ValueError("approximations 形状必须为 (帧数, len(time))")
    if orders.ndim != 1 or amplitudes.shape != orders.shape:
        raise ValueError("orders 和 amplitudes 必须是一维等长数组")
    if (
        not np.all(np.isfinite(time))
        or not np.all(np.isfinite(reference))
        or not np.all(np.isfinite(approximations))
        or not np.all(np.isfinite(amplitudes))
    ):
        raise ValueError("动画输入数据必须全部为有限值")

    frame_names = [str(index) for index in range(approximations.shape[0])]
    figure = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.16,
        subplot_titles=(f"{signal_name}傅里叶级数合成", "当前谐波幅值"),
    )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=reference,
            mode="lines",
            name="目标波形",
            line={"color": "#888888", "width": 1, "dash": "dot"},
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=approximations[0],
            mode="lines",
            name="合成波形",
            line={"color": "#1769aa", "width": 2},
        ),
        row=1,
        col=1,
    )
    initial_amplitudes = np.where(orders <= 1, amplitudes, 0)
    figure.add_trace(
        go.Bar(
            x=orders,
            y=initial_amplitudes,
            name="谐波幅值",
            marker_color="#d1495b",
        ),
        row=2,
        col=1,
    )
    figure.frames = tuple(
        go.Frame(
            name=name,
            data=[
                go.Scatter(y=approximations[index]),
                go.Bar(y=np.where(orders <= index + 1, amplitudes, 0)),
            ],
            traces=[1, 2],
        )
        for index, name in enumerate(frame_names)
    )
    all_wave_values = np.concatenate((reference, approximations.ravel()))
    wave_min = float(np.min(all_wave_values))
    wave_max = float(np.max(all_wave_values))
    padding = max((wave_max - wave_min) * 0.08, 0.05)
    figure.update_layout(
        font={"family": "Microsoft YaHei, sans-serif"},
        template="plotly_white",
        height=720,
        margin={"t": 125},
        xaxis={
            "title": "时间 (s)",
            "range": [float(time[0]), float(time[-1])],
            "fixedrange": True,
        },
        yaxis={"title": "幅值", "range": [wave_min - padding, wave_max + padding]},
        xaxis2={"title": "谐波序号", "range": [0, max(int(orders[-1]), 1) + 1]},
        yaxis2={"title": "峰值幅度"},
    )
    for frame in figure.frames:
        frame.layout = go.Layout(
            xaxis={"range": [float(time[0]), float(time[-1])]}
        )
    _add_animation_controls(figure, frame_names)
    return figure


def build_stft_animation(
    time: NDArray[np.float64],
    samples: NDArray[np.float64],
    frame_times: NDArray[np.float64],
    frequencies: NDArray[np.float64],
    magnitude: NDArray[np.float64],
    *,
    window_length: int,
    sampling_rate: float,
) -> go.Figure:
    time = np.asarray(time, dtype=float)
    samples = np.asarray(samples, dtype=float)
    frame_times = np.asarray(frame_times, dtype=float)
    frequencies = np.asarray(frequencies, dtype=float)
    magnitude = np.asarray(magnitude, dtype=float)
    if time.ndim != 1 or samples.shape != time.shape or time.size == 0:
        raise ValueError("time 和 samples 必须是一维等长数组")
    if frame_times.ndim != 1 or frame_times.size == 0:
        raise ValueError("frame_times 必须是一维非空数组")
    if frequencies.ndim != 1 or frequencies.size == 0:
        raise ValueError("frequencies 必须是一维非空数组")
    if magnitude.shape != (frame_times.size, frequencies.size):
        raise ValueError("magnitude 形状必须为 (len(frame_times), len(frequencies))")
    if not isinstance(window_length, int) or window_length < 1:
        raise ValueError("window_length 必须为正整数")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not all(
        np.all(np.isfinite(values))
        for values in (time, samples, frame_times, frequencies, magnitude)
    ):
        raise ValueError("STFT 动画输入必须全部为有限值")

    half_window = window_length / (2 * sampling_rate)
    frame_names = [str(index) for index in range(frame_times.size)]
    figure = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.14,
        row_heights=[0.35, 0.65],
        subplot_titles=("信号与当前分析窗", "STFT 时频图（相对幅度 dB）"),
    )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=samples,
            mode="lines",
            name="信号",
            line={"color": "#1769aa", "width": 1.5},
        ),
        row=1,
        col=1,
    )
    magnitude_db = 20 * np.log10(np.maximum(magnitude.T, 1e-8))
    figure.add_trace(
        go.Heatmap(
            x=frame_times,
            y=frequencies,
            z=magnitude_db,
            colorscale="Magma",
            colorbar={"title": "幅度 (dB)"},
            name="STFT",
        ),
        row=2,
        col=1,
    )

    def frame_shapes(frame_time: float) -> list[dict[str, object]]:
        return [
            {
                "type": "rect",
                "xref": "x",
                "yref": "y domain",
                "x0": max(float(time[0]), frame_time - half_window),
                "x1": min(float(time[-1]), frame_time + half_window),
                "y0": 0,
                "y1": 1,
                "fillcolor": "rgba(244, 162, 97, 0.25)",
                "line": {"width": 0},
                "layer": "above",
            },
            {
                "type": "line",
                "xref": "x2",
                "yref": "y2",
                "x0": float(frame_time),
                "x1": float(frame_time),
                "y0": float(frequencies[0]),
                "y1": float(frequencies[-1]),
                "line": {"color": "#d1495b", "width": 2},
            },
        ]

    figure.frames = tuple(
        go.Frame(
            name=name,
            layout=go.Layout(shapes=frame_shapes(float(frame_time))),
        )
        for name, frame_time in zip(frame_names, frame_times)
    )
    figure.update_layout(
        font={"family": "Microsoft YaHei, sans-serif"},
        template="plotly_white",
        height=720,
        margin={"t": 125},
        xaxis={
            "title": "时间 (s)",
            "range": [float(time[0]), float(time[-1])],
            "fixedrange": True,
        },
        yaxis={"title": "幅值"},
        xaxis2={
            "title": "时间 (s)",
            "range": [float(frame_times[0]), float(frame_times[-1])],
            "fixedrange": True,
        },
        yaxis2={
            "title": "频率 (Hz)",
            "range": [float(frequencies[0]), float(frequencies[-1])],
        },
        shapes=frame_shapes(float(frame_times[0])),
    )
    for frame in figure.frames:
        frame.layout = go.Layout(
            shapes=frame.layout.shapes,
            xaxis={"range": [float(time[0]), float(time[-1])]},
            xaxis2={
                "range": [float(frame_times[0]), float(frame_times[-1])]
            },
        )
    _add_animation_controls(figure, frame_names)
    return figure


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

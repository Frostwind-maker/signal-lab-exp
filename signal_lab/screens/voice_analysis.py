import queue

import numpy as np
import streamlit as st
import sounddevice as sd

from signal_lab.core.audio import analyze_audio_frames, decode_wav
from signal_lab.core.spectrum import compute_amplitude_spectrum
from signal_lab.visualization.animation import render_animation_controls
from signal_lab.visualization.plots import (
    create_audio_analysis_figure,
    create_live_audio_figure,
)


class _AudioChunkQueue:
    def __init__(self) -> None:
        self._queue = queue.Queue(maxsize=64)
        self.dropped_chunks = 0
        self.callback_status = ""

    def append(self, chunk: np.ndarray) -> None:
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self.dropped_chunks += 1
            self._queue.put_nowait(chunk)

    def drain(self) -> list[np.ndarray]:
        chunks = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                return chunks


@st.fragment(run_every=0.1)
def _render_live_microphone() -> None:
    sampling_rate = 16000
    history_length = sampling_rate
    queue_key = "live_audio_queue"
    stream_key = "live_audio_stream"
    samples_key = "live_audio_samples"
    st.session_state.setdefault(samples_key, np.zeros(0, dtype=float))

    columns = st.columns(2)
    start_requested = columns[0].button(
        "開始實時分析",
        key="live_audio_start",
        disabled=st.session_state.get(stream_key) is not None,
    )
    stop_requested = columns[1].button(
        "停止實時分析",
        key="live_audio_stop",
        disabled=st.session_state.get(stream_key) is None,
    )
    if start_requested:
        audio_queue = _AudioChunkQueue()

        def capture_callback(
            input_data: np.ndarray,
            frames: int,
            timing: object,
            status: sd.CallbackFlags,
        ) -> None:
            if status:
                audio_queue.callback_status = str(status)
            audio_queue.append(input_data[:, 0].copy())

        stream: sd.InputStream | None = None
        try:
            stream = sd.InputStream(
                samplerate=sampling_rate,
                channels=1,
                dtype="float32",
                blocksize=512,
                callback=capture_callback,
            )
            stream.start()
        except (sd.PortAudioError, OSError) as error:
            if stream is not None:
                try:
                    stream.close()
                except sd.PortAudioError as close_error:
                    st.error(
                        f"无法启动麦克风：{error}；清理音频设备也失败：{close_error}"
                    )
                    return
            st.error(f"无法启动麦克风：{error}")
        else:
            st.session_state[queue_key] = audio_queue
            st.session_state[stream_key] = stream
            st.session_state[samples_key] = np.zeros(0, dtype=float)

    if stop_requested:
        stop_live_audio_if_running()

    audio_queue = st.session_state.get(queue_key)
    if audio_queue is not None:
        new_chunks = audio_queue.drain()
        if new_chunks:
            st.session_state[samples_key] = np.concatenate(
                (st.session_state[samples_key], *new_chunks)
            )[-history_length:]

    stream_active = st.session_state.get(stream_key) is not None
    if stream_active:
        samples = st.session_state[samples_key]
        padded = np.pad(samples, (max(0, history_length - samples.size), 0))
        time = np.arange(-history_length, 0) / sampling_rate
        frequencies, magnitude = compute_amplitude_spectrum(
            padded,
            sampling_rate,
            history_length,
            "汉宁窗",
        )
        st.pyplot(
            create_live_audio_figure(time, padded, frequencies, magnitude),
            width="stretch",
        )
        st.caption(
            f"采样率 {sampling_rate} Hz | 缓冲区丢弃帧数："
            f"{audio_queue.dropped_chunks}"
        )
        if audio_queue.callback_status:
            st.warning(f"麦克风采集状态：{audio_queue.callback_status}")
    else:
        st.info("点击“开始实时分析”以启动本机麦克风；结束后请停止采集。")


def stop_live_audio_if_running() -> None:
    stream = st.session_state.get("live_audio_stream")
    if stream is None:
        return
    try:
        stream.stop()
        stream.close()
    except sd.PortAudioError as error:
        st.error(f"关闭麦克风时发生错误：{error}")
    finally:
        st.session_state["live_audio_stream"] = None
        st.session_state["live_audio_queue"] = None


@st.cache_data(show_spinner=False)
def _decode_and_analyze(
    audio_bytes: bytes,
    frame_length_ms: int,
    hop_length_ms: int,
) -> tuple[
    float,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    sampling_rate, samples = decode_wav(audio_bytes)
    samples = samples[: int(sampling_rate * 30)]
    frame_length = max(2, round(sampling_rate * frame_length_ms / 1000))
    hop_length = max(1, round(sampling_rate * hop_length_ms / 1000))
    frame_times, frequencies, magnitude = analyze_audio_frames(
        samples,
        sampling_rate,
        frame_length,
        hop_length,
        fft_points=1 << (frame_length - 1).bit_length(),
        window_name="汉宁窗",
    )
    return sampling_rate, samples, frame_times, frequencies, magnitude


def render() -> None:
    st.title("拓展：语音实时频谱分析")
    st.write("实时查看本机麦克风频谱，或导入/录制 PCM WAV 逐帧分析。")
    st.subheader("实时麦克风频谱")
    _render_live_microphone()
    st.divider()
    st.subheader("录音或 WAV 分帧回放")
    uploaded_audio = st.file_uploader("选择 WAV 音频", type=["wav"])
    recorded_audio = st.audio_input("使用麦克风录制语音")
    audio_file = recorded_audio or uploaded_audio

    if audio_file is None:
        st.info("请录制一段语音或上传 PCM WAV 音频开始分析。")
        return

    frame_length_ms = st.select_slider(
        "分析帧长 (ms)",
        options=(16, 20, 25, 32, 40),
        value=25,
    )
    hop_length_ms = st.select_slider(
        "帧移 (ms)",
        options=(5, 10, 15, 20),
        value=10,
    )
    audio_bytes = audio_file.getvalue()
    try:
        (
            sampling_rate,
            samples,
            frame_times,
            frequencies,
            magnitude,
        ) = _decode_and_analyze(audio_bytes, frame_length_ms, hop_length_ms)
    except ValueError as error:
        st.error(str(error))
        return

    if samples.size == 0:
        st.error("WAV 音频没有可分析的采样点。")
        return
    duration = samples.size / sampling_rate
    if audio_file.getbuffer().nbytes and duration >= 30:
        st.warning("为控制计算量，仅分析音频的前 30 秒。")

    display_step = max(1, samples.size // 12000)
    time = np.arange(0, samples.size, display_step) / sampling_rate
    displayed_samples = samples[::display_step]

    def render_frame(frame_index: int) -> None:
        st.pyplot(
            create_audio_analysis_figure(
                time,
                displayed_samples,
                frame_times,
                frequencies,
                magnitude,
                frame_index,
                sampling_rate,
            ),
            width="stretch",
        )

    render_animation_controls(len(frame_times), "voice_analysis", render_frame)
    st.audio(audio_bytes, format="audio/wav")
    metrics = st.columns(3)
    metrics[0].metric("采样率", f"{sampling_rate:g} Hz")
    metrics[1].metric("分析时长", f"{duration:.2f} s")
    metrics[2].metric("分析帧数", len(frame_times))
    st.caption(
        "音频以 10 ms 帧移逐帧分析。浏览器录音/WAV 回放为采集后的分帧分析；"
        "实时麦克风区域直接从运行应用的本机音频设备采集。"
    )

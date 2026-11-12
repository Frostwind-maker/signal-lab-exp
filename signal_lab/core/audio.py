"""WAV 音频解码和分帧频谱分析。"""

import io
import wave

import numpy as np
from numpy.typing import NDArray

from signal_lab.core.spectrum import compute_amplitude_spectrum


def decode_wav(audio_bytes: bytes) -> tuple[float, NDArray[np.float64]]:
    """解码 8/16/32 位 PCM WAV，并将多声道合成为单声道。"""
    if not audio_bytes:
        raise ValueError("音频文件为空")
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sampling_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            compression = wav_file.getcomptype()
            raw = wav_file.readframes(frame_count)
    except (wave.Error, EOFError) as error:
        raise ValueError(f"无法读取 WAV 音频：{error}") from error

    if compression != "NONE":
        raise ValueError("仅支持未压缩 PCM WAV 音频")
    if sample_width not in (1, 2, 3, 4):
        raise ValueError("仅支持 8、16、24 或 32 位 PCM WAV 音频")

    if sample_width == 1:
        pcm = np.frombuffer(raw, dtype=np.uint8).astype(float)
        pcm = (pcm - 128) / 128
    elif sample_width == 2:
        pcm = np.frombuffer(raw, dtype="<i2").astype(float) / 32768
    elif sample_width == 3:
        byte_samples = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        integer_samples = (
            byte_samples[:, 0].astype(np.int32)
            | (byte_samples[:, 1].astype(np.int32) << 8)
            | (byte_samples[:, 2].astype(np.int32) << 16)
        )
        integer_samples = np.where(
            integer_samples & 0x800000,
            integer_samples - 0x1000000,
            integer_samples,
        )
        pcm = integer_samples.astype(float) / 8388608
    else:
        pcm = np.frombuffer(raw, dtype="<i4").astype(float) / 2147483648

    if pcm.size != frame_count * channels:
        raise ValueError("WAV 音频数据不完整")
    samples = pcm.reshape(-1, channels).mean(axis=1)
    return float(sampling_rate), samples


def analyze_audio_frames(
    samples: NDArray[np.float64],
    sampling_rate: float,
    frame_length: int,
    hop_length: int,
    fft_points: int | None = None,
    window_name: str = "汉宁窗",
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 1 or samples.size == 0 or not np.all(np.isfinite(samples)):
        raise ValueError("samples 必须是一维、非空且全部有限的数组")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate 必须为正")
    if not isinstance(frame_length, int) or frame_length < 2:
        raise ValueError("frame_length 必须大于等于 2")
    if not isinstance(hop_length, int) or hop_length < 1:
        raise ValueError("hop_length 必须为正整数")

    starts = np.arange(0, samples.size, hop_length, dtype=np.int64)
    frames = np.zeros((starts.size, frame_length), dtype=float)
    valid_lengths = np.minimum(frame_length, samples.size - starts)
    frame_times = (starts + valid_lengths / 2) / sampling_rate
    for index, start in enumerate(starts):
        segment = samples[start : start + frame_length]
        frames[index, : segment.size] = segment

    spectra = []
    frequencies = None
    for frame in frames:
        frequencies, magnitude = compute_amplitude_spectrum(
            frame,
            sampling_rate,
            fft_points or frame_length,
            window_name,
        )
        spectra.append(magnitude)
    return frame_times, frequencies, np.vstack(spectra)

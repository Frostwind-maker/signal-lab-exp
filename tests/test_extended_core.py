import io
import unittest
import wave

import numpy as np

from signal_lab.core.audio import analyze_audio_frames, decode_wav
from signal_lab.core.filters import apply_fir_filter, design_fir_filter
from signal_lab.core.fourier_series import (
    harmonic_components,
    synthesize_series,
)
from signal_lab.core.sampling import alias_frequency, is_aliased, sample_signal
from signal_lab.core.spectrum import compute_amplitude_phase_spectrum
from signal_lab.core.time_frequency import compute_stft


class FourierSeriesTests(unittest.TestCase):
    def test_square_and_triangle_harmonic_ratios(self) -> None:
        _, _, square = harmonic_components("square", 10, 5)
        _, _, triangle = harmonic_components("triangle", 10, 5)
        self.assertAlmostEqual(float(square[1] / square[0]), 1 / 3)
        self.assertAlmostEqual(float(triangle[1] / triangle[0]), -1 / 9)

    def test_series_approximation_has_requested_shape(self) -> None:
        time = np.linspace(0, 1, 200, endpoint=False)
        result = synthesize_series(time, "square", 5, 9)
        self.assertEqual(result.shape, time.shape)
        self.assertGreater(float(result.max()), 1.0)


class TimeFrequencyTests(unittest.TestCase):
    def test_stft_frame_times_and_frequency_bins(self) -> None:
        sampling_rate = 1000
        time = np.arange(1000) / sampling_rate
        samples = np.sin(2 * np.pi * 50 * time)
        frame_times, frequencies, magnitude = compute_stft(
            samples,
            sampling_rate,
            window_length=128,
            hop_length=64,
            fft_points=256,
        )
        self.assertEqual(magnitude.shape, (len(frame_times), len(frequencies)))
        self.assertEqual(len(frequencies), 129)
        self.assertTrue(np.all(np.diff(frame_times) > 0))
        self.assertLessEqual(float(frame_times[-1]), float(time[-1]))
        self.assertEqual(float(frequencies[np.argmax(magnitude[4])]), 50.78125)

    def test_stft_rejects_invalid_fft_length(self) -> None:
        with self.assertRaises(ValueError):
            compute_stft(np.ones(100), 1000, 64, 16, 32)


class SamplingTests(unittest.TestCase):
    def test_sample_signal_uses_requested_rate(self) -> None:
        reference_time = np.arange(2000) / 2000
        reference = np.sin(2 * np.pi * 10 * reference_time)
        sample_times, samples = sample_signal(
            reference_time,
            reference,
            sampling_rate=100,
            duration=1,
        )
        self.assertEqual(len(samples), 100)
        self.assertAlmostEqual(float(sample_times[1] - sample_times[0]), 0.01)
        self.assertAlmostEqual(float(samples[25]), 0.0, places=2)

    def test_alias_frequency_and_nyquist_decision(self) -> None:
        self.assertEqual(alias_frequency(75, 100), 25)
        self.assertTrue(is_aliased(75, 100))
        self.assertFalse(is_aliased(50, 100))


class FilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sampling_rate = 1000
        self.time = np.arange(4000) / self.sampling_rate

    def _filtered_rms(self, frequency: float, filter_type: str) -> float:
        signal = np.sin(2 * np.pi * frequency * self.time)
        coefficients = design_fir_filter(
            filter_type,
            self.sampling_rate,
            cutoff_low=150,
            cutoff_high=300,
            tap_count=101,
        )
        filtered = apply_fir_filter(signal, coefficients)
        return float(np.sqrt(np.mean(filtered[200:-200] ** 2)))

    def test_lowpass_passes_low_and_rejects_high_tone(self) -> None:
        coefficients = design_fir_filter("低通", self.sampling_rate, 100)
        low_signal = np.sin(2 * np.pi * 40 * self.time)
        high_signal = np.sin(2 * np.pi * 300 * self.time)
        low_output = apply_fir_filter(low_signal, coefficients)
        high_output = apply_fir_filter(high_signal, coefficients)
        self.assertGreater(float(np.std(low_output[200:-200])), 0.65)
        self.assertLess(float(np.std(high_output[200:-200])), 0.1)

    def test_bandpass_normalization_and_bandstop_rejection(self) -> None:
        self.assertGreater(self._filtered_rms(220, "带通"), 0.6)
        self.assertLess(self._filtered_rms(220, "带阻"), 0.2)

    def test_even_fir_tap_count_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            design_fir_filter("低通", self.sampling_rate, 100, tap_count=100)


class AudioTests(unittest.TestCase):
    @staticmethod
    def _wav_bytes(samples: np.ndarray, sample_width: int, channels: int = 1) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(8000)
            wav_file.writeframes(samples.tobytes())
        return output.getvalue()

    def test_decode_16_bit_stereo_to_normalized_mono(self) -> None:
        stereo = np.array([[16384, 16384], [-16384, -16384]], dtype="<i2")
        sample_rate, decoded = decode_wav(self._wav_bytes(stereo, 2, 2))
        self.assertEqual(sample_rate, 8000)
        np.testing.assert_allclose(decoded, [0.5, -0.5])

    def test_decode_24_bit_pcm(self) -> None:
        values = [-8388608, 0, 8388607]
        payload = b"".join(
            (value & 0xFFFFFF).to_bytes(3, "little")
            for value in values
        )
        sample_rate, decoded = decode_wav(self._wav_bytes(np.frombuffer(payload, dtype=np.uint8), 3))
        self.assertEqual(sample_rate, 8000)
        self.assertAlmostEqual(float(decoded[0]), -1.0)
        self.assertAlmostEqual(float(decoded[-1]), 1.0, places=6)

    def test_audio_frames_return_valid_spectra(self) -> None:
        sampling_rate = 8000
        time = np.arange(4000) / sampling_rate
        samples = np.sin(2 * np.pi * 440 * time)
        frame_times, frequencies, magnitude = analyze_audio_frames(
            samples,
            sampling_rate,
            frame_length=400,
            hop_length=160,
        )
        self.assertEqual(magnitude.shape, (len(frame_times), len(frequencies)))
        peak_frequency = frequencies[int(np.argmax(magnitude[3]))]
        self.assertAlmostEqual(float(peak_frequency), 440, delta=20)


class PhaseSpectrumTests(unittest.TestCase):
    def test_sine_phase_is_recovered_at_tone_bin(self) -> None:
        sampling_rate = 1024
        time = np.arange(1024) / sampling_rate
        phase = np.deg2rad(30)
        samples = np.sin(2 * np.pi * 64 * time + phase)
        frequencies, magnitude, phase_spectrum = compute_amplitude_phase_spectrum(
            samples,
            sampling_rate,
            1024,
        )
        peak_index = int(np.argmax(magnitude))
        self.assertEqual(float(frequencies[peak_index]), 64)
        self.assertAlmostEqual(
            float(phase_spectrum[peak_index]),
            -np.pi / 3,
            places=10,
        )


if __name__ == "__main__":
    unittest.main()

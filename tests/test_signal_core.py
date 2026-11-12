import unittest

import numpy as np

from signal_lab.core.signals import generate_signal
from signal_lab.core.spectrum import compute_amplitude_spectrum


class GenerateSignalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sampling_rate = 1000
        self.time = np.arange(self.sampling_rate, dtype=float) / self.sampling_rate

    def test_sine_wave_has_requested_amplitude(self) -> None:
        samples = generate_signal(
            "sine",
            self.time,
            amplitude=2.5,
            frequency=10,
        )
        self.assertAlmostEqual(float(np.max(samples)), 2.5)
        self.assertAlmostEqual(float(np.min(samples)), -2.5)

    def test_sine_phase_controls_initial_sample(self) -> None:
        samples = generate_signal(
            "sine",
            self.time,
            frequency=10,
            phase_degrees=90,
        )
        self.assertAlmostEqual(float(samples[0]), 1.0)

    def test_time_offset_moves_signal_without_changing_time_axis(self) -> None:
        time = np.arange(100, dtype=float) / 100
        frequency = 5
        offset = 0.1
        moved = generate_signal(
            "sine",
            time,
            frequency=frequency,
            time_offset=offset,
        )
        expected = generate_signal("sine", time + offset, frequency=frequency)
        np.testing.assert_allclose(moved, expected)

    def test_time_offset_moves_rectangular_pulse_on_fixed_axis(self) -> None:
        time = np.arange(100, dtype=float) / 100
        original = generate_signal("pulse", time, pulse_width=0.1)
        moved = generate_signal(
            "pulse",
            time,
            pulse_width=0.1,
            time_offset=0.2,
        )
        self.assertNotEqual(int(np.argmax(original)), int(np.argmax(moved)))
        self.assertAlmostEqual(float(moved.sum()), float(original.sum()))

    def test_square_wave_obeys_duty_cycle(self) -> None:
        samples = generate_signal(
            "square",
            self.time,
            frequency=10,
            duty_cycle=0.25,
        )
        self.assertAlmostEqual(float(np.mean(samples == 1)), 0.25)

    def test_triangle_wave_stays_within_amplitude(self) -> None:
        samples = generate_signal("triangle", self.time, amplitude=3, frequency=5)
        self.assertLessEqual(float(np.max(samples)), 3)
        self.assertGreaterEqual(float(np.min(samples)), -3)

    def test_pulse_is_centered_and_has_requested_width(self) -> None:
        time = np.arange(1000, dtype=float) / 1000
        samples = generate_signal("pulse", time, amplitude=2, pulse_width=0.1)
        active_times = time[samples > 0]
        self.assertAlmostEqual(float(active_times.mean()), 0.4995)
        self.assertEqual(len(active_times), 100)
        self.assertAlmostEqual(float(samples.max()), 2.0)

    def test_exponential_is_causal_and_decays(self) -> None:
        time = np.linspace(-0.2, 1, 1201)
        samples = generate_signal("exponential", time, decay_rate=2)
        self.assertEqual(float(samples[0]), 1.0)
        self.assertGreater(float(samples[200]), float(samples[-1]))

    def test_invalid_signal_parameters_raise(self) -> None:
        with self.assertRaises(ValueError):
            generate_signal("square", self.time, duty_cycle=1)


class SpectrumTests(unittest.TestCase):
    def test_single_sided_spectrum_recovers_bin_amplitude(self) -> None:
        sampling_rate = 1024
        time = np.arange(1024, dtype=float) / sampling_rate
        samples = 2.0 * np.sin(2 * np.pi * 64 * time)

        frequencies, magnitude = compute_amplitude_spectrum(
            samples,
            sampling_rate,
            1024,
        )

        peak_index = int(np.argmax(magnitude))
        self.assertEqual(float(frequencies[peak_index]), 64.0)
        self.assertAlmostEqual(float(magnitude[peak_index]), 2.0)

    def test_zero_padding_changes_bin_spacing(self) -> None:
        samples = np.ones(128)
        frequencies, _ = compute_amplitude_spectrum(samples, 1000, 512)
        self.assertEqual(len(frequencies), 257)
        self.assertAlmostEqual(float(frequencies[1]), 1000 / 512)

    def test_square_spectrum_has_odd_harmonics(self) -> None:
        sampling_rate = 4096
        time = np.arange(4096, dtype=float) / sampling_rate
        samples = generate_signal(
            "square",
            time,
            frequency=16,
            duty_cycle=0.5,
        )
        _, magnitude = compute_amplitude_spectrum(samples, sampling_rate, 4096)

        fundamental = magnitude[16]
        self.assertAlmostEqual(float(magnitude[32]), 0.0, places=12)
        self.assertAlmostEqual(float(magnitude[48] / fundamental), 1 / 3, places=2)

    def test_triangle_harmonics_decay_faster_than_square_harmonics(self) -> None:
        sampling_rate = 4096
        time = np.arange(4096, dtype=float) / sampling_rate
        square = generate_signal("square", time, frequency=16)
        triangle = generate_signal("triangle", time, frequency=16)
        _, square_magnitude = compute_amplitude_spectrum(
            square,
            sampling_rate,
            4096,
        )
        _, triangle_magnitude = compute_amplitude_spectrum(
            triangle,
            sampling_rate,
            4096,
        )
        self.assertAlmostEqual(
            float(triangle_magnitude[48] / triangle_magnitude[16]),
            1 / 9,
            places=2,
        )
        self.assertLess(
            triangle_magnitude[48] / triangle_magnitude[16],
            square_magnitude[48] / square_magnitude[16],
        )

    def test_window_gain_correction_recovers_bin_amplitude(self) -> None:
        sampling_rate = 1024
        time = np.arange(1024, dtype=float) / sampling_rate
        samples = 1.75 * np.sin(2 * np.pi * 64 * time)

        for window_name in ("汉宁窗", "汉明窗"):
            with self.subTest(window=window_name):
                _, magnitude = compute_amplitude_spectrum(
                    samples,
                    sampling_rate,
                    1024,
                    window_name,
                )
                self.assertAlmostEqual(float(magnitude[64]), 1.75, places=2)

    def test_unsupported_window_raises(self) -> None:
        with self.assertRaises(ValueError):
            compute_amplitude_spectrum(
                np.ones(16),
                1000,
                16,
                "未知窗",
            )


if __name__ == "__main__":
    unittest.main()

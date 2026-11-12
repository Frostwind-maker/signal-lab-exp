import unittest

import numpy as np

from signal_lab.visualization.plots import (
    build_series_animation,
    build_stft_animation,
    build_time_frequency_animation,
)


class PlotlyAnimationTests(unittest.TestCase):
    def test_time_frequency_animation_has_fixed_x_and_y_only_frames(self) -> None:
        time = np.linspace(0, 1, 1200, endpoint=False)
        frequencies = np.linspace(0, 500, 257)
        wave_frames = np.stack(
            [np.sin(2 * np.pi * 5 * (time + index * 0.05)) for index in range(60)]
        )
        freq_frames = np.ones((60, frequencies.size))

        figure = build_time_frequency_animation(
            time,
            wave_frames,
            freq_frames,
            frequencies,
            sampling_rate=1000,
            fft_points=512,
            window_name="汉宁窗",
        )

        self.assertEqual(len(figure.frames), 60)
        self.assertEqual(list(figure.layout.xaxis.range), [time[0], time[-1]])
        self.assertEqual(len(figure.frames[0].data), 2)
        self.assertIsNone(figure.frames[0].data[0].x)
        self.assertIsNone(figure.frames[0].data[1].x)
        self.assertEqual(
            len(figure.layout.updatemenus[0].buttons),
            2,
        )
        self.assertEqual(len(figure.layout.sliders[0].steps), 60)

    def test_series_animation_updates_approximation_and_harmonics(self) -> None:
        time = np.linspace(0, 1, 1200, endpoint=False)
        approximations = np.stack(
            [
                np.sin(2 * np.pi * time),
                np.sin(2 * np.pi * time)
                + np.sin(6 * np.pi * time) / 3,
            ]
        )
        reference = np.sign(np.sin(2 * np.pi * time))
        figure = build_series_animation(
            time,
            approximations,
            np.array([1, 3]),
            np.array([1.0, 1 / 3]),
            signal_name="方波",
            reference=reference,
        )

        self.assertEqual(len(figure.frames), 2)
        self.assertEqual(len(figure.frames[1].data), 2)
        self.assertIsNone(figure.frames[1].data[0].x)
        self.assertIsNone(figure.frames[1].data[1].x)
        self.assertEqual(list(figure.layout.xaxis.range), [time[0], time[-1]])

    def test_stft_heatmap_is_static_and_frames_only_update_shapes(self) -> None:
        time = np.linspace(0, 2, 2000, endpoint=False)
        samples = np.sin(2 * np.pi * 25 * time)
        frame_times = np.linspace(0.064, 1.936, 30)
        frequencies = np.linspace(0, 500, 129)
        magnitude = np.abs(
            np.random.default_rng(42).normal(size=(frame_times.size, frequencies.size))
        )

        figure = build_stft_animation(
            time,
            samples,
            frame_times,
            frequencies,
            magnitude,
            window_length=128,
            sampling_rate=1000,
        )

        self.assertEqual(len(figure.data), 2)
        self.assertEqual(len(figure.frames), len(frame_times))
        self.assertEqual(figure.data[1].type, "heatmap")
        self.assertEqual(figure.frames[0].data, ())
        self.assertEqual(len(figure.frames[0].layout.shapes), 2)
        self.assertEqual(
            list(figure.layout.xaxis.range),
            [time[0], time[-1]],
        )
        self.assertEqual(
            list(figure.frames[1].layout.xaxis.range),
            [time[0], time[-1]],
        )

    def test_time_frequency_payload_stays_below_two_megabytes(self) -> None:
        time = np.linspace(0, 1, 1200, endpoint=False)
        frequencies = np.linspace(0, 500, 512)
        wave_frames = np.stack(
            [np.sin(2 * np.pi * 5 * (time + index / 60)) for index in range(60)]
        )
        freq_frames = np.ones((60, frequencies.size))
        figure = build_time_frequency_animation(
            time,
            wave_frames,
            freq_frames,
            frequencies,
            sampling_rate=1000,
            fft_points=1024,
            window_name="矩形窗",
        )
        self.assertLess(len(figure.to_json().encode("utf-8")), 2_000_000)


if __name__ == "__main__":
    unittest.main()

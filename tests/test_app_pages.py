import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
PAGES = (
    "时域与频域",
    "傅里叶级数合成",
    "短时傅里叶变换",
    "采样与混叠",
    "相位谱与窗函数",
    "滤波前后对比",
    "语音实时频谱",
)


class AppPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = AppTest.from_file(str(APP_PATH)).run()

    def test_all_pages_render_without_exceptions(self) -> None:
        for page in PAGES:
            with self.subTest(page=page):
                self.app.sidebar.radio[0].set_value(page)
                self.app.run()
                self.assertEqual(
                    len(self.app.exception),
                    0,
                    [error.message for error in self.app.exception],
                )

    def test_report_template_is_not_in_navigation(self) -> None:
        self.assertNotIn("实验报告", self.app.sidebar.radio[0].options)

    def test_all_signal_types_render_and_animation_advances(self) -> None:
        self.app.sidebar.radio[0].set_value("时域与频域").run()
        signal_selector = next(
            widget for widget in self.app.selectbox if widget.label == "信号类型"
        )
        for signal_name in ("正弦波", "方波", "三角波", "矩形脉冲", "指数衰减"):
            with self.subTest(signal=signal_name):
                signal_selector.set_value(signal_name)
                self.app.run()
                self.assertEqual(
                    len(self.app.exception),
                    0,
                    [error.message for error in self.app.exception],
                )

        next_button = next(
            button
            for button in self.app.button
            if button.key == "time_frequency_next"
        )
        next_button.click().run()
        self.assertEqual(self.app.session_state["time_frequency_position"], 1)

        reset_button = next(
            button
            for button in self.app.button
            if button.key == "time_frequency_reset"
        )
        reset_button.click().run()
        self.assertEqual(self.app.session_state["time_frequency_position"], 0)

        play_button = next(
            button
            for button in self.app.button
            if button.key == "time_frequency_toggle"
        )
        play_button.click().run()
        self.assertTrue(self.app.session_state["time_frequency_playing"])
        play_button = next(
            button
            for button in self.app.button
            if button.key == "time_frequency_toggle"
        )
        play_button.click().run()
        self.assertFalse(self.app.session_state["time_frequency_playing"])


if __name__ == "__main__":
    unittest.main()

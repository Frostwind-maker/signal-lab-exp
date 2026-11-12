import streamlit as st

from signal_lab.screens import (
    dashboard,
    fourier_series,
    sampling,
    spectral_extensions,
    stft,
    time_frequency,
    voice_analysis,
    waveform_filter,
)


PAGES = {
    "项目总览": dashboard.render,
    "时域与频域": time_frequency.render,
    "傅里叶级数合成": fourier_series.render,
    "短时傅里叶变换": stft.render,
    "采样与混叠": sampling.render,
    "相位谱与窗函数": spectral_extensions.render,
    "滤波前后对比": waveform_filter.render,
    "语音实时频谱": voice_analysis.render,
}


def render_app() -> None:
    st.sidebar.title("信号与系统实验")
    selected_page = st.sidebar.radio(
        "实验模块",
        tuple(PAGES),
        key="experiment_page",
    )
    st.sidebar.caption("基础实验、拓展实验及报告模板")
    if selected_page != "语音实时频谱":
        voice_analysis.stop_live_audio_if_running()
    PAGES[selected_page]()

import streamlit as st

from signal_lab.ui import render_app


st.set_page_config(
    page_title="信号与系统实验可视化",
    page_icon="📈",
    layout="wide",
)

render_app()

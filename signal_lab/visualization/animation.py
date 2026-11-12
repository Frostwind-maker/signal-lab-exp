"""Plotly 客户端帧动画展示。"""

import plotly.graph_objects as go
import streamlit as st


def render_animation_player(figure: go.Figure, state_key: str) -> None:
    st.plotly_chart(
        figure,
        use_container_width=True,
        key=state_key,
        config={"displayModeBar": False},
    )

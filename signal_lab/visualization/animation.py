"""基于 Streamlit fragment 的播放/暂停/单步/重置控件。"""

from collections.abc import Callable

import streamlit as st


@st.fragment(run_every=0.05)
def _render_controls(
    frame_count: int,
    state_key: str,
    render_frame: Callable[[int], None],
) -> None:
    position_key = f"{state_key}_position"
    playing_key = f"{state_key}_playing"
    slider_key = f"{state_key}_slider"

    position = min(
        max(
            st.session_state.get(
                position_key,
                st.session_state.get(slider_key, 0),
            ),
            0,
        ),
        frame_count - 1,
    )
    st.session_state[position_key] = position
    st.session_state[slider_key] = position
    st.session_state.setdefault(playing_key, False)

    if st.session_state[playing_key]:
        st.session_state[position_key] = (
            st.session_state.get(position_key, 0) + 1
        ) % frame_count
        st.session_state[slider_key] = st.session_state[position_key]

    play_columns = st.columns(4)
    if play_columns[0].button(
        "暂停" if st.session_state[playing_key] else "播放",
        key=f"{state_key}_toggle",
    ):
        st.session_state[playing_key] = not st.session_state[playing_key]
    if play_columns[1].button("上一步", key=f"{state_key}_previous"):
        st.session_state[playing_key] = False
        st.session_state[position_key] = (
            st.session_state.get(position_key, 0) - 1
        ) % frame_count
        st.session_state[slider_key] = st.session_state[position_key]
    if play_columns[2].button("下一步", key=f"{state_key}_next"):
        st.session_state[playing_key] = False
        st.session_state[position_key] = (
            st.session_state.get(position_key, 0) + 1
        ) % frame_count
        st.session_state[slider_key] = st.session_state[position_key]
    if play_columns[3].button("重置", key=f"{state_key}_reset"):
        st.session_state[playing_key] = False
        st.session_state[position_key] = 0
        st.session_state[slider_key] = 0

    st.slider(
        "动画帧",
        min_value=0,
        max_value=frame_count - 1,
        key=slider_key,
        on_change=_sync_position,
        args=(position_key, slider_key),
    )
    st.session_state[position_key] = st.session_state[slider_key]
    render_frame(st.session_state[position_key])


def _sync_position(position_key: str, slider_key: str) -> None:
    st.session_state[position_key] = st.session_state[slider_key]


def render_animation_controls(
    frame_count: int,
    state_key: str,
    render_frame: Callable[[int], None],
) -> None:
    if frame_count < 1:
        raise ValueError("frame_count 必须至少为 1")
    st.session_state.setdefault(f"{state_key}_position", 0)
    _render_controls(frame_count, state_key, render_frame)

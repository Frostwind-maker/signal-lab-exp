import streamlit as st


def render_module_placeholder(
    title: str,
    objective: str,
    planned_features: list[str],
    next_step: str,
) -> None:
    st.title(title)
    st.info("项目框架已建立，此模块将在后续步骤中实现。")
    st.markdown(f"**模块目标：** {objective}")

    st.subheader("计划功能")
    for feature in planned_features:
        st.markdown(f"- {feature}")

    st.caption(f"后续实现：{next_step}")

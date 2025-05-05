import streamlit as st

def display_pretty_table(df):
    st.dataframe(
        df.style.set_properties(**{
            'text-align': 'center'
        }).set_table_styles([
            {'selector': 'thead th', 'props': [('text-align', 'center')]}
        ])
    )

# alert section
def show_dismissible_alert(key: str, text: str, alert_type="warning"):
    colors = {
        "warning": {"bg": "#FFF3CD", "border": "#FFA502"},
        "info": {"bg": "#D1ECF1", "border": "#0C5460"},
        "success": {"bg": "#D4EDDA", "border": "#28A745"},
        "danger": {"bg": "#F8D7DA", "border": "#DC3545"},
    }

    style = colors.get(alert_type, colors["warning"])

    if f"hide_{key}" not in st.session_state:
        st.session_state[f"hide_{key}"] = False

    if not st.session_state[f"hide_{key}"]:

        # 將 ❌ 放在 alert 裡面
        close = st.button("❌", key=f"close_{key}", help="Close this alert")

        if close:
            st.session_state[f"hide_{key}"] = True
            return  # 提前結束，不顯示 alert

        # 顯示 alert 本體
        st.markdown(
            f"""
            <div style="padding:10px 10px 10px 10px;background-color:{style['bg']};
                        border-left:6px solid {style['border']};
                        margin-bottom:10px;position:relative;border-radius:5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>{text}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

import streamlit as st
from db_utils import *

CORRECT_PASSWORD = "1234"

def render_profile_section():
    # 密碼驗證階段
    if "profile_unlocked" not in st.session_state:
        st.session_state["profile_unlocked"] = False

    if not st.session_state["profile_unlocked"]:
        with st.expander("🧑‍💻 Profile Settings", expanded=False):
            with st.form("password_form"):
                password = st.text_input("🔒 Enter password to unlock profile settings", type="password")
                submitted = st.form_submit_button("🔓 Unlock")

                if submitted:
                    if password == CORRECT_PASSWORD:
                        st.session_state["profile_unlocked"] = True
                        st.success("✅ Unlocked!")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Please try again.")

    # 若通過密碼驗證才顯示 Expander
    if st.session_state["profile_unlocked"]:
        with st.expander("🧑‍💻 Profile Settings", expanded=True):
            with st.form(key="profile_form"):
                new_name = st.text_input("User Name", value=st.session_state.get("user_name", "Brian"))
                new_image = st.text_input("Avatar Image URL", value=st.session_state.get("user_image", ""))
                submitted = st.form_submit_button("💾 Save Profile")

                if submitted:
                    save_user_profile(new_name, new_image)
                    st.session_state["user_name"] = new_name
                    st.session_state["user_image"] = new_image
                    st.success("Profile saved! Please refresh to see changes.")
                    st.rerun()
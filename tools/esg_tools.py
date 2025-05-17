import streamlit as st
from typing import Annotated
from pdf_context import get_pdf_context

def show_pdf_content():
    pdf_content = st.session_state.get("pdf_text", "")

    return f"""
            🤖 Here's what I found from the uploaded PDF:\n
            {pdf_content}
            ----------------------------------##ALL DONE##\n
            """

def get_pdf_page_content(
    page: Annotated[int, "Page number to retrieve from PDF"]
) -> str:
    return get_pdf_context(page=page) + "##ALL DONE##"

def esg_analysis():
    from esg_analysis import analyze_esg_from_pdf
    return analyze_esg_from_pdf() + "##ALL DONE##"

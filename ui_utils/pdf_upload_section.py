import io # Process byte obj to file obj
import json
import fitz  # PyMuPDF
import streamlit as st
from pdf_context import *
from db_utils.esg_report_db_utils import (
    insert_esg_report_by_id
)
from lib.esg_info_extractor import extract_esg_info_from_pdf
from db_utils.esg_report_db_utils import insert_or_get_company_id


# pdf upload section
def render_pdf_upload_section():
    with st.expander("📄 Upload a PDF file", expanded=True):
        # Upload button section
        uploaded_file = st.file_uploader(
            "Upload PDF file",
            type=["pdf"],
            label_visibility="collapsed",
            key=st.session_state.get("file_uploader_key", "default_uploader")
        )

        # Load pdf example button
        if st.button("📥 Load ESG report example (PDF)"):
            with open("db/examples/esg_report_example.pdf", "rb") as f:
                uploaded_file = io.BytesIO(f.read())  # 包裝成類檔案物件

        # 若已解析 pdf 就不要重複執行
        if uploaded_file and "pdf_text" not in st.session_state:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

            extracted = extract_text_by_page(doc, max_pages=len(doc)) # 取全部頁面
            # extracted = extract_text_by_page(doc, max_pages=10) # 只取前 10 頁 for testing

            st.session_state["pdf_text"] = extracted
            st.success("✅ PDF uploaded and parsed successfully!")
        elif uploaded_file and "pdf_text" in st.session_state:
            st.warning("📄 A PDF is already loaded. Click 🗑️ Clear PDF to upload a new one.")

        # 匯入 Gemini Agent 以取得 ESG report info
        try:
            GEMINI_ENABLED = bool(st.secrets.get("GEMINI_API_KEY", None))
        except Exception as e:
            GEMINI_ENABLED = False
            print(f"❌ Failed to import Gemini agent: {e}")
            st.warning(f"Gemini Agent not available: {e}")

        # 若有 PDF 且 Gemini 可用，自動萃取 ESG 報告資訊
        if GEMINI_ENABLED and "pdf_text" in st.session_state and st.session_state["pdf_text"] != None:
            extract_esg_info_from_pdf(top_n_pages=[1, 2, 3, 4, 5])

        # Clear button
        if "pdf_text" in st.session_state:
            if st.button("🗑️ Clear PDF"):
                del st.session_state["pdf_text"]
                st.session_state.pop("pdf_info", None)
                st.session_state.pop("pdf_language", None)
                st.session_state.pop("esg_inserted", None)
                st.session_state["file_uploader_key"] = str(time.time())  # 重新生成 key
                st.rerun()

         # 自動寫入 ESG Report DB（僅當已解析並尚未寫入）
        if "pdf_info" in st.session_state and "pdf_text" in st.session_state and not st.session_state.get("esg_inserted", False):
            company_name = st.session_state["pdf_info"]["company_name"]
            industry = st.session_state["pdf_info"]["industry"]
            report_year = int(st.session_state["pdf_info"]["report_year"])

            # text_list = st.session_state["pdf_text"][:3]  # for testing: 前 3 頁內容
            text_list = st.session_state["pdf_text"]  # 全部頁面
            content = "\n\n".join(
                [page["content"] for page in text_list] if isinstance(text_list[0], dict) else text_list
            )

            # 🔍 將 "chinese"/"english" 轉換成 "zh"/"en"
            lang_detected = st.session_state.get("pdf_language", "english")
            language = "zh" if lang_detected == "chinese" else "en"

            try:
                company_id = insert_or_get_company_id(company_name, industry, language)
                # insert 進 db
                esg_report_inserted = insert_esg_report_by_id(company_id, report_year, content)

                st.session_state["esg_inserted"] = esg_report_inserted
                if esg_report_inserted:
                    st.success("✅ ESG report auto-inserted into the database!")
                else:
                    st.warning("⚠️ Report already exists in database.")

            except Exception as e:
                st.error(f"❌ Auto insert failed: {e}")

import json
import fitz  # PyMuPDF
import streamlit as st
import re
from pdf_context import *

# pdf upload section
def extract_json_from_gemini_output(text: str) -> str:
    """從 Gemini 回應中清理並提取 JSON 字串"""
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    return text[json_start:json_end].strip()

def render_pdf_upload_section():
    with st.expander("📄 Upload a PDF file", expanded=True):
        # Upload button section
        uploaded_file = st.file_uploader(
            "Upload PDF file",
            type=["pdf"],
            label_visibility="collapsed",
            key=st.session_state.get("file_uploader_key", "default_uploader")
        )

        # 若已解析 pdf 就不要重複執行
        if uploaded_file and "pdf_text" not in st.session_state:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

            # extracted = extract_text_by_page(doc, max_pages=len(doc)) # 取全部頁面
            extracted = extract_text_by_page(doc, max_pages=10) # 只取前 10 頁 for testing

            st.session_state["pdf_text"] = extracted
            st.success("✅ PDF uploaded and parsed successfully!")

        # 匯入 Gemini Agent
        try:
            from agents.gemini_agent import chat_with_gemini
            GEMINI_ENABLED = bool(st.secrets.get("GEMINI_API_KEY", None))
        except Exception as e:
            GEMINI_ENABLED = False
            print(f"❌ Failed to import Gemini agent: {e}")
            st.warning(f"Gemini Agent not available: {e}")

        # 若有 PDF 且 Gemini 可用，自動萃取 ESG 報告資訊
        if GEMINI_ENABLED and "pdf_text" in st.session_state and st.session_state["pdf_text"] != None:
            top_n_pages = [1, 2, 3, 4, 5]  # 預設前 5 頁
            contents = ""
            for p in top_n_pages:
                contents += get_pdf_context(page=p)

            prompt = (
                f"You are a JSON data extractor. Read the following ESG report text (from pages {top_n_pages}):\n\n"
                f"{contents}\n\n"
                "Please extract the following fields:\n"
                "- `company_name`\n"
                "- `industry`\n"
                "- `report_year`\n\n"
                "⚠️ Only return pure JSON with no explanation, no markdown formatting, and no extra text.\n"
                "✅ The JSON format should look exactly like:\n"
                "{\"company_name\": \"\", \"industry\": \"\", \"report_year\": \"\"}"
            )

            with st.spinner("🤖 Gemini is extracting ESG report information..."):
                result = chat_with_gemini(prompt, restrict = False)

            try:
                cleaned = extract_json_from_gemini_output(result)
                response = json.loads(cleaned)

                required_fields = ["company_name", "industry", "report_year"]
                missing_or_empty = [
                    key for key in required_fields
                    if key not in response or not response[key].strip()
                ]

                if not missing_or_empty:
                    st.session_state["pdf_info"] = response
                    st.info(
                        f"✅ ESG report info extracted:\n\n"
                        f"📌 **Company Name:** {response['company_name']}\n"
                        f"🏭 **Industry:** {response['industry']}\n"
                        f"📅 **Report Year:** {response['report_year']}"
                    )
                else:
                    st.warning(
                        f"⚠️ Gemini returned incomplete or empty fields: {', '.join(missing_or_empty)}.\n\n"
                        f"📄 Please check whether the uploaded PDF is a valid **ESG report** containing identifiable company, industry, and year information."
                    )
                    # st.code(result)


            except Exception as e:
                st.warning(f"⚠️ Failed to parse Gemini output as JSON: {e}")
                st.code(result)

        # Clear button
        if "pdf_text" in st.session_state:
            if st.button("🗑️ Clear PDF"):
                del st.session_state["pdf_text"]
                st.session_state.pop("pdf_info", None)
                st.session_state.pop("pdf_language", None)
                st.session_state["file_uploader_key"] = str(time.time())  # 重新生成 key
                st.rerun()

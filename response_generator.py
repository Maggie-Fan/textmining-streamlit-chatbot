import re
import streamlit as st
from pdf_context import get_pdf_context
from qa_utils.Word2vec import view_2d, view_3d, cbow_skipgram
from esg_analysis import analyze_esg_from_pdf
import pandas as pd
import sqlite3
from qa_utils.twse_scraper import write_twse_example_to_db



# 匯入 Gemini Agent，並確認 key 是否存在
try:
    from agents.gemini_agent import chat_with_gemini
    GEMINI_ENABLED = bool(st.secrets.get("GEMINI_API_KEY", None))
    # print(f"GEMINI_ENABLED: {GEMINI_ENABLED}")
except Exception as e:
    GEMINI_ENABLED = False
    print(f"❌ Failed to import Gemini agent: {e}")
    st.warning(f"Gemini Agent not available: {e}")

def generate_response(prompt):
    pdf_context = get_pdf_context()
    original_prompt = prompt
    prompt = prompt.strip().lower()

    # 可執行 Word2Vec 子模組對應表
    vector_semantics_tasks = {
        "view2d": (view_2d.run, "🧭 2D Word Embedding Visualization is ready to run. Please provide your input sentences in the UI."),
        "view3d": (view_3d.run, "📡 3D Word Embedding Visualization is ready to run."),
        "cbow": (cbow_skipgram.run, "📘 CBOW model is ready to run."),
        "skipgram": (cbow_skipgram.run, "⚙️ Skip-gram model is ready to run."),
    }

    prompt_lists = [
        "show content",
        "clustering analysis",
        "esg analysis",
        "vector semantics - word2vec",
        "view2d",
        "view3d",
        "cbow",
        "skipgram",
        "negative sampling",
        "show session state", # for debug
    ]

    # for debug
    if prompt == "show session state":
        # st.write("🔍 Current session_state:")
        st.json(st.session_state)
        return f"🔍 Current session_state:"

    # 指令：PDF / Word2Vec / 分析模組
    if prompt in prompt_lists or "show pdf page" in prompt:
        if pdf_context:
            if prompt == "show content":
                return f"""
                🤖 Here's what I found from the uploaded PDF:\n
                {pdf_context}
                ----------------------------------\n
                """

            elif "show pdf page" in prompt:
                match = re.search(r"show pdf page (\d+)", prompt)
                if match:
                    page_number = int(match.group(1))
                    return get_pdf_context(page=page_number)
                else:
                    return "⚠️ Please specify the page number, e.g., `Show PDF page 2`."

            elif prompt == "clustering analysis":
                return f"📊 Working on clustering analysis..."

            elif prompt == "esg analysis":
                # return f"🌱 Working on ESG analysis..."
                return analyze_esg_from_pdf()

        else:
            if prompt == "vector semantics - word2vec":
                return (
                    "📊 You're now in the **Vector Semantics - Word2Vec** module!\n\n"
                    "You can enter one of the following prompts to run specific visualizations:\n"
                    "- `view2d` → 2D Word Embedding Visualization\n"
                    "- `view3d` → 3D Word Embedding Visualization\n"
                    "- `cbow` → CBOW model explanation or demo\n"
                    "- `skipgram` → Skip-gram model explanation or demo\n"
                    "- `negative sampling` → Negative Sampling demo\n\n"
                    "💡 For example, type `view2d` to run the 2D vector space visualization."
                )

            elif prompt in vector_semantics_tasks:
                st.session_state["pending_vector_task"], message = vector_semantics_tasks[prompt]
                return message

            else:
                return f"📂 Please upload a PDF file to get context."

    # if prompt == "show esg report db table":
        st.subheader("📊 ESG_Report Interactive Table")

        # 觸發爬蟲資料更新按鈕
        if st.button("📥 Update ESG DB from TWSE"):
            write_twse_example_to_db()
            st.success("✅ TWSE ESG 資料已寫入 Company / Industry Table")

        # 讀取資料
        with sqlite3.connect("db/esg_reports.db") as conn:
            df = pd.read_sql_query("""
                SELECT 
                    ESG_Report.report_id,
                    Company.company_name_zh AS company,
                    Industry.industry_name_zh AS industry,
                    ESG_Report.report_year,
                    ESG_Report.content
                FROM ESG_Report
                JOIN Company ON ESG_Report.company_id = Company.company_id
                JOIN Industry ON Company.industry_id = Industry.industry_id
                ORDER BY report_year DESC
            """, conn)

        # 選單過濾條件
        with st.expander("🔍 Filter Conditions", expanded=False):
            companies = sorted(df["company"].unique())
            industries = sorted(df["industry"].unique())
            years = sorted(df["report_year"].unique().astype(str))

            selected_company = st.multiselect("Company", ["All"] + companies, default=["All"])
            selected_industry = st.multiselect("Industry", ["All"] + industries, default=["All"])
            selected_year = st.multiselect("Report Year", ["All"] + years, default=["All"])

            if "All" not in selected_company:
                df = df[df["company"].isin(selected_company)]
            if "All" not in selected_industry:
                df = df[df["industry"].isin(selected_industry)]
            if "All" not in selected_year:
                df = df[df["report_year"].astype(str).isin(selected_year)]

        # 每一列都可以刪除
        st.markdown("### 🗑️ Delete Rows")

        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 4, 1])
            with col1:
                st.markdown(f"**Company:** {row['company']}")
            with col2:
                st.markdown(f"**Industry:** {row['industry']}")
            with col3:
                st.markdown(f"**Year:** {row['report_year']}")
            with col4:
                st.markdown(f"**ID:** {row['report_id']}")
            with col5:
                st.markdown(f"**Content:** {row['content'][:50]}...")  # truncate
            with col6:
                if st.button("❌", key=f"del_{row['report_id']}"):
                    with sqlite3.connect("db/esg_reports.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM ESG_Report WHERE report_id = ?", (row['report_id'],))
                        conn.commit()
                    st.success(f"🗑️ Deleted report ID {row['report_id']}")
                    st.rerun()

        return f"🧾 Showing {len(df)} ESG report records."
  
    # if prompt == "show esg report db table":
    #     from ui_utils.esg_reports_section import show_esg_report_table
    #     show_esg_report_table()
    #     return "📄 ESG Report Table displayed."
    if prompt == "show esg report db table":
        try:
            from ui_utils.esg_reports_section import show_esg_report_table
            show_esg_report_table()
            return "📄 ESG Report Table displayed."
        except ImportError as e:
            st.error(f"❌ Unable to show ESG report table: {e}")
            return "❌ Error: ESG report table function not found."

    # 非內建指令：使用 Gemini（如果啟用）
    elif GEMINI_ENABLED:
        with st.spinner("🤖 Gemini is thinking..."):
            return chat_with_gemini(original_prompt)

    else:
        print(GEMINI_ENABLED)

    # fallback 提示
    return (
        "📝 It looks like your prompt might not match the expected operations.\n\n"
        "💡 Try entering prompts like:\n"
        "- `Show content`\n"
        "- `Show pdf page <num>`\n"
        "- `Vector Semantics - Word2vec`\n"
        "- `Clustering analysis`\n"
        "- `ESG analysis`\n\n"
        "📄 Also, make sure you've uploaded a PDF file first!"
    )

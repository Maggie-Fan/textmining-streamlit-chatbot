from pdf_context import get_pdf_context
from agents.gemini_agent import chat_with_gemini
import streamlit as st
import re

def clean_chinese_markdown_spacing(text):
    text = text.replace("。\n", "。\n\n").replace("。", "。\n")
    text = re.sub(r"(?<!\n)- ", r"\n- ", text)
    return text

def analyze_esg_from_pdf():
    pdf_text = get_pdf_context(page="all")
    language = st.session_state.get("pdf_language", "english")

    if language == "chinese":
        prompt = (
            "你是一位專業的 ESG 報告分析師。\n\n"
            "請根據下方企業永續報告的內容，分別針對三個構面進行**批判性分析與重點整理**：\n"
            "1. 🌿 環境（Environmental）：與氣候變遷、能源、碳排、資源使用、生物多樣性有關的政策與行動\n"
            "2. 🤝 社會（Social）：涉及員工、社區、客戶、教育、多元共融、員工照顧等人際互動面向\n"
            "3. 🏛️ 治理（Governance）：與公司治理、風險管理、董事會、資訊安全、政策制定有關的議題\n"
            "請針對每個構面提供以下資訊：\n"
            "1. **核心策略**：一句話描述該構面的整體方向與目標\n"
            "2. **關鍵行動**：條列 3~5 項具體實踐作法或措施（避免空泛口號）\n"
            "3. **待改善處**：指出內容中的缺口、模糊處、缺乏量化指標、或過於籠統的部分（如無則寫 N/A）\n\n"
            "請用下列 Markdown 格式回應：\n"
            "### 🌿 環境（Environmental）\n"
            "**核心策略**：...\n"
            "**關鍵行動**：\n"
            "- ...\n"
            "**待改善處**：\n"
            "- ...\n\n"
            "（依序接續列出 社會 與 治理）\n\n"
            "⚠️ 請避免同一項目出現在多個構面，需根據內容判斷最合適分類。"
            "📄 報告內容如下：\n"
            f"{pdf_text}"
        )
    else:
        prompt = (
            "You are a professional ESG report analyst.\n\n"
            "Please critically analyze the following ESG report and summarize findings into the **three official ESG dimensions**:\n"
            "1. 🌿 Environmental (E): climate change, energy, emissions, biodiversity, etc.\n"
            "2. 🤝 Social (S): employee relations, diversity, education, customer/community engagement\n"
            "3. 🏛️ Governance (G): board structure, transparency, cybersecurity, risk management, ethics\n\n"
            "For each of the three sections, return:\n"
            "- **Core Strategy**: One concise sentence that summarizes the main goal or policy direction\n"
            "- **Key Actions**: A bullet list (3–5 items) of clear, concrete actions or programs the company has taken.\n"
            "- **Areas for Improvement**: Any vague statements, missing indicators, repetitive info, or lack of quantitative support (write 'N/A' if none)\n\n"
            "⚠️ Avoid overlaps — each point should appear in only one category.\n"
            "⚠️ If applicable, comment on whether the actions include measurable KPIs, clear timelines, or observable outcomes — but also include meaningful qualitative efforts.\n"
            "📄 ESG Report Content:\n"
            f"{pdf_text}"
        )

    with st.spinner("🤖 Gemini is reading and analyzing..."):
        result = chat_with_gemini(prompt)

    if language == "chinese":
        result = clean_chinese_markdown_spacing(result)

    return result
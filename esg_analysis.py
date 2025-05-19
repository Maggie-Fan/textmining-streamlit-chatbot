from pdf_context import get_pdf_context, preprocess_pdf_sentences
from agents.gemini_agent import chat_with_gemini
import streamlit as st
import re
import os
import nltk
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
from matplotlib import font_manager as fm
from ckip_transformers.nlp import CkipPosTagger

# 若部署在 Streamlit Cloud，自動加載這個路徑
nltk_data_path = "/home/appuser/.nltk_data"
if os.path.exists(nltk_data_path):
    nltk.data.path.append(nltk_data_path)

# 自動下載 NLTK 所需資源（避免雲端錯誤）
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("taggers/averaged_perceptron_tagger")
except LookupError:
    nltk.download("averaged_perceptron_tagger")

from nltk import pos_tag

def clean_chinese_markdown_spacing(text):
    text = text.replace("。\n", "。\n\n").replace("。", "。\n")
    text = re.sub(r"(?<!\n)- ", r"\n- ", text)
    return text

def analyze_esg_from_pdf():
    pdf_text = get_pdf_context(page="all")
    # language = st.session_state.get("pdf_language", "english")
    lang_setting = st.session_state.get("lang_setting", "English")

    prompt = (
        "You are a professional ESG report analyst.\n\n"
        f"⚠️ Please output in {lang_setting}\n"
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
        "⚠️ If the below content is not identified as a ESG report content, you dont have to analyze it, but gently remind users to upload ESG report.\n"
        "📄 ESG Report Content:\n"
        f"{pdf_text}\n"
    )

    with st.spinner("🤖 Gemini is reading and analyzing..."):
        result = chat_with_gemini(prompt, restrict = False)

    if lang_setting == "繁體中文":
        result = clean_chinese_markdown_spacing(result)

    # show_wordcloud()
    return result

def get_english_noun_adj_tokens(tokens):
    pos_tags = pos_tag(tokens)
    filtered = [word for word, pos in pos_tags if pos.startswith("NN") or pos.startswith("JJ")]
    return filtered

def show_wordcloud():
    if "pdf_text" not in st.session_state:
        st.warning("⚠️ Please upload a PDF for plotting.")
        return

    pdf_text = get_pdf_context(page="all")
    language = st.session_state.get("pdf_language", "english")

    # --- 圖的標題（從 session 中撈公司資訊） ---
    pdf_info = st.session_state.get("pdf_info", {})
    company = pdf_info.get("company_name", "Unknown Company")
    industry = pdf_info.get("industry", "Unknown Industry")
    year = pdf_info.get("report_year", "Unknown Year")
    full_title = f"{company} ({year})\n{industry} Sector"

    def plot_wordcloud(word_freq, title):
        FONT_PATH = os.path.join("fonts", "TaipeiSansTCBeta-Regular.ttf")
        try:
            wc = WordCloud(
                font_path=FONT_PATH if language == "chinese" else None,
                width=800,
                height=500,
                background_color="white"
            ).generate_from_frequencies(word_freq)
        except Exception as e:
            wc = WordCloud(width=800, height=500, background_color="white").generate_from_frequencies(word_freq)

        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')

        if language == "chinese":
            font_prop = fm.FontProperties(fname=FONT_PATH)
            ax.set_title(title, fontsize=10, fontproperties=font_prop)
        else:
            ax.set_title(title, fontsize=10)

        ax.axis("off")
        st.pyplot(fig)

    # --- TF-IDF + POS ---
    sentences = preprocess_pdf_sentences(pdf_text, tokenize=True)
    if not sentences:
        st.warning("⚠️ No valid sentences extracted.")
        return

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(sentences)
    scores = tfidf_matrix.sum(axis=0).A1
    tokens = tfidf.get_feature_names_out()
    tfidf_dict = dict(zip(tokens, scores))

    if language == "chinese":
        words = list(tfidf_dict.keys())
        pos_tagger = CkipPosTagger()
        pos_tags = pos_tagger([words])[0]
        valid_pos_prefix = ("N", "V", "A")
        filtered = {
            w: tfidf_dict[w]
            for w, pos in zip(words, pos_tags)
            if any(pos.startswith(p) for p in valid_pos_prefix)
        }
    else:
        filtered = tfidf_dict.copy()
        filtered = {w: tfidf_dict[w] for w in get_english_noun_adj_tokens(list(tfidf_dict.keys()))}

    # --- 圖顯示邏輯 ---
    mode = st.session_state.get("wordcloud_mode", None)

    if mode == "main":
        st.subheader("☁️ Word Cloud (with POS)")
        plot_wordcloud(filtered, title=full_title)

    elif mode == "esg":
        st.subheader("ESG Dimensions Word Clouds")

        # 隨機模擬分類
        e_words, s_words, g_words = {}, {}, {}
        for i, (word, score) in enumerate(filtered.items()):
            r = i % 3
            if r == 0:
                e_words[word] = score
            elif r == 1:
                s_words[word] = score
            else:
                g_words[word] = score

        st.markdown("#### 🌿 Environmental")
        plot_wordcloud(e_words, title="Environmental Word Cloud")

        st.markdown("#### 🤝 Social")
        plot_wordcloud(s_words, title="Social Word Cloud")

        st.markdown("#### 🏛️ Governance")
        plot_wordcloud(g_words, title="Governance Word Cloud")

    # --- 控制按鈕區塊 ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Show Word Cloud"):
            st.session_state["wordcloud_mode"] = "main"
            st.rerun()
    with col2:
        if st.button("📥 E / S / G plot"):
            st.session_state["wordcloud_mode"] = "esg"
            st.rerun()
    with col3:
        if st.button("🗑️ Clear ESG wordcloud"):
            st.session_state["wordcloud_mode"] = None
            st.rerun()
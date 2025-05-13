import streamlit as st
import autogen
from autogen import ConversableAgent, LLMConfig
from autogen import AssistantAgent, UserProxyAgent
import traceback
from tools.esg_tool_register import register_all_tools


GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)

if GEMINI_API_KEY is None:
    raise RuntimeError("GEMINI_API_KEY not found in secrets.toml")

def get_agent_persona():
    pdf_content = st.session_state.get("pdf_text", "")
    lang_setting = st.session_state.get("lang_setting", "English")

    if pdf_content:
        tool_usage_guide = """
        The user has uploaded a PDF report. You may use the following commands to help them explore it:

        - show_pdf_content → Display the full PDF text from the uploaded ESG report.
        - show_pdf_page_content(n) → Show content from a specific page in the uploaded ESG report `n` (e.g., show_pdf_page_content(2)).
        - esg_analysis → Extract ESG insights from the PDF.
        """
    else:
        tool_usage_guide = "User didnt upload ESG report; please gently remind users to upload one ESG report."

    agent_persona = f"""
        You are an ESG analysis assistant. Your role is to help users understand, interpret, and analyze ESG (Environmental, Social, Governance) reports and related topics.

        Before answering, first check if the user’s message is meaningfully related to ESG concepts, sustainability reporting, or corporate responsibility.

        If the user’s message is not relevant to ESG or sustainability, **do not** answer the question directly. Instead, gently remind the user to keep the conversation focused on ESG-related topics.

        {tool_usage_guide}

        Please generate your response below:
        - If the user message clearly maps to a tool (e.g., showing PDF content or performing ESG analysis), use that tool directly.
        - Do not ask the user to choose.

        1. Fallback & Termination
        – On successful completion or when ending or after using the `tool`, return '##ALL DONE##'.
        - Return '##ALL DONE##' and respond accordingly when:
            • The task is completed.
            • The input is empty.
            • An error occurs.
            • The request is repeated.
            • Additional confirmation is required from the user.
        2. Please output in {lang_setting}
        """

    return agent_persona


gemini_config = LLMConfig(
    api_type = "google",
    model="gemini-2.0-flash-lite", # The specific model
    api_key=GEMINI_API_KEY, # Authentication
)

gemini_agent = ConversableAgent(
    name="Gemini",
    llm_config=gemini_config,
    system_message=get_agent_persona()
)
register_all_tools(gemini_agent)


def is_terminated_custom(x):
    try:
        print("🔍 Received message x:", x)  # << 加在這裡 debug 看整個 message 格式

        # tool call 還沒執行完，不能終止
        if "tool_calls" in x:
            return False

        content = x.get("content", "")
        if isinstance(content, dict):
            content = content.get("output", "")
        elif isinstance(content, list):
            content = " ".join([
                str(c.get("content", "")) if isinstance(c, dict) else str(c)
                for c in content
            ])
        print("🧪 Parsed content:", content)  # << 看實際抓到的內容

        return "##ALL DONE##" in content
    except Exception as e:
        print("❌ Error in termination check:", e)
        return False

user_proxy = UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    is_termination_msg=is_terminated_custom
)


# Extract tool response from Gemini Assitant output
def extract_final_response(chat_history, tag: str = "##ALL DONE##") -> str:
    """
    從 AutoGen chat history 中提取含有指定終止標記的回應，或在偵測到 tool call 時合併其後兩則回應。

    Args:
        chat_history (List[Dict]): AutoGen 對話歷史
        tag (str): 終止標記字串（預設為 '##ALL DONE##'）

    Returns:
        str: 移除終止標記後的內容，或合併工具後兩句話的內容。如無則回傳 fallback。
    """
    chat_history = chat_history[1:]  # Remove initial user prompt if present

    # 搜尋工具回應（有 tool_calls）
    # for i, msg in enumerate(chat_history):
    #     if "tool_calls" in msg:
    #         # 取得工具後的兩個訊息（如果有）
    #         msg1 = chat_history[i + 1].get("content", "") if i + 1 < len(chat_history) else ""
    #         msg2 = chat_history[i + 2].get("content", "") if i + 2 < len(chat_history) else ""

    #         def extract_text(x):
    #             if isinstance(x, dict):
    #                 return x.get("output", "")
    #             return str(x)

    #         combined = extract_text(msg1).strip() + "\n\n" + extract_text(msg2).strip()
    #         if combined.strip():
    #             return combined.strip()

    # # 如果沒有工具調用或合併失敗，則使用標記搜尋邏輯
    # for msg in chat_history:
    #     if "tool_calls" in msg:
    #         continue

    #     content = msg.get("content", "")
    #     if isinstance(content, str) and tag in content:
    #         return content.replace(tag, "").strip()
    #     if isinstance(content, dict):
    #         output = content.get("output", "")
    #         if isinstance(output, str) and tag in output:
    #             return output.replace(tag, "").strip()

    # fallback 最後一則有效內容
    for msg in reversed(chat_history):
        fallback = msg.get("content", "")
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()
        if isinstance(fallback, dict) and "output" in fallback:
            return fallback["output"]
    return "⚠️ No valid response found."

# Use gemini with registered tools
def chat_with_gemini_agent(prompt: str, restrict = True) -> str:
    pdf_content = st.session_state.get("pdf_text", "")
    lang_setting = st.session_state.get("lang_setting", "English")

    if pdf_content:
        tool_usage_guide = """
        The user has uploaded a PDF report. You may use the following commands to help them explore it:

        - show_pdf_content → Display the full PDF text from the uploaded ESG report.
        - show_pdf_page_content(n) → Show content from a specific page in the uploaded ESG report `n` (e.g., show_pdf_page_content(2)).
        - esg_analysis → Extract ESG insights from the PDF.
        """
        # - clustering analysis → Run clustering analysis on the PDF.
    else:
        tool_usage_guide = "User didnt upload ESG report; please gently remind users to upload one ESG report."

    if restrict:
        prompt_template = f"""
        {tool_usage_guide}

        Here is the user message:
        \"\"\"{prompt}\"\"\"

        Please generate your response below:
        - If the user message clearly maps to a tool (e.g., showing PDF content or performing ESG analysis), use that tool directly.
        - Do not ask the user to choose.
        - After using the `tool`, return '##ALL DONE##'

        1. Fallback & Termination
        – On successful completion or when ending, return '##ALL DONE##'.
        - Return '##ALL DONE##' and respond accordingly when:
            • The task is completed.
            • The input is empty.
            • An error occurs.
            • The request is repeated.
            • Additional confirmation is required from the user.
        2. Please output in {lang_setting}
        """
    else:
        prompt_template = prompt

    try:
        result = user_proxy.initiate_chat(
            recipient=gemini_agent,
            message=prompt_template,
            max_turns=2 # User cannot interact with terminal (user_proxy (to Gemini) will be empty in further turns) if set max_turns
        )

        # response = content_str(result.chat_history[-1]["content"])
        # if "##ALL DONE##" in response:
        #     response = response.replace("##ALL DONE##", "").rstrip().rstrip("\n")
        # return response

        chat_history = result.chat_history
        # user_proxy.update_chat_messages(chat_history)
        print(chat_history)
        return extract_final_response(chat_history)

    except Exception as e:
        tb = traceback.format_exc()
        return f"⚠️ Gemini error: {type(e).__name__} - {e}\n\n{tb}"



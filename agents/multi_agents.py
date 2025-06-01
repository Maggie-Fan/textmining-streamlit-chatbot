import streamlit as st
import autogen
from autogen import ConversableAgent, LLMConfig, UserProxyAgent
import traceback
from tools.esg_tool_register import register_all_tools

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
if GEMINI_API_KEY is None:
    raise RuntimeError("GEMINI_API_KEY not found in secrets.toml")

gemini_config = LLMConfig(
    api_type="google",
    model="gemini-2.0-flash-lite",
    api_key=GEMINI_API_KEY,
)

def get_agent_persona(role_persona):
    pdf_content = st.session_state.get("pdf_text", "")
    lang_setting = st.session_state.get("lang_setting", "English")

    if pdf_content:
        tool_usage_guide = """
        The user has uploaded a PDF report. You may use:
        - show_pdf_content
        - show_pdf_page_content(n)
        - esg_analysis
        """
    else:
        tool_usage_guide = "User didn't upload ESG report. Please remind them."

    if role_persona == "reader_persona":
        role_desc = """
        You are an assistant who extracts text from ESG PDFs. Only use `show_pdf_content` or `show_pdf_page_content(n)`.
        Do not analyze ESG content.
        """
    elif role_persona == "student_persona":
        role_desc = """
        You analyze ESG reports and summarize insights. Send your findings to the teacher for review. Do not finalize answers.
        """
    elif role_persona == "teacher_persona":
        role_desc = """
        You are an ESG expert. Review the student's work. You may use `esg_analysis` if needed. Conclude with '##ALL DONE##'.
        """
    else:
        role_desc = ""

    return f"""
    {role_desc}
    {tool_usage_guide}
    Output in {lang_setting}.
    """

def is_terminated_custom(x):
    try:
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
        return "##ALL DONE##" in content
    except Exception:
        return False

with gemini_config:
    reader_agent = ConversableAgent(
        name="Reader_Agent",
        llm_config=gemini_config,
        system_message=get_agent_persona("reader_persona")
    )

    student_agent = ConversableAgent(
        name="Student_Agent",
        llm_config=gemini_config,
        system_message=get_agent_persona("student_persona")
    )

    teacher_agent = ConversableAgent(
        name="Teacher_Agent",
        llm_config=gemini_config,
        system_message=get_agent_persona("teacher_persona"),
        is_termination_msg=is_terminated_custom,
        human_input_mode="NEVER",
    )

register_all_tools(caller_agent=student_agent, executor_agent=reader_agent)
register_all_tools(caller_agent=student_agent, executor_agent=teacher_agent)
register_all_tools(caller_agent=reader_agent, executor_agent=teacher_agent)

user_proxy = UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    is_termination_msg=is_terminated_custom
)

def extract_final_response(chat_history, tag: str = "##ALL DONE##") -> str:
    chat_history = chat_history[1:]
    for i, msg in enumerate(chat_history):
        if "tool_calls" in msg:
            msg1 = chat_history[i + 1].get("content", "") if i + 1 < len(chat_history) else ""
            msg2 = chat_history[i + 2].get("content", "") if i + 2 < len(chat_history) else ""
            def extract_text(x):
                if isinstance(x, dict):
                    return x.get("output", "")
                return str(x)
            combined = extract_text(msg1).strip() + "\n\n" + extract_text(msg2).strip()
            if combined.strip():
                return combined.strip()
    for msg in chat_history:
        if "tool_calls" in msg:
            continue
        content = msg.get("content", "")
        if isinstance(content, str) and tag in content:
            return content.replace(tag, "").strip()
        if isinstance(content, dict):
            output = content.get("output", "")
            if isinstance(output, str) and tag in output:
                return output.replace(tag, "").strip()
    for msg in reversed(chat_history):
        fallback = msg.get("content", "")
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()
        if isinstance(fallback, dict) and "output" in fallback:
            return fallback["output"]
    return "⚠️ No valid response found."

def chat_with_three_gemini_agents(prompt: str) -> str:
    try:
        result = student_agent.initiate_chat(
            teacher_agent,
            message=prompt,
            recipient=reader_agent,
            max_turns=6,
            summary_method="reflection_with_llm"
        )
        chat_history = result.chat_history
        response = extract_final_response(chat_history)
        if "##ALL DONE##" in response:
            return response.replace("##ALL DONE##", "").rstrip().rstrip("\n")
        return response
    except Exception as e:
        tb = traceback.format_exc()
        return f"⚠️ Gemini error: {type(e).__name__} - {e}\n\n{tb}"



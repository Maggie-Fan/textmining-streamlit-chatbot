import streamlit as st
import autogen
from autogen import ConversableAgent, LLMConfig
from autogen import AssistantAgent, UserProxyAgent
from autogen.code_utils import content_str
import traceback

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)

if GEMINI_API_KEY is None:
    raise RuntimeError("GEMINI_API_KEY not found in secrets.toml")

gemini_config = LLMConfig(
    api_type = "google",
    model="gemini-2.0-flash-lite", # The specific model
    api_key=GEMINI_API_KEY, # Authentication
)

gemini_agent = ConversableAgent(
    name="Gemini",
    llm_config=gemini_config,
    # max_consecutive_auto_reply=3
)

# assistant = AssistantAgent(
#     "assistant",
#     llm_config=gemini_config,
#     max_consecutive_auto_reply=3
# )

user_proxy = UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
    is_termination_msg=lambda x: content_str(x.get("content")).find("ALL DONE") >= 0,
)

def chat_with_gemini(prompt: str) -> str:
    prompt_template = f"{prompt}"

    try:
        message = {"role": "user", "content": prompt_template}
        reply = gemini_agent.generate_reply(messages=[message])

        if not reply or "content" not in reply:
            return "⚠️ Gemini did not return a valid reply."

        return content_str(reply["content"])

        # result = user_proxy.initiate_chat(
        #     # recipient=assistant,
        #     recipient=gemini_agent,
        #     message=prompt_template
        # )

        # response = result.chat_history
        # return response

    except Exception as e:
        tb = traceback.format_exc()
        return f"⚠️ Gemini error: {type(e).__name__} - {e}\n\n{tb}"
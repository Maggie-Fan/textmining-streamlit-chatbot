# 💬 Chatbot template

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

    - Note (commands for window users): if numpy installed with error:
      - Use python version == 3.10 and open venv to run 3.10 version
      ```
      $ py -3.10 -m venv .venv
      ```
      -  Run powershell as administrator and get authorized for venv-activation
      ```
      # Run in powershell as administrator
      $ Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
      ```

      ```
      # Run in terminal
      $ .venv\Scripts\activate
      ```

      - Deactivate to quit
      ```
      $ deactivate
      ```


2. Run the app (in venv)
   - Activate venv if needed to run in venv

   ```
   $ streamlit run streamlit_app.py
   ```

   - Press ctrl+C to stop the app

### Note: About Gemini agent
   - Apply for Gemini API key: https://aistudio.google.com/app/apikey
   - About API quota: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - About autogen using Gemini: https://microsoft.github.io/autogen/0.2/docs/topics/non-openai-models/cloud-gemini_vertexai/

See deployed:
- Production(ckip-allowed): https://brian-textmining-chatbot-finalproject.streamlit.app/
- Test: https://brian-textmining-chatbot.streamlit.app/

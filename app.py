import streamlit as st
import requests

st.title("Telegram Token Test")

token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")

st.write("Secret exists:", bool(token))
st.write("Token length:", len(token))

if token:
    response = requests.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=10
    )

    st.write("HTTP Status:", response.status_code)
    st.json(response.json())
else:
    st.error("TELEGRAM_BOT_TOKEN not found")
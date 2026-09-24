import streamlit as st
import requests

st.set_page_config(
    page_title="Telegram Website",
    page_icon="📱",
    layout="wide"
)

st.title("📱 My Telegram Website")

TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

url = f"https://api.telegram.org/bot{TOKEN}/getMe"

try:
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("ok"):
        bot = data["result"]

        st.success("✅ Telegram Bot Connected!")

        st.write("**Bot Name:**", bot.get("first_name"))
        st.write("**Bot Username:**", "@" + bot.get("username", ""))

    else:
        st.error("❌ Telegram connection failed")
        st.json(data)

except Exception as e:
    st.error("❌ Error")
    st.write(str(e))
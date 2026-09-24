import streamlit as st
import requests

# ============================================================
# 1. PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="My Telegram Website",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# 2. TELEGRAM BOT TOKEN
# ============================================================

TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

API_URL = f"https://api.telegram.org/bot{TOKEN}"

# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .stApp {
        background: #0b0b0b;
        color: white;
    }

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .subtitle {
        text-align: center;
        color: #aaaaaa;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .status-box {
        padding: 18px;
        border-radius: 12px;
        background: #151515;
        border: 1px solid #292929;
        margin-bottom: 20px;
    }

    .message-box {
        background: #151515;
        border: 1px solid #292929;
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
    }

    .message-title {
        font-size: 20px;
        font-weight: 700;
    }

    .message-text {
        color: #cccccc;
        font-size: 15px;
        line-height: 1.6;
    }

    .small-text {
        color: #777777;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 4. HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📱 My Telegram Website</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Private Telegram Channel Dashboard</div>',
    unsafe_allow_html=True
)

# ============================================================
# 5. TELEGRAM BOT TEST
# ============================================================

try:

    response = requests.get(
        f"{API_URL}/getMe",
        timeout=15
    )

    data = response.json()

except Exception as e:

    st.error("❌ Telegram API connection error")
    st.code(str(e))
    st.stop()

# ============================================================
# 6. BOT STATUS
# ============================================================

if not data.get("ok"):

    st.error("❌ Telegram Bot Authentication Failed")

    st.json(data)

    st.stop()

bot = data["result"]

st.markdown(
    f"""
    <div class="status-box">
        <h3>🟢 Telegram Connected</h3>
        <p><b>Bot Name:</b> {bot.get("first_name", "Unknown")}</p>
        <p><b>Username:</b> @{bot.get("username", "Unknown")}</p>
        <p class="small-text">
            Telegram Bot API connection is working successfully.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 7. GET UPDATES
# ============================================================

st.subheader("📨 Telegram Updates")

try:

    updates_response = requests.get(
        f"{API_URL}/getUpdates",
        params={
            "limit": 100,
            "timeout": 5
        },
        timeout=15
    )

    updates_data = updates_response.json()

except Exception as e:

    st.error("❌ Could not retrieve Telegram updates")
    st.code(str(e))
    st.stop()

# ============================================================
# 8. DISPLAY UPDATES
# ============================================================

if not updates_data.get("ok"):

    st.error("❌ Telegram returned an error")

    st.json(updates_data)

else:

    updates = updates_data.get("result", [])

    if not updates:

        st.info(
            "ℹ️ Abhi koi Telegram update nahi mila."
        )

        st.write(
            "Apne Telegram channel me ek naya test post/message "
            "bhejo aur phir neeche Refresh button dabao."
        )

    else:

        st.success(
            f"✅ {len(updates)} update(s) received"
        )

        for update in reversed(updates):

            # ------------------------------------------------
            # CHANNEL POST
            # ------------------------------------------------

            if "channel_post" in update:

                post = update["channel_post"]

                chat = post.get("chat", {})

                channel_title = chat.get(
                    "title",
                    "Unknown Channel"
                )

                channel_id = chat.get(
                    "id",
                    "Unknown"
                )

                text = post.get(
                    "text",
                    ""
                )

                caption = post.get(
                    "caption",
                    ""
                )

                message_text = text or caption

                st.markdown(
                    f"""
                    <div class="message-box">

                        <div class="message-title">
                            📢 {channel_title}
                        </div>

                        <p>
                            <b>Channel ID:</b> {channel_id}
                        </p>

                        <p>
                            <b>Message ID:</b> {post.get("message_id")}
                        </p>

                        <div class="message-text">
                            {message_text if message_text else "📎 Media/File message"}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # --------------------------------------------
                # PHOTO
                # --------------------------------------------

                if "photo" in post:

                    photos = post["photo"]

                    if photos:

                        photo = photos[-1]

                        st.info(
                            f"🖼️ Photo detected | "
                            f"File ID: {photo.get('file_id')}"
                        )

                # --------------------------------------------
                # VIDEO
                # --------------------------------------------

                if "video" in post:

                    video = post["video"]

                    st.info(
                        f"🎬 Video detected | "
                        f"File ID: {video.get('file_id')}"
                    )

                # --------------------------------------------
                # DOCUMENT
                # --------------------------------------------

                if "document" in post:

                    document = post["document"]

                    st.info(
                        f"📄 Document detected | "
                        f"File: {document.get('file_name', 'Unknown')}"
                    )

                # --------------------------------------------
                # AUDIO
                # --------------------------------------------

                if "audio" in post:

                    audio = post["audio"]

                    st.info(
                        f"🎵 Audio detected | "
                        f"File ID: {audio.get('file_id')}"
                    )

            # ------------------------------------------------
            # OTHER UPDATE TYPES
            # ------------------------------------------------

            else:

                st.markdown(
                    """
                    <div class="message-box">
                        <b>ℹ️ Other Telegram update detected</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ============================================================
# 9. REFRESH BUTTON
# ============================================================

st.divider()

if st.button(
    "🔄 Refresh Telegram Updates",
    use_container_width=True
):

    st.rerun()

# ============================================================
# 10. FOOTER
# ============================================================

st.markdown(
    """
    <br>
    <p style="
        text-align:center;
        color:#666;
        font-size:13px;
    ">
        Telegram → Bot API → Streamlit
    </p>
    """,
    unsafe_allow_html=True
)
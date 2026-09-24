import os
import tempfile
import asyncio
import hashlib

import streamlit as st
from telethon import TelegramClient
from telethon.errors import RPCError


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="My Telegram Website",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 2. CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #080808;
    color: white;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    margin-top: 15px;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #999;
    margin-bottom: 30px;
}

.channel-card {
    background: linear-gradient(145deg, #171717, #0d0d0d);
    border: 1px solid #292929;
    border-radius: 18px;
    padding: 22px;
    margin: 10px 0;
}

.channel-name {
    font-size: 24px;
    font-weight: 800;
}

.file-card {
    background: #141414;
    border: 1px solid #292929;
    border-radius: 15px;
    padding: 16px;
    margin: 8px 0;
}

.file-name {
    font-size: 17px;
    font-weight: 700;
}

.file-info {
    color: #888;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. SECRETS
# ============================================================

try:
    API_ID = int(st.secrets["TELEGRAM_API_ID"])
    API_HASH = st.secrets["TELEGRAM_API_HASH"]
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

except Exception:
    st.error("❌ Telegram Secrets missing.")

    st.code("""
TELEGRAM_API_ID = "YOUR_API_ID"
TELEGRAM_API_HASH = "YOUR_API_HASH"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
""")

    st.stop()


# ============================================================
# 4. TELEGRAM CLIENT
# ============================================================

SESSION_FILE = "telegram_streamlit_bot"

client = TelegramClient(
    SESSION_FILE,
    API_ID,
    API_HASH
)


# ============================================================
# 5. ASYNC HELPER
# ============================================================

def run_async(coro):
    """
    Run async Telegram operations safely.
    """
    try:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            new_loop = asyncio.new_event_loop()

            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        return loop.run_until_complete(coro)

    except RuntimeError:
        return asyncio.run(coro)


# ============================================================
# 6. CONNECT TELEGRAM
# ============================================================

async def connect_client():

    if not client.is_connected():
        await client.connect()

    if not await client.is_user_authorized():

        await client.start(
            bot_token=BOT_TOKEN
        )

    return True


try:

    run_async(connect_client())

except Exception as e:

    st.error("❌ Telegram connection failed")
    st.code(str(e))
    st.stop()


# ============================================================
# 7. GET CHANNELS
# ============================================================

async def get_channels():

    result = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        # Only channels
        if getattr(entity, "broadcast", False):

            result.append({
                "id": entity.id,
                "title": getattr(
                    entity,
                    "title",
                    "Unknown Channel"
                ),
                "username": getattr(
                    entity,
                    "username",
                    None
                )
            })

    return result


try:

    channels = run_async(
        get_channels()
    )

except Exception as e:

    st.error("❌ Channels load nahi ho paaye.")
    st.code(str(e))
    st.stop()


# ============================================================
# 8. HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📱 My Telegram Website</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your Private Telegram Channels'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# 9. CHANNEL CHECK
# ============================================================

if not channels:

    st.warning(
        "⚠️ Koi Telegram channel nahi mila."
    )

    st.info(
        "Check karo ki bot ko tumhare private channels "
        "me required access diya gaya hai."
    )

    st.stop()


# ============================================================
# 10. SIDEBAR
# ============================================================

st.sidebar.title("📁 Channels")

channel_names = [
    channel["title"]
    for channel in channels
]

selected_channel_name = st.sidebar.selectbox(
    "Select Channel",
    channel_names
)


selected_channel = next(
    channel
    for channel in channels
    if channel["title"] == selected_channel_name
)


# ============================================================
# 11. CHANNEL HEADER
# ============================================================

st.markdown(
    f"""
    <div class="channel-card">
        <div class="channel-name">
            📁 {selected_channel["title"]}
        </div>
        <div class="file-info">
            Telegram Channel
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 12. SEARCH
# ============================================================

search_text = st.text_input(
    "🔎 Search files/posts",
    placeholder="Movie, video, PDF, etc..."
)


# ============================================================
# 13. NUMBER OF POSTS
# ============================================================

limit = st.slider(
    "Number of posts to load",
    min_value=20,
    max_value=500,
    value=100,
    step=20
)


# ============================================================
# 14. MEDIA INFORMATION
# ============================================================

def get_media_type(message):

    if message.video:
        return "video"

    if message.document:

        mime = message.document.mime_type or ""

        if mime.startswith("video/"):
            return "video"

        if mime.startswith("audio/"):
            return "audio"

        if mime.startswith("image/"):
            return "image"

        return "document"

    if message.photo:
        return "photo"

    if message.audio:
        return "audio"

    return "text"


def get_file_name(message):

    if message.file:

        if message.file.name:
            return message.file.name

        if message.file.ext:
            return (
                f"telegram_file"
                f"{message.file.ext}"
            )

    media_type = get_media_type(message)

    return f"{media_type}_{message.id}"


# ============================================================
# 15. GET MESSAGES
# ============================================================

async def get_messages(
    channel_id,
    limit_value,
    search_value
):

    messages = []

    entity = await client.get_entity(
        channel_id
    )

    async for message in client.iter_messages(
        entity,
        limit=limit_value,
        search=search_value if search_value else None
    ):

        # Skip empty text-only posts
        if not message.media and not message.text:
            continue

        messages.append(message)

    return messages


try:

    messages = run_async(
        get_messages(
            selected_channel["id"],
            limit,
            search_text
        )
    )

except Exception as e:

    st.error("❌ Messages load nahi ho paaye.")
    st.code(str(e))
    st.stop()


# ============================================================
# 16. MESSAGE COUNT
# ============================================================

st.write(
    f"**{len(messages)} posts/files found**"
)

st.divider()


# ============================================================
# 17. DOWNLOAD MEDIA
# ============================================================

async def download_media(message):

    temp_dir = tempfile.gettempdir()

    unique = hashlib.md5(
        f"{message.chat_id}_{message.id}".encode()
    ).hexdigest()

    original_name = get_file_name(
        message
    )

    safe_name = (
        original_name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    file_path = os.path.join(
        temp_dir,
        f"{unique}_{safe_name}"
    )

    if os.path.exists(file_path):

        return file_path

    downloaded = await client.download_media(
        message,
        file=file_path
    )

    return downloaded


# ============================================================
# 18. DISPLAY MESSAGE
# ============================================================

for index, message in enumerate(messages):

    media_type = get_media_type(
        message
    )

    file_name = get_file_name(
        message
    )

    caption = (
        message.text
        or message.message
        or ""
    )

    with st.container():

        st.markdown(
            '<div class="file-card">',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        if media_type == "video":

            st.markdown(
                f"""
                <div class="file-name">
                    🎬 {file_name}
                </div>
                """,
                unsafe_allow_html=True
            )

            if caption:

                st.caption(
                    caption[:500]
                )

            if st.button(
                f"▶️ Play Video",
                key=f"video_{message.id}_{index}",
                use_container_width=True
            ):

                with st.spinner(
                    "⏳ Video loading..."
                ):

                    try:

                        video_path = run_async(
                            download_media(message)
                        )

                        if video_path:

                            st.video(
                                video_path
                            )

                    except Exception as e:

                        st.error(
                            "Video load failed."
                        )

                        st.code(
                            str(e)
                        )


        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        elif media_type == "photo":

            st.markdown(
                f"""
                <div class="file-name">
                    🖼️ Image
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "👁️ Open Image",
                key=f"photo_{message.id}_{index}",
                use_container_width=True
            ):

                with st.spinner(
                    "Loading image..."
                ):

                    try:

                        image_path = run_async(
                            download_media(message)
                        )

                        if image_path:

                            st.image(
                                image_path,
                                use_container_width=True
                            )

                    except Exception as e:

                        st.error(
                            "Image load failed."
                        )

                        st.code(
                            str(e)
                        )


        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        elif media_type == "audio":

            st.markdown(
                f"""
                <div class="file-name">
                    🎵 {file_name}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "▶️ Play Audio",
                key=f"audio_{message.id}_{index}",
                use_container_width=True
            ):

                with st.spinner(
                    "Loading audio..."
                ):

                    try:

                        audio_path = run_async(
                            download_media(message)
                        )

                        if audio_path:

                            st.audio(
                                audio_path
                            )

                    except Exception as e:

                        st.error(
                            "Audio load failed."
                        )

                        st.code(
                            str(e)
                        )


        # ----------------------------------------------------
        # DOCUMENT
        # ----------------------------------------------------

        elif media_type == "document":

            st.markdown(
                f"""
                <div class="file-name">
                    📄 {file_name}
                </div>
                """,
                unsafe_allow_html=True
            )

            if caption:

                st.caption(
                    caption[:500]
                )

            if st.button(
                "📂 Open File",
                key=f"doc_{message.id}_{index}",
                use_container_width=True
            ):

                with st.spinner(
                    "Loading file..."
                ):

                    try:

                        document_path = run_async(
                            download_media(message)
                        )

                        if document_path:

                            with open(
                                document_path,
                                "rb"
                            ) as f:

                                file_bytes = f.read()

                            st.download_button(
                                "⬇️ Download File",
                                data=file_bytes,
                                file_name=file_name,
                                key=f"download_{message.id}_{index}",
                                use_container_width=True
                            )

                            # PDF viewer
                            if file_name.lower().endswith(
                                ".pdf"
                            ):

                                import base64

                                encoded = base64.b64encode(
                                    file_bytes
                                ).decode()

                                pdf_display = f"""
                                <iframe
                                    src="data:application/pdf;base64,{encoded}"
                                    width="100%"
                                    height="700"
                                    style="border:none;">
                                </iframe>
                                """

                                st.markdown(
                                    pdf_display,
                                    unsafe_allow_html=True
                                )

                    except Exception as e:

                        st.error(
                            "File open failed."
                        )

                        st.code(
                            str(e)
                        )


        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        else:

            st.markdown(
                f"""
                <div class="file-name">
                    📝 Telegram Post
                </div>
                """,
                unsafe_allow_html=True
            )

            if caption:

                st.write(
                    caption
                )

        # ----------------------------------------------------
        # MESSAGE INFO
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="file-info">
                Message ID: {message.id}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# ============================================================
# 19. REFRESH
# ============================================================

st.divider()

if st.button(
    "🔄 Refresh",
    use_container_width=True
):

    st.rerun()


# ============================================================
# 20. FOOTER
# ============================================================

st.markdown(
    """
    <p style="
        text-align:center;
        color:#666;
        margin-top:30px;
    ">
        Powered by Telegram + Streamlit
    </p>
    """,
    unsafe_allow_html=True
)
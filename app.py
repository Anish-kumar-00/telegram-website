import os
import asyncio
import tempfile
import streamlit as st

from telethon import TelegramClient
from telethon.errors import RPCError


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="My Telegram Website",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #080808;
    color: white;
}

.block-container {
    max-width: 1400px;
    padding-top: 25px;
}

.title {
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #888;
    margin-bottom: 30px;
}

.channel-box {
    background: linear-gradient(135deg, #191919, #0d0d0d);
    border: 1px solid #292929;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
}

.channel-title {
    font-size: 28px;
    font-weight: 800;
}

.file-box {
    background: #151515;
    border: 1px solid #292929;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
}

.file-title {
    font-size: 17px;
    font-weight: 700;
}

.file-info {
    color: #888;
    font-size: 13px;
    margin-top: 5px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SECRETS
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
# TELEGRAM CLIENT
# ============================================================

SESSION_PATH = os.path.join(
    tempfile.gettempdir(),
    "telegram_streamlit"
)

client = TelegramClient(
    SESSION_PATH,
    API_ID,
    API_HASH
)


# ============================================================
# ASYNC RUNNER
# ============================================================

def run_async(coro):

    try:
        loop = asyncio.get_event_loop()

    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():

        new_loop = asyncio.new_event_loop()

        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    return loop.run_until_complete(coro)


# ============================================================
# CONNECT
# ============================================================

async def connect_telegram():

    if not client.is_connected():
        await client.connect()

    if not await client.is_user_authorized():
        await client.start(
            bot_token=BOT_TOKEN
        )

    return True


try:

    run_async(
        connect_telegram()
    )

except Exception as e:

    st.error("❌ Telegram connection failed")
    st.code(str(e))
    st.stop()


# ============================================================
# GET CHANNELS
# ============================================================

async def load_channels():

    channels = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        # Telegram broadcast channel
        if getattr(entity, "broadcast", False):

            channels.append({
                "id": entity.id,
                "title": getattr(
                    entity,
                    "title",
                    "Unknown Channel"
                )
            })

    return channels


try:

    channels = run_async(
        load_channels()
    )

except Exception as e:

    st.error("❌ Channels load nahi ho paaye.")
    st.code(str(e))
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">📱 My Telegram Website</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Private Telegram Channels'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# NO CHANNEL
# ============================================================

if not channels:

    st.warning(
        "⚠️ Koi channel nahi mila."
    )

    st.info(
        "Confirm karo ki bot tumhare private channel "
        "me added hai aur required permissions rakhta hai."
    )

    st.stop()


# ============================================================
# SIDEBAR CHANNEL LIST
# ============================================================

st.sidebar.title("📁 My Channels")

channel_titles = [
    c["title"]
    for c in channels
]

selected_title = st.sidebar.selectbox(
    "Channel select karo",
    channel_titles
)

selected_channel = next(
    c for c in channels
    if c["title"] == selected_title
)


# ============================================================
# CHANNEL HEADER
# ============================================================

st.markdown(
    f"""
    <div class="channel-box">
        <div class="channel-title">
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
# SEARCH
# ============================================================

search = st.text_input(
    "🔎 Search",
    placeholder="Search video, file, PDF, post..."
)


# ============================================================
# LIMIT
# ============================================================

limit = st.select_slider(
    "Posts load karo",
    options=[
        20,
        50,
        100,
        200,
        500
    ],
    value=100
)


# ============================================================
# GET MESSAGES
# ============================================================

async def load_messages(
    channel_id,
    limit_value,
    search_value
):

    entity = await client.get_entity(
        channel_id
    )

    result = []

    async for message in client.iter_messages(
        entity,
        limit=limit_value,
        search=search_value or None
    ):

        if message.media or message.text:

            result.append(message)

    return result


try:

    messages = run_async(
        load_messages(
            selected_channel["id"],
            limit,
            search
        )
    )

except RPCError as e:

    st.error(
        "❌ Telegram API error"
    )

    st.code(str(e))
    st.stop()

except Exception as e:

    st.error(
        "❌ Messages load nahi ho paaye."
    )

    st.code(str(e))
    st.stop()


# ============================================================
# COUNT
# ============================================================

st.write(
    f"**{len(messages)} items found**"
)

st.divider()


# ============================================================
# MEDIA TYPE
# ============================================================

def media_type(message):

    if message.video:
        return "video"

    if message.photo:
        return "photo"

    if message.audio:
        return "audio"

    if message.document:

        mime = (
            message.document.mime_type
            or ""
        )

        if mime.startswith("video/"):
            return "video"

        if mime.startswith("audio/"):
            return "audio"

        if mime.startswith("image/"):
            return "photo"

        return "document"

    return "text"


# ============================================================
# FILE NAME
# ============================================================

def get_name(message):

    if message.file:

        if message.file.name:
            return message.file.name

        if message.file.ext:
            return (
                f"Telegram_File"
                f"{message.file.ext}"
            )

    return f"Telegram_Message_{message.id}"


# ============================================================
# DOWNLOAD
# ============================================================

async def download_message(message):

    folder = tempfile.gettempdir()

    filename = get_name(message)

    safe_filename = (
        filename
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    path = os.path.join(
        folder,
        f"{message.chat_id}_{message.id}_{safe_filename}"
    )

    if os.path.exists(path):

        return path

    result = await client.download_media(
        message,
        file=path
    )

    return result


# ============================================================
# DISPLAY ITEMS
# ============================================================

for number, message in enumerate(messages):

    kind = media_type(message)

    filename = get_name(message)

    caption = (
        message.text
        or ""
    )

    st.markdown(
        '<div class="file-box">',
        unsafe_allow_html=True
    )


    # ========================================================
    # VIDEO
    # ========================================================

    if kind == "video":

        st.markdown(
            f"""
            <div class="file-title">
                🎬 {filename}
            </div>
            """,
            unsafe_allow_html=True
        )

        if caption:
            st.caption(
                caption[:500]
            )

        if st.button(
            "▶️ Play Video",
            key=f"play_{message.id}_{number}",
            use_container_width=True
        ):

            with st.spinner(
                "⏳ Video loading..."
            ):

                try:

                    video_path = run_async(
                        download_message(message)
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


    # ========================================================
    # PHOTO
    # ========================================================

    elif kind == "photo":

        st.markdown(
            f"""
            <div class="file-title">
                🖼️ Image
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "👁️ Open Image",
            key=f"image_{message.id}_{number}",
            use_container_width=True
        ):

            with st.spinner(
                "Loading image..."
            ):

                try:

                    image_path = run_async(
                        download_message(message)
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


    # ========================================================
    # AUDIO
    # ========================================================

    elif kind == "audio":

        st.markdown(
            f"""
            <div class="file-title">
                🎵 {filename}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "▶️ Play Audio",
            key=f"audio_{message.id}_{number}",
            use_container_width=True
        ):

            with st.spinner(
                "Loading audio..."
            ):

                try:

                    audio_path = run_async(
                        download_message(message)
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


    # ========================================================
    # DOCUMENT / FILE
    # ========================================================

    elif kind == "document":

        st.markdown(
            f"""
            <div class="file-title">
                📄 {filename}
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
            key=f"file_{message.id}_{number}",
            use_container_width=True
        ):

            with st.spinner(
                "⏳ File loading..."
            ):

                try:

                    file_path = run_async(
                        download_message(message)
                    )

                    if file_path:

                        with open(
                            file_path,
                            "rb"
                        ) as file:

                            data = file.read()

                        st.download_button(
                            "⬇️ Download File",
                            data=data,
                            file_name=filename,
                            key=f"download_{message.id}_{number}",
                            use_container_width=True
                        )

                        # PDF viewer
                        if filename.lower().endswith(
                            ".pdf"
                        ):

                            import base64

                            encoded = base64.b64encode(
                                data
                            ).decode()

                            st.markdown(
                                f"""
                                <iframe
                                    src="data:application/pdf;base64,{encoded}"
                                    width="100%"
                                    height="700"
                                    style="border:none;">
                                </iframe>
                                """,
                                unsafe_allow_html=True
                            )

                except Exception as e:

                    st.error(
                        "File load failed."
                    )

                    st.code(
                        str(e)
                    )


    # ========================================================
    # TEXT POST
    # ========================================================

    else:

        st.markdown(
            """
            <div class="file-title">
                📝 Telegram Post
            </div>
            """,
            unsafe_allow_html=True
        )

        if caption:

            st.write(
                caption
            )

        else:

            st.caption(
                "Empty Telegram post"
            )


    # ========================================================
    # MESSAGE ID
    # ========================================================

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
# REFRESH
# ============================================================

st.divider()

if st.button(
    "🔄 Refresh Channels",
    use_container_width=True
):

    st.cache_data.clear()
    st.rerun()

सबसे जरूरी: "requirements.txt"

इसे भी exactly ऐसा रखो:

streamlit
Telethon

Streamlit की documentation के अनुसार external Python packages को "requirements.txt" में declare करना होता है और file repository root या app entrypoint के directory में होनी चाहिए। Dependency file बदलने पर Community Cloud नया environment resolve/install करता है।

तुम्हारा GitHub structure:

telegram-website/
│
├── app.py
└── requirements.txt

⚠️ लेकिन एक बात

अगर "Telethon" डालने के बाद भी वही "ModuleNotFoundError" आ रहा है, तो इस नए "app.py" को बदलने से error ठीक नहीं होगा। उस स्थिति में समस्या deployment/dependency installation की है, और हमें Manage app → Logs देखना होगा। Streamlit भी "ModuleNotFoundError" के लिए dependency file और deployment logs check करने की सलाह देता है।

अगर चाहो तो Manage app → Logs का screenshot भेज दो; token/API credentials छिपाकर। मैं उसी के आधार पर exact fix बताऊँगा।
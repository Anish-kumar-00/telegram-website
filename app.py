import os
import asyncio
import tempfile
import html
import mimetypes
import base64

import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import Channel


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Telegram Website",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(80, 70, 180, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(0, 150, 255, 0.10),
            transparent 30%
        ),
        #080b12;
    color: white;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

.hero {
    padding: 35px;
    border-radius: 25px;
    background:
        linear-gradient(
            135deg,
            rgba(30, 40, 75, 0.95),
            rgba(10, 13, 25, 0.98)
        );
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 20px 70px rgba(0,0,0,0.35);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    color: #b9c0d0;
    font-size: 17px;
}

.folder-card {
    padding: 22px;
    border-radius: 20px;
    background:
        linear-gradient(
            145deg,
            rgba(30,35,55,0.95),
            rgba(14,17,28,0.98)
        );
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 20px;
}

.file-card {
    padding: 20px;
    border-radius: 18px;
    background: rgba(20,24,38,0.95);
    border: 1px solid rgba(255,255,255,0.08);
    margin: 14px 0;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(80,130,255,0.15);
    border: 1px solid rgba(80,130,255,0.25);
    color: #bcd0ff;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 3. TELEGRAM SECRETS
# ============================================================

try:
    API_ID = int(st.secrets["TELEGRAM_API_ID"])
    API_HASH = st.secrets["TELEGRAM_API_HASH"]
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

except Exception:
    st.error("❌ Telegram Secrets missing.")

    st.code(
        """TELEGRAM_API_ID = "YOUR_API_ID"
TELEGRAM_API_HASH = "YOUR_API_HASH"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
"""
    )

    st.stop()


# ============================================================
# 4. ASYNC HELPER
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
# 5. TELEGRAM CLIENT
# ============================================================

SESSION_PATH = os.path.join(
    tempfile.gettempdir(),
    "telegram_website_session"
)


async def create_client():

    client = TelegramClient(
        SESSION_PATH,
        API_ID,
        API_HASH,
    )

    await client.start(
        bot_token=BOT_TOKEN
    )

    return client


@st.cache_resource
def get_client():

    return run_async(
        create_client()
    )


try:

    client = get_client()

except Exception as e:

    st.error("❌ Telegram connection failed.")
    st.code(str(e))
    st.stop()


# ============================================================
# 6. GET CHANNELS
# ============================================================

async def get_channels():

    channels = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        if isinstance(entity, Channel):

            if getattr(
                entity,
                "broadcast",
                False
            ):

                channels.append(
                    {
                        "id": entity.id,
                        "title": (
                            dialog.name
                            or "Unnamed Channel"
                        ),
                        "username": getattr(
                            entity,
                            "username",
                            None
                        ),
                    }
                )

    return channels


try:

    channels = run_async(
        get_channels()
    )

except Exception as e:

    st.error("❌ Channels load nahi ho pa rahe.")
    st.code(str(e))
    st.stop()


# ============================================================
# 7. HEADER
# ============================================================

st.markdown(
    """
<div class="hero">

<h1>📁 Telegram Website</h1>

<p>
Your Telegram channels in folders — videos, images,
PDFs, audio and other files.
</p>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 8. CHANNEL CHECK
# ============================================================

if not channels:

    st.warning(
        "⚠️ Koi Telegram channel nahi mila."
    )

    st.info(
        "Check karo ki bot ko tumhare private channels me add kiya gaya hai."
    )

    st.stop()


# ============================================================
# 9. SIDEBAR
# ============================================================

st.sidebar.title("📁 Telegram Channels")

st.sidebar.caption(
    f"{len(channels)} channel(s)"
)

channel_names = [
    channel["title"]
    for channel in channels
]

selected_name = st.sidebar.radio(
    "Folders",
    channel_names,
)

selected_channel = next(
    (
        channel
        for channel in channels
        if channel["title"] == selected_name
    ),
    None,
)


# ============================================================
# 10. FOLDER HEADER
# ============================================================

st.markdown(
    f"""
<div class="folder-card">

<h2>📂 {html.escape(selected_channel["title"])}</h2>

<span class="badge">
PRIVATE TELEGRAM CHANNEL
</span>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 11. SEARCH
# ============================================================

col1, col2 = st.columns([4, 1])

with col1:

    search_text = st.text_input(
        "🔎 Search files / messages",
        placeholder="Search...",
    )

with col2:

    message_limit = st.number_input(
        "Messages",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
    )


# ============================================================
# 12. FETCH MESSAGES
# ============================================================

async def fetch_messages(
    channel_id,
    limit,
    search,
):

    result = []

    async for message in client.iter_messages(
        channel_id,
        limit=limit,
        search=search if search else None,
    ):

        result.append(message)

    return result


with st.spinner(
    "📡 Telegram se messages load ho rahe hain..."
):

    try:

        messages = run_async(
            fetch_messages(
                selected_channel["id"],
                int(message_limit),
                search_text.strip(),
            )
        )

    except Exception as e:

        st.error(
            "❌ Messages load nahi ho pa rahe."
        )

        st.code(str(e))

        st.stop()


# ============================================================
# 13. RESULT
# ============================================================

st.caption(
    f"📦 {len(messages)} item(s) found"
)

if not messages:

    st.info(
        "Is channel me koi matching message nahi mila."
    )

    st.stop()


# ============================================================
# 14. MEDIA TYPE
# ============================================================

def get_media_type(message):

    if message.video:
        return "video"

    if message.photo:
        return "photo"

    if message.audio:
        return "audio"

    if message.document:

        mime = ""
        filename = ""

        if message.file:

            mime = (
                message.file.mime_type
                or ""
            )

            filename = (
                message.file.name
                or ""
            ).lower()

        if (
            mime == "application/pdf"
            or filename.endswith(".pdf")
        ):

            return "pdf"

        return "document"

    if message.text:
        return "text"

    return "other"


# ============================================================
# 15. DOWNLOAD
# ============================================================

async def download_media(
    message,
    folder,
):

    os.makedirs(
        folder,
        exist_ok=True
    )

    return await client.download_media(
        message,
        file=folder,
    )


# ============================================================
# 16. DISPLAY
# ============================================================

for message in messages:

    media_type = get_media_type(message)

    caption = (
        message.text or ""
    ).strip()


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    if media_type == "text":

        st.markdown(
            '<div class="file-card">',
            unsafe_allow_html=True,
        )

        st.markdown("### 💬 Message")

        st.write(caption)

        if message.date:

            st.caption(
                message.date.strftime(
                    "%d %b %Y • %I:%M %p"
                )
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        continue


    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    if media_type == "other":
        continue


    # --------------------------------------------------------
    # CARD
    # --------------------------------------------------------

    st.markdown(
        '<div class="file-card">',
        unsafe_allow_html=True,
    )


    filename = "Telegram File"

    if message.file:

        filename = (
            message.file.name
            or filename
        )


    if media_type == "video":
        icon = "🎬"

    elif media_type == "photo":
        icon = "🖼️"

    elif media_type == "audio":
        icon = "🎵"

    elif media_type == "pdf":
        icon = "📕"

    else:
        icon = "📄"


    st.markdown(
        f"### {icon} {html.escape(filename)}"
    )


    if message.date:

        st.caption(
            message.date.strftime(
                "%d %b %Y • %I:%M %p"
            )
        )


    # ========================================================
    # VIDEO
    # ========================================================

    if media_type == "video":

        folder = tempfile.mkdtemp(
            prefix="telegram_video_"
        )

        with st.spinner(
            "🎬 Video loading..."
        ):

            try:

                video_path = run_async(
                    download_media(
                        message,
                        folder,
                    )
                )

                if video_path:

                    st.video(
                        video_path
                    )

                    with open(
                        video_path,
                        "rb"
                    ) as f:

                        video_data = f.read()


                    mime = (
                        message.file.mime_type
                        if message.file
                        and message.file.mime_type
                        else "video/mp4"
                    )


                    st.download_button(
                        "⬇️ Download Video",
                        data=video_data,
                        file_name=os.path.basename(
                            video_path
                        ),
                        mime=mime,
                        key=f"video_{message.id}",
                    )

            except Exception as e:

                st.error(
                    "Video load nahi ho paya."
                )

                st.caption(str(e))


    # ========================================================
    # PHOTO
    # ========================================================

    elif media_type == "photo":

        folder = tempfile.mkdtemp(
            prefix="telegram_photo_"
        )

        with st.spinner(
            "🖼️ Image loading..."
        ):

            try:

                image_path = run_async(
                    download_media(
                        message,
                        folder,
                    )
                )

                if image_path:

                    st.image(
                        image_path,
                        use_container_width=True,
                    )

                    with open(
                        image_path,
                        "rb"
                    ) as f:

                        image_data = f.read()


                    st.download_button(
                        "⬇️ Download Image",
                        data=image_data,
                        file_name=os.path.basename(
                            image_path
                        ),
                        mime="image/jpeg",
                        key=f"photo_{message.id}",
                    )

            except Exception as e:

                st.error(
                    "Image load nahi ho payi."
                )

                st.caption(str(e))


    # ========================================================
    # AUDIO
    # ========================================================

    elif media_type == "audio":

        folder = tempfile.mkdtemp(
            prefix="telegram_audio_"
        )

        with st.spinner(
            "🎵 Audio loading..."
        ):

            try:

                audio_path = run_async(
                    download_media(
                        message,
                        folder,
                    )
                )

                if audio_path:

                    mime = (
                        message.file.mime_type
                        if message.file
                        and message.file.mime_type
                        else "audio/mpeg"
                    )

                    st.audio(
                        audio_path,
                        format=mime,
                    )

                    with open(
                        audio_path,
                        "rb"
                    ) as f:

                        audio_data = f.read()


                    st.download_button(
                        "⬇️ Download Audio",
                        data=audio_data,
                        file_name=os.path.basename(
                            audio_path
                        ),
                        mime=mime,
                        key=f"audio_{message.id}",
                    )

            except Exception as e:

                st.error(
                    "Audio load nahi ho paya."
                )

                st.caption(str(e))


    # ========================================================
    # PDF
    # ========================================================

    elif media_type == "pdf":

        folder = tempfile.mkdtemp(
            prefix="telegram_pdf_"
        )

        with st.spinner(
            "📕 PDF loading..."
        ):

            try:

                pdf_path = run_async(
                    download_media(
                        message,
                        folder,
                    )
                )

                if pdf_path:

                    with open(
                        pdf_path,
                        "rb"
                    ) as f:

                        pdf_data = f.read()


                    encoded = base64.b64encode(
                        pdf_data
                    ).decode("utf-8")


                    pdf_viewer = f"""
                    <iframe
                        src="data:application/pdf;base64,{encoded}"
                        width="100%"
                        height="700"
                        style="
                            border:none;
                            border-radius:15px;
                        "
                    ></iframe>
                    """


                    st.components.v1.html(
                        pdf_viewer,
                        height=720,
                    )


                    pdf_name = filename

                    if not pdf_name.lower().endswith(
                        ".pdf"
                    ):

                        pdf_name += ".pdf"


                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf_data,
                        file_name=pdf_name,
                        mime="application/pdf",
                        key=f"pdf_{message.id}",
                    )

            except Exception as e:

                st.error(
                    "PDF load nahi ho paya."
                )

                st.caption(str(e))


    # ========================================================
    # DOCUMENT
    # ========================================================

    elif media_type == "document":

        folder = tempfile.mkdtemp(
            prefix="telegram_document_"
        )

        with st.spinner(
            "📄 File loading..."
        ):

            try:

                file_path = run_async(
                    download_media(
                        message,
                        folder,
                    )
                )

                if file_path:

                    mime = (
                        message.file.mime_type
                        if message.file
                        and message.file.mime_type
                        else (
                            mimetypes.guess_type(
                                file_path
                            )[0]
                            or "application/octet-stream"
                        )
                    )


                    with open(
                        file_path,
                        "rb"
                    ) as f:

                        file_data = f.read()


                    st.download_button(
                        "⬇️ Download File",
                        data=file_data,
                        file_name=os.path.basename(
                            file_path
                        ),
                        mime=mime,
                        key=f"document_{message.id}",
                    )

            except Exception as e:

                st.error(
                    "File load nahi ho payi."
                )

                st.caption(str(e))


    # ========================================================
    # CAPTION
    # ========================================================

    if caption:

        st.markdown("**Caption:**")

        st.write(caption)


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# 17. FOOTER
# ============================================================

st.markdown(
    """
<hr>

<div style="text-align:center;color:#777;">
Telegram Website • Streamlit • Telegram API
</div>
""",
    unsafe_allow_html=True,
)
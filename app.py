# ============================================================
# TELEGRAM WEBSITE - STREAMLIT
# ============================================================

import os
import sys
import asyncio
import tempfile
import subprocess
import html
import mimetypes

import streamlit as st


# ============================================================
# 1. AUTO INSTALL TELETHON
# ============================================================

try:
    import telethon
except ImportError:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "Telethon==1.41.2",
        ]
    )

from telethon import TelegramClient
from telethon.tl.types import Channel


# ============================================================
# 2. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Telegram Website",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(90, 60, 180, 0.18), transparent 30%),
        radial-gradient(circle at 90% 20%, rgba(0, 150, 255, 0.12), transparent 30%),
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
            rgba(25, 35, 70, 0.92),
            rgba(12, 15, 28, 0.96)
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
    background: linear-gradient(
        145deg,
        rgba(30,35,55,0.95),
        rgba(14,17,28,0.98)
    );
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 15px;
}

.file-card {
    padding: 20px;
    border-radius: 18px;
    background: rgba(20,24,38,0.95);
    border: 1px solid rgba(255,255,255,0.08);
    margin: 12px 0;
}

.small-text {
    color: #aeb6c7;
    font-size: 14px;
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
# 4. TELEGRAM SECRETS
# ============================================================

try:
    API_ID = int(st.secrets["TELEGRAM_API_ID"])
    API_HASH = st.secrets["TELEGRAM_API_HASH"]
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

except Exception as e:
    st.error("Telegram Secrets nahi mile.")
    st.code(
        """TELEGRAM_API_ID = "YOUR_API_ID"
TELEGRAM_API_HASH = "YOUR_API_HASH"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN" """
    )
    st.stop()


# ============================================================
# 5. ASYNC HELPERS
# ============================================================

def run_async(coro):
    """
    Streamlit ke andar async Telethon functions safely run karta hai.
    """
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
# 6. TELEGRAM CLIENT
# ============================================================

SESSION_PATH = os.path.join(
    tempfile.gettempdir(),
    "telegram_streamlit_session"
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
    return run_async(create_client())


try:
    client = get_client()

except Exception as e:
    st.error("Telegram connection failed.")
    st.code(str(e))
    st.info(
        "Check karo ki API ID, API HASH aur Bot Token Streamlit Secrets me sahi hain."
    )
    st.stop()


# ============================================================
# 7. GET CHANNELS
# ============================================================

async def fetch_channels():
    channels = []

    async for dialog in client.iter_dialogs():

        entity = dialog.entity

        if isinstance(entity, Channel):

            if getattr(entity, "broadcast", False):

                channels.append(
                    {
                        "id": entity.id,
                        "title": dialog.name or "Unnamed Channel",
                        "username": getattr(
                            entity,
                            "username",
                            None
                        ),
                    }
                )

    return channels


try:
    channels = run_async(fetch_channels())

except Exception as e:
    st.error("Channels load nahi ho pa rahe.")
    st.code(str(e))
    st.stop()


# ============================================================
# 8. HEADER
# ============================================================

st.markdown(
    """
<div class="hero">

<h1>📁 Telegram Website</h1>

<p>
Private Telegram Channels ko folders ki tarah browse karein,
videos play karein aur files/PDFs access karein.
</p>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 9. NO CHANNEL
# ============================================================

if not channels:

    st.warning(
        "Koi Telegram channel nahi mila."
    )

    st.info(
        "Make sure bot ko required channel me add kiya gaya hai."
    )

    st.stop()


# ============================================================
# 10. SIDEBAR - FOLDERS
# ============================================================

st.sidebar.title("📁 Channels")

st.sidebar.caption(
    f"{len(channels)} channel(s) available"
)


channel_names = [
    channel["title"]
    for channel in channels
]


selected_name = st.sidebar.radio(
    "Open Folder",
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
# 11. MAIN FOLDER HEADER
# ============================================================

st.markdown(
    f"""
<div class="folder-card">

<h2>📂 {html.escape(selected_channel["title"])}</h2>

<span class="badge">
Telegram Channel
</span>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 12. SEARCH + LIMIT
# ============================================================

col1, col2 = st.columns(
    [4, 1]
)

with col1:

    search_text = st.text_input(
        "🔎 Search",
        placeholder="Message ya file search karein...",
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
# 13. GET MESSAGES
# ============================================================

async def fetch_messages(
    channel_id,
    limit,
    search=None,
):

    messages = []

    async for message in client.iter_messages(
        channel_id,
        limit=limit,
        search=search if search else None,
    ):

        messages.append(message)

    return messages


with st.spinner("Telegram se files load ho rahi hain..."):

    try:

        messages = run_async(
            fetch_messages(
                selected_channel["id"],
                int(message_limit),
                search_text.strip() or None,
            )
        )

    except Exception as e:

        st.error("Messages load nahi ho pa rahe.")
        st.code(str(e))
        st.stop()


# ============================================================
# 14. MESSAGE COUNT
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
# 15. MEDIA TYPE
# ============================================================

def get_media_type(message):

    if message.video:
        return "video"

    if message.photo:
        return "photo"

    if message.audio:
        return "audio"

    if message.document:

        filename = ""

        if message.file:
            filename = (
                message.file.name or ""
            ).lower()

        mime = (
            message.file.mime_type
            if message.file
            else ""
        )

        if mime == "application/pdf":
            return "pdf"

        if filename.endswith(".pdf"):
            return "pdf"

        return "document"

    if message.text:
        return "text"

    return "other"


# ============================================================
# 16. DOWNLOAD MEDIA
# ============================================================

async def download_message_media(
    message,
    folder,
):

    os.makedirs(
        folder,
        exist_ok=True
    )

    path = await client.download_media(
        message,
        file=folder,
    )

    return path


# ============================================================
# 17. DISPLAY MESSAGES
# ============================================================

for index, message in enumerate(messages):

    media_type = get_media_type(message)

    message_text = (
        message.text or ""
    ).strip()

    message_date = ""

    if message.date:

        try:
            message_date = message.date.strftime(
                "%d %b %Y • %I:%M %p"
            )
        except Exception:
            message_date = str(message.date)


    # --------------------------------------------------------
    # TEXT MESSAGE
    # --------------------------------------------------------

    if media_type == "text":

        st.markdown(
            '<div class="file-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"### 💬 Message"
        )

        st.write(message_text)

        if message_date:
            st.caption(message_date)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        continue


    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    if media_type == "other":

        if not message_text:
            continue

        st.markdown(
            '<div class="file-card">',
            unsafe_allow_html=True,
        )

        st.write(message_text)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        continue


    # --------------------------------------------------------
    # MEDIA CARD
    # --------------------------------------------------------

    with st.container():

        st.markdown(
            '<div class="file-card">',
            unsafe_allow_html=True,
        )

        # File name
        filename = "Telegram File"

        if message.file:

            filename = (
                message.file.name
                or filename
            )

        # Title
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


        if message_date:

            st.caption(
                message_date
            )


        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        if media_type == "video":

            temp_folder = tempfile.mkdtemp(
                prefix="telegram_video_"
            )

            with st.spinner(
                "Video loading..."
            ):

                try:

                    video_path = run_async(
                        download_message_media(
                            message,
                            temp_folder,
                        )
                    )

                    if video_path and os.path.exists(
                        video_path
                    ):

                        st.video(
                            video_path
                        )

                        with open(
                            video_path,
                            "rb"
                        ) as video_file:

                            st.download_button(
                                "⬇️ Download Video",
                                data=video_file,
                                file_name=os.path.basename(
                                    video_path
                                ),
                                mime=(
                                    message.file.mime_type
                                    if message.file
                                    and message.file.mime_type
                                    else "video/mp4"
                                ),
                                key=f"video_{message.id}",
                            )

                    else:

                        st.warning(
                            "Video download nahi ho paya."
                        )

                except Exception as e:

                    st.error(
                        "Video load nahi ho paya."
                    )

                    st.caption(
                        str(e)
                    )


        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        elif media_type == "photo":

            temp_folder = tempfile.mkdtemp(
                prefix="telegram_photo_"
            )

            with st.spinner(
                "Image loading..."
            ):

                try:

                    image_path = run_async(
                        download_message_media(
                            message,
                            temp_folder,
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
                        ) as image_file:

                            st.download_button(
                                "⬇️ Download Image",
                                data=image_file,
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

                    st.caption(
                        str(e)
                    )


        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        elif media_type == "audio":

            temp_folder = tempfile.mkdtemp(
                prefix="telegram_audio_"
            )

            with st.spinner(
                "Audio loading..."
            ):

                try:

                    audio_path = run_async(
                        download_message_media(
                            message,
                            temp_folder,
                        )
                    )

                    if audio_path:

                        mime_type = (
                            message.file.mime_type
                            if message.file
                            and message.file.mime_type
                            else "audio/mpeg"
                        )

                        st.audio(
                            audio_path,
                            format=mime_type,
                        )

                        with open(
                            audio_path,
                            "rb"
                        ) as audio_file:

                            st.download_button(
                                "⬇️ Download Audio",
                                data=audio_file,
                                file_name=os.path.basename(
                                    audio_path
                                ),
                                mime=mime_type,
                                key=f"audio_{message.id}",
                            )

                except Exception as e:

                    st.error(
                        "Audio load nahi ho paya."
                    )

                    st.caption(
                        str(e)
                    )


        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        elif media_type == "pdf":

            temp_folder = tempfile.mkdtemp(
                prefix="telegram_pdf_"
            )

            with st.spinner(
                "PDF loading..."
            ):

                try:

                    pdf_path = run_async(
                        download_message_media(
                            message,
                            temp_folder,
                        )
                    )

                    if pdf_path:

                        with open(
                            pdf_path,
                            "rb"
                        ) as pdf_file:

                            pdf_data = pdf_file.read()


                        # PDF viewer
                        import base64

                        pdf_base64 = base64.b64encode(
                            pdf_data
                        ).decode("utf-8")


                        pdf_html = f"""
                        <iframe
                            src="data:application/pdf;base64,{pdf_base64}"
                            width="100%"
                            height="700"
                            style="
                                border:none;
                                border-radius:15px;
                                background:#111;
                            "
                        >
                        </iframe>
                        """

                        st.components.v1.html(
                            pdf_html,
                            height=720,
                        )


                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_data,
                            file_name=(
                                filename
                                if filename.lower().endswith(
                                    ".pdf"
                                )
                                else filename + ".pdf"
                            ),
                            mime="application/pdf",
                            key=f"pdf_{message.id}",
                        )

                except Exception as e:

                    st.error(
                        "PDF load nahi ho paya."
                    )

                    st.caption(
                        str(e)
                    )


        # ----------------------------------------------------
        # OTHER DOCUMENT
        # ----------------------------------------------------

        elif media_type == "document":

            temp_folder = tempfile.mkdtemp(
                prefix="telegram_document_"
            )

            with st.spinner(
                "File loading..."
            ):

                try:

                    file_path = run_async(
                        download_message_media(
                            message,
                            temp_folder,
                        )
                    )

                    if file_path:

                        mime_type = (
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


                        # Try browser-friendly files
                        if mime_type.startswith(
                            "text/"
                        ):

                            try:

                                with open(
                                    file_path,
                                    "r",
                                    encoding="utf-8",
                                    errors="ignore",
                                ) as f:

                                    content = f.read()

                                st.code(
                                    content,
                                    language="text",
                                )

                            except Exception:
                                pass


                        with open(
                            file_path,
                            "rb"
                        ) as file_data:

                            st.download_button(
                                "⬇️ Download File",
                                data=file_data,
                                file_name=os.path.basename(
                                    file_path
                                ),
                                mime=mime_type,
                                key=f"file_{message.id}",
                            )

                except Exception as e:

                    st.error(
                        "File load nahi ho payi."
                    )

                    st.caption(
                        str(e)
                    )


        # ----------------------------------------------------
        # CAPTION
        # ----------------------------------------------------

        if message_text:

            st.markdown(
                "**Caption:**"
            )

            st.write(
                message_text
            )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# 18. FOOTER
# ============================================================

st.markdown(
    """
<hr>

<center>

<span style="color:#777;">
Telegram Website • Powered by Streamlit & Telegram API
</span>

</center>
""",
    unsafe_allow_html=True,
)
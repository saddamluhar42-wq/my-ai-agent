import os
import re
import uuid
from pathlib import Path

import streamlit as st

from agent.core import run_agent
from ai.agent import (
    AgentError,
    generate_image,
    is_image_generation_available,
)
from config import MAX_FILE_SIZE_MB
from database.memory import (
    build_memory_context,
    get_recent_messages,
    save_assistant_message,
    save_user_message,
)
from database.models import (
    get_or_create_conversation,
    get_or_create_user,
)
from files.processor import (
    build_file_context,
    process_multiple_files,
)
from providers.video.manager import (
    generate_video,
    get_available_video_providers,
)


# ============================================================
# FILE SUPPORT
# ============================================================

ALLOWED_FILE_TYPES = [
    "txt",
    "md",
    "csv",
    "json",
    "py",
    "html",
    "xml",
    "yaml",
    "yml",
    "pdf",
    "docx",
]


# ============================================================
# EMPTY STATE IMAGE
# ============================================================

EMPTY_STATE_IMAGE = "assets/agent_astronaut.webp"


# ============================================================
# VIDEO OUTPUT
# ============================================================

VIDEO_OUTPUT_DIR = Path(
    os.getenv(
        "VIDEO_OUTPUT_DIR",
        "generated_videos",
    )
)


# ============================================================
# IMAGE REQUEST DETECTION
# ============================================================

IMAGE_REQUEST_PHRASES = [
    "generate image",
    "create image",
    "make image",
    "generate an image",
    "create an image",
    "make an image",
    "image generate",
    "image banao",
    "image bana",
    "image bana do",
    "photo banao",
    "photo bana do",
    "picture banao",
    "picture bana do",
    "tasveer banao",
    "tasveer bana do",
    "image generate karo",
    "image create karo",
    "image chahiye",
]


# ============================================================
# VIDEO REQUEST DETECTION
# ============================================================

VIDEO_REQUEST_PHRASES = [
    "generate video",
    "create video",
    "make video",
    "generate a video",
    "create a video",
    "make a video",
    "video generate",
    "video banao",
    "video bana",
    "video bana do",
    "video generate karo",
    "video create karo",
    "video bana do",
    "video chahiye",
    "video generate kar",
    "video create kar",
    "video bana kar do",
    "video bana ke do",
    "ai video banao",
    "ai video bana do",
    "text to video",
    "text-to-video",
]


# ============================================================
# CONFIRMATION WORDS
# ============================================================

YES_WORDS = [
    "yes",
    "y",
    "haan",
    "ha",
    "ji",
    "ji haan",
    "kar do",
    "bana do",
    "generate karo",
    "generate",
    "proceed",
    "ok",
    "okay",
]


NO_WORDS = [
    "no",
    "n",
    "nahi",
    "nahin",
    "cancel",
    "cancel karo",
    "mat karo",
    "stop",
]


# ============================================================
# VIDEO PROVIDER NORMALIZATION
# ============================================================

VIDEO_PROVIDER_ALIASES = {
    "google": "google",
    "veo": "google",
    "gemini video": "google",
    "google veo": "google",
    "runway": "runway",
    "luma": "luma",
    "replicate": "replicate",
}


META_REPLY_PREFIXES = (
    r"^(user safety|powered by)\s*:",
)


def clean_assistant_text(text):

    value = str(
        text or ""
    ).strip()

    if not value:
        return ""

    cleaned_lines = []

    for line in value.splitlines():

        stripped = line.strip()

        if not stripped:
            cleaned_lines.append("")
            continue

        if any(
            re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            )
            for pattern in META_REPLY_PREFIXES
        ):
            continue

        cleaned_lines.append(
            line
        )

    return "\n".join(
        cleaned_lines
    ).strip()


# ============================================================
# CHAT STATE
# ============================================================

def initialize_chat_state():

    defaults = {
        "messages": [],
        "uploaded_files": [],
        "file_context": "",
        "clarification_answer": "",
        "clarification_question": "",
        "conversation_id": None,
        "user_id": None,
        "preferred_provider": "Auto",
        "pending_image_prompt": None,
        "pending_video_prompt": None,
        "show_provider_info": False,
        "enable_chat_memory": True,
        "confirm_image_generation": True,
        "confirm_video_generation": True,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# MAIN CHAT
# ============================================================

def render_chat():

    initialize_chat_state()

    render_chat_header()

    if not st.session_state.get("messages"):

        render_empty_state()

    else:

        render_messages()

    render_composer()


# ============================================================
# CHAT HEADER
# ============================================================

def render_chat_header():

    provider = st.session_state.get(
        "preferred_provider",
        "Auto",
    )

    st.markdown(
        f"""
<div class="chat-header">
    <div>
        My AI Agent
        <span style="
            color:#858585;
            font-weight:400;
            margin-left:8px;
        ">
            {provider}
        </span>
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# EMPTY STATE
# ============================================================

def render_empty_state():

    st.markdown(
        "<div style='height:55px'></div>",
        unsafe_allow_html=True,
    )

    image_col_left, image_col, image_col_right = st.columns(
        [1, 1, 1]
    )

    with image_col:

        try:

            st.image(
                EMPTY_STATE_IMAGE,
                width=155,
            )

        except Exception:

            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-size:48px;
                    padding:30px;
                ">
                    🤖
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:8px;
            margin-bottom:8px;
        ">
            <div style="
                font-size:28px;
                font-weight:600;
                color:#f5f5f5;
            ">
                How can I help you today?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#9b9b9b;
            font-size:14px;
            line-height:1.6;
            margin-bottom:30px;
        ">
            Ask anything, upload a file, or request an image or video.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        3,
        gap="small",
    )

    with col1:

        if st.button(
            "Explain something",
            use_container_width=True,
            key="suggest_explain",
        ):

            handle_user_message(
                "Explain something interesting to me."
            )

    with col2:

        if st.button(
            "Write something",
            use_container_width=True,
            key="suggest_write",
        ):

            handle_user_message(
                "Help me write something useful."
            )

    with col3:

        if st.button(
            "Generate an image",
            use_container_width=True,
            key="suggest_image",
        ):

            handle_user_message(
                "Generate an image of a beautiful cinematic landscape."
            )


# ============================================================
# MESSAGE RENDERING
# ============================================================

def render_messages():

    messages = st.session_state.get(
        "messages",
        [],
    )

    for message_index, message in enumerate(messages):

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        message_type = message.get(
            "type",
            "text",
        )

        with st.chat_message(role):

            if message_type == "image":

                render_image_message(
                    message,
                    message_index,
                )

                continue

            if message_type == "video":

                render_video_message(
                    message,
                    message_index,
                )

                continue

            if content:

                if role == "assistant":
                    content = clean_assistant_text(
                        content
                    )

                st.markdown(
                    content
                )

            if (
                role == "assistant"
                and st.session_state.get(
                    "show_provider_info",
                    False,
                )
            ):

                provider = message.get(
                    "provider"
                )

                model = message.get(
                    "model"
                )

                if provider:

                    if model:

                        st.caption(
                            f"{provider} • {model}"
                        )

                    else:

                        st.caption(
                            f"Powered by {provider}"
                        )


# ============================================================
# IMAGE MESSAGE
# ============================================================

def render_image_message(
    message,
    message_index,
):

    image_data = message.get(
        "image"
    )

    if not image_data:
        return

    st.image(
        image_data,
        use_container_width=True,
    )

    st.download_button(
        label="Download image",
        data=image_data,
        file_name=(
            f"my_ai_agent_image_"
            f"{message_index}.png"
        ),
        mime="image/png",
        key=(
            f"download_image_"
            f"{message_index}"
        ),
    )

    provider = message.get(
        "provider"
    )

    model = message.get(
        "model"
    )

    if provider:

        if model:

            st.caption(
                f"Generated by {provider} • {model}"
            )

        else:

            st.caption(
                f"Generated by {provider}"
            )


# ============================================================
# VIDEO MESSAGE
# ============================================================

def render_video_message(
    message,
    message_index,
):

    video_path = message.get(
        "video_path"
    )

    if not video_path:
        st.error(
            "Generated video path is missing."
        )
        return

    path = Path(
        video_path
    )

    if not path.exists():

        st.error(
            "Generated video file is no longer available."
        )

        return

    try:

        st.video(
            str(path)
        )

    except Exception as error:

        st.error(
            "Unable to display generated video."
        )

        st.caption(
            str(error)
        )

        return

    try:

        video_bytes = path.read_bytes()

        st.download_button(
            label="Download video",
            data=video_bytes,
            file_name=path.name,
            mime="video/mp4",
            key=(
                f"download_video_"
                f"{message_index}"
            ),
        )

    except Exception as error:

        st.caption(
            f"Download unavailable: {error}"
        )

    provider = message.get(
        "provider"
    )

    model = message.get(
        "model"
    )

    task_id = message.get(
        "task_id"
    )

    if provider:

        if model:

            st.caption(
                f"Generated by {provider} • {model}"
            )

        else:

            st.caption(
                f"Generated by {provider}"
            )

    if task_id:

        st.caption(
            f"Task ID: {task_id}"
        )


# ============================================================
# COMPOSER
# ============================================================

def render_composer():

    submission = st.chat_input(
        "Message My AI Agent...",
        accept_file="multiple",
        file_type=ALLOWED_FILE_TYPES,
        max_upload_size=MAX_FILE_SIZE_MB,
        key="main_chat_input",
    )

    if submission is None:
        return

    text = submission.text.strip()

    files = list(
        submission.files
    )

    if files:

        process_uploaded_files(
            files
        )

    if not text and files:

        text = build_file_message(
            files
        )

    if text:

        handle_user_message(
            text
        )


# ============================================================
# FILE MESSAGE
# ============================================================
def build_file_message(files):

    names = [
        file.name
        for file in files
    ]

    if len(names) == 1:

        return (
            "Please analyze the attached "
            f"file: {names[0]}"
        )

    joined_names = ", ".join(
        names
    )

    return (
        "Please analyze these attached "
        f"files: {joined_names}"
    )


# ============================================================
# FILE PROCESSING
# ============================================================
def process_uploaded_files(
    uploaded_files,
):

    current_names = {
        item.get("name")
        for item in st.session_state.get(
            "uploaded_files",
            [],
        )
    }

    new_files = [
        file
        for file in uploaded_files
        if file.name not in current_names
    ]

    if not new_files:
        return

    processed, errors = (
        process_multiple_files(
            new_files
        )
    )

    if processed:

        existing = st.session_state.get(
            "uploaded_files",
            [],
        )

        existing.extend(
            processed
        )

        st.session_state[
            "uploaded_files"
        ] = existing

        st.session_state[
            "file_context"
        ] = build_file_context(
            existing
        )

    for error in errors:

        st.warning(
            f"{error['name']}: "
            f"{error['error']}"
        )


# ============================================================
# IMAGE REQUEST DETECTION
# ============================================================
def is_image_request(prompt):

    text = prompt.lower().strip()

    return any(
        phrase in text
        for phrase in IMAGE_REQUEST_PHRASES
    )


# ============================================================
# VIDEO REQUEST DETECTION
# ============================================================
def is_video_request(prompt):

    text = prompt.lower().strip()

    return any(
        phrase in text
        for phrase in VIDEO_REQUEST_PHRASES
    )


# ============================================================
# CONFIRMATION
# ============================================================
def is_yes_confirmation(prompt):

    return (
        prompt.lower().strip()
        in YES_WORDS
    )


def is_no_confirmation(prompt):

    return (
        prompt.lower().strip()
        in NO_WORDS
    )


# ============================================================
# IMAGE CONFIRMATION REQUEST
# ============================================================
def request_image_confirmation(
    image_prompt,
):

    st.session_state[
        "pending_image_prompt"
    ] = image_prompt

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "I detected an image-generation "
                "request.\n\n"
                "Should I generate this image?\n\n"
                "**Yes / No**"
            ),
        }
    )

    st.rerun()


# ============================================================
# VIDEO CONFIRMATION REQUEST
# ============================================================
def request_video_confirmation(
    video_prompt,
):

    st.session_state[
        "pending_video_prompt"
    ] = video_prompt

    available = get_available_video_providers()

    if available:

        providers_text = ", ".join(
            available
        )

        provider_message = (
            f"\n\nAvailable video providers: "
            f"**{providers_text}**"
        )

    else:

        provider_message = ""

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "I detected a video-generation "
                "request.\n\n"
                "Should I generate this video?\n\n"
                "**Yes / No**"
                + provider_message
            ),
        }
    )

    st.rerun()


# ============================================================
# PENDING IMAGE CONFIRMATION
# ============================================================
def handle_pending_image_confirmation(
    prompt,
):

    pending_prompt = (
        st.session_state.get(
            "pending_image_prompt"
        )
    )

    if not pending_prompt:
        return False

    if is_yes_confirmation(prompt):

        st.session_state[
            "pending_image_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        generate_confirmed_image(
            pending_prompt
        )

        return True

    if is_no_confirmation(prompt):

        st.session_state[
            "pending_image_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Image generation cancelled."
                ),
            }
        )

        st.rerun()

        return True

    st.session_state[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "Please confirm with **Yes** "
                "or **No**."
            ),
        }
    )

    st.rerun()

    return True


# ============================================================
# PENDING VIDEO CONFIRMATION
# ============================================================
def handle_pending_video_confirmation(
    prompt,
):

    pending_prompt = (
        st.session_state.get(
            "pending_video_prompt"
        )
    )

    if not pending_prompt:
        return False

    if is_yes_confirmation(prompt):

        st.session_state[
            "pending_video_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        generate_confirmed_video(
            pending_prompt
        )

        return True

    if is_no_confirmation(prompt):

        st.session_state[
            "pending_video_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Video generation cancelled."
                ),
            }
        )

        st.rerun()

        return True

    st.session_state[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "Please confirm with **Yes** "
                "or **No**."
            ),
        }
    )

    st.rerun()

    return True


# ============================================================
# VIDEO PROVIDER
# ============================================================
def resolve_video_provider():

    preferred_provider = (
        st.session_state.get(
            "preferred_provider",
            "Auto",
        )
    )

    if not preferred_provider:
        return None

    normalized = (
        str(
            preferred_provider
        )
        .strip()
        .lower()
    )

    if normalized == "auto":
        return None

    return VIDEO_PROVIDER_ALIASES.get(
        normalized
    )


# ============================================================
# VIDEO OUTPUT PATH
# ============================================================
def create_video_output_path():

    VIDEO_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        "my_ai_agent_video_"
        f"{uuid.uuid4().hex}.mp4"
    )

    return (
        VIDEO_OUTPUT_DIR
        / filename
    )


# ============================================================
# CONFIRMED VIDEO GENERATION
# ============================================================
def generate_confirmed_video(
    video_prompt,
):

    try:

        available_providers = (
            get_available_video_providers()
        )

        if not available_providers:

            raise AgentError(
                "No video-generation provider "
                "is configured."
            )

        ensure_database_context()

        conversation_id = (
            st.session_state[
                "conversation_id"
            ]
        )

        save_user_message(
            conversation_id,
            "Video generation confirmed: "
            + video_prompt,
        )

        output_path = (
            create_video_output_path()
        )

        provider = (
            resolve_video_provider()
        )

        provider_label = (
            provider
            or "Auto"
        )

        with st.spinner(
            f"Generating video with {provider_label}..."
        ):

            result = generate_video(
                prompt=video_prompt,
                provider=provider,
                output_path=str(
                    output_path
                ),
                fallback=True,
            )

        if not isinstance(
            result,
            dict,
        ):

            raise AgentError(
                "Video generation returned "
                "an invalid result."
            )

        if not result.get(
            "success",
            False,
        ):

            raise AgentError(
                result.get(
                    "error",
                    "Video generation failed.",
                )
            )

        final_output_path = result.get(
            "output_path"
        )

        if not final_output_path:

            raise AgentError(
                "Video generation returned "
                "no output file."
            )

        final_path = Path(
            final_output_path
        )

        if not final_path.exists():

            raise AgentError(
                "Generated video file was not "
                "found on the server."
            )

        result_provider = result.get(
            "provider",
            provider_label,
        )

        result_model = result.get(
            "model",
            "",
        )

        task_id = result.get(
            "task_id"
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": "",
                "type": "video",
                "video_path": str(
                    final_path
                ),
                "provider": result_provider,
                "model": result_model,
                "task_id": task_id,
            }
        )

        save_assistant_message(
            conversation_id,
            "[Video generated]",
            provider=result_provider,
        )

        st.rerun()

    except Exception as error:

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Video generation failed:\n\n"
                    f"{error}"
                ),
                "type": "text",
            }
        )

        st.rerun()


# ============================================================
# CONFIRMED IMAGE GENERATION
# ============================================================
def generate_confirmed_image(
    image_prompt,
):

    try:

        if not is_image_generation_available():

            raise AgentError(
                "No image-generation provider "
                "is configured."
            )

        ensure_database_context()

        conversation_id = (
            st.session_state[
                "conversation_id"
            ]
        )

        save_user_message(
            conversation_id,
            "Image generation confirmed: "
            + image_prompt,
        )

        with st.spinner(
            "Generating image..."
        ):

            result = generate_image(
                prompt=image_prompt,
            )

        image_data = result.get(
            "image",
        )

        if not image_data:

            raise AgentError(
                "Image generation returned "
                "no image."
            )

        provider = result.get(
            "provider",
            "Unknown",
        )

        model = result.get(
            "model",
            "",
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": "",
                "type": "image",
                "image": image_data,
                "provider": provider,
                "model": model,
            }
        )

        save_assistant_message(
            conversation_id,
            "[Image generated]",
            provider=provider,
        )

        st.rerun()

    except Exception as error:

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Image generation failed:\n\n"
                    f"{error}"
                ),
            }
        )

        st.rerun()


# ============================================================
# USER MESSAGE
# ============================================================
def handle_user_message(
    prompt,
):

    prompt = prompt.strip()

    if not prompt:
        return

    st.session_state[
        "clarification_answer"
    ] = prompt

    # --------------------------------------------------------
    # PENDING IMAGE CONFIRMATION
    # --------------------------------------------------------

    if st.session_state.get(
        "pending_image_prompt"
    ):

        handle_pending_image_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # PENDING VIDEO CONFIRMATION
    # --------------------------------------------------------

    if st.session_state.get(
        "pending_video_prompt"
    ):

        handle_pending_video_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # VIDEO REQUEST
    # --------------------------------------------------------

    if is_video_request(prompt):

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_video_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # IMAGE REQUEST
    # --------------------------------------------------------

    if is_image_request(prompt):

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_image_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # NORMAL AI CHAT
    # --------------------------------------------------------

    st.session_state[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:

        ensure_database_context()

        conversation_id = (
            st.session_state[
                "conversation_id"
            ]
        )

        user_id = (
            st.session_state[
                "user_id"
            ]
        )

        save_user_message(
            conversation_id,
            prompt,
        )

        recent_messages = (
            get_recent_messages(
                conversation_id,
                limit=30,
            )
        )

        if st.session_state.get(
            "enable_chat_memory",
            True,
        ):

            memory_context = (
                build_memory_context(
                    conversation_id,
                    prompt,
                )
            )

        else:

            memory_context = ""

        file_context = (
            st.session_state.get(
                "file_context",
                "",
            )
        )

        preferred_provider = (
            st.session_state.get(
                "preferred_provider",
                "Auto",
            )
        )

        if preferred_provider == "Auto":
            preferred_provider = None

        context = {
            "user_id": user_id,
            "memory_context": memory_context,
            "file_context": file_context,
            "recent_messages": recent_messages,
            "preferred_provider": preferred_provider,
            "uploaded_files": (
                st.session_state.get(
                    "uploaded_files",
                    [],
                )
            ),
        }

        with st.spinner(
            "Thinking..."
        ):

            result = run_agent(
                query=prompt,
                context=context,
            )

        if not result.success:

            error_message = result.metadata.get(
                "error",
                "Agent execution failed."
            )

            raise AgentError(
                error_message
            )

        answer = clean_assistant_text(
            result.answer
        )

        provider = result.provider

        metadata = result.metadata or {}

        model = metadata.get(
            "model",
            "",
        )

        if not answer:

            raise AgentError(
                "Agent returned an empty response."
            )

        save_assistant_message(
            conversation_id,
            answer,
            provider=provider,
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": answer,
                "provider": provider,
                "model": model,
                "type": "text",
                "skill": metadata.get(
                    "primary_skill",
                    "",
                ),
            }
        )

        st.session_state[
            "clarification_question"
        ] = ""

        st.rerun()

    except Exception as error:

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "AI Agent error:\n\n"
                    f"{error}"
                ),
                "type": "text",
            }
        )

        st.rerun()


# ============================================================
# DATABASE CONTEXT
# ============================================================
def ensure_database_context():

    if st.session_state.get(
        "user_id"
    ) is None:

        user_id = get_or_create_user(
            external_id="streamlit:web-user",
            display_name="Web User",
        )

        st.session_state[
            "user_id"
        ] = user_id

    if st.session_state.get(
        "conversation_id"
    ) is None:

        conversation_id = (
            get_or_create_conversation(
                st.session_state[
                    "user_id"
                ],
                title="Web Conversation",
            )
        )

        st.session_state[
            "conversation_id"
        ] = conversation_id

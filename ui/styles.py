import streamlit as st


def get_app_css():
    return """
    <style>

    /* ========================================================
       GLOBAL
    ======================================================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    html,
    body,
    [data-testid="stAppViewContainer"] {
        background: #212121 !important;
    }

    [data-testid="stAppViewContainer"] {
        min-height: 100vh;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    [data-testid="stToolbar"] {
        visibility: hidden;
    }


    /* ========================================================
       MAIN BLOCK
    ======================================================== */

    .main .block-container {
        max-width: 100%;
        padding-top: 0.75rem;
        padding-bottom: 7rem;
        padding-left: 0;
        padding-right: 0;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 0.75rem;
        padding-bottom: 7rem;
    }


    /* ========================================================
       SIDEBAR
    ======================================================== */

    [data-testid="stSidebar"] {
        background: #171717 !important;
        border-right: 1px solid #2b2b2b !important;
    }

    [data-testid="stSidebarContent"] {
        padding: 14px 12px 18px 12px !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding-bottom: 20px;
    }

    .sidebar-brand {
        color: #ffffff;
        font-size: 17px;
        font-weight: 600;
        padding: 5px 4px 12px 4px;
    }

    .sidebar-section {
        color: #9b9b9b;
        font-size: 11px;
        font-weight: 600;
        margin-top: 16px;
        margin-bottom: 7px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }


    /* ========================================================
       CHAT HEADER
    ======================================================== */

    .chat-header {
        width: 100%;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ececec;
        font-size: 14px;
        font-weight: 600;
        border-bottom: 1px solid #2b2b2b;
        background: rgba(33, 33, 33, 0.92);
    }


    /* ========================================================
       EMPTY STATE
    ======================================================== */

    .empty-state {
        width: min(720px, 92%);
        margin: 17vh auto 0 auto;
        text-align: center;
    }

    .empty-state-icon {
        width: 54px;
        height: 54px;
        margin: 0 auto 20px auto;
        border-radius: 50%;
        background: #2f2f2f;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 23px;
    }

    .empty-state-title {
        color: #f5f5f5;
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .empty-state-subtitle {
        color: #9b9b9b;
        font-size: 14px;
        line-height: 1.6;
    }


    /* ========================================================
       CHAT MESSAGES
    ======================================================== */

    [data-testid="stChatMessage"] {
        width: 100%;
        max-width: 820px;
        margin-left: auto;
        margin-right: auto;
        padding: 18px 22px;
        background: transparent !important;
        border: none !important;
    }

    [data-testid="stChatMessageContent"] {
        color: #ececec !important;
        font-size: 15px;
        line-height: 1.7;
        max-width: 100%;
    }

    [data-testid="stChatMessageContent"] p {
        margin-bottom: 0.8rem;
    }

    [data-testid="stChatMessageContent"] p:last-child {
        margin-bottom: 0;
    }


    /* ========================================================
       MESSAGE AVATAR
    ======================================================== */

    [data-testid="stChatMessageAvatarIcon"] {
        border-radius: 50%;
    }


    /* ========================================================
       MARKDOWN
    ======================================================== */

    [data-testid="stChatMessageContent"] code {
        background: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 5px;
        padding: 2px 5px;
        color: #eeeeee;
    }

    [data-testid="stChatMessageContent"] pre {
        background: #171717 !important;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 14px;
        overflow-x: auto;
    }

    [data-testid="stChatMessageContent"] pre code {
        background: transparent;
        border: none;
        padding: 0;
    }

    [data-testid="stChatMessageContent"] blockquote {
        border-left: 3px solid #666666;
        padding-left: 14px;
        color: #b5b5b5;
    }


    /* ========================================================
       CHAT INPUT
    ======================================================== */

    [data-testid="stChatInput"] {
        width: min(820px, calc(100% - 32px)) !important;
        margin-left: auto !important;
        margin-right: auto !important;
        bottom: 18px;
    }

    [data-testid="stChatInput"] > div {
        background: #2f2f2f !important;
        border: 1px solid #454545 !important;
        border-radius: 22px !important;
        box-shadow:
            0 4px 20px rgba(0, 0, 0, 0.28);
        min-height: 56px;
    }

    [data-testid="stChatInput"] > div:focus-within {
        border-color: #666666 !important;
        box-shadow:
            0 4px 22px rgba(0, 0, 0, 0.34);
    }

    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        background: transparent !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #999999 !important;
    }


    /* ========================================================
       CHAT INPUT BUTTONS
    ======================================================== */

    [data-testid="stChatInput"] button {
        border-radius: 12px !important;
    }


    /* ========================================================
       NORMAL BUTTONS
    ======================================================== */

    .stButton > button {
        width: 100%;
        min-height: 38px;
        border-radius: 9px !important;
        border: 1px solid #3a3a3a !important;
        background: transparent !important;
        color: #eeeeee !important;
        font-size: 13px;
        transition:
            background 0.15s ease,
            border-color 0.15s ease;
    }

    .stButton > button:hover {
        background: #2a2a2a !important;
        border-color: #4d4d4d !important;
    }

    .stButton > button:focus {
        box-shadow: none !important;
    }


    /* ========================================================
       PRIMARY BUTTON
    ======================================================== */

    .stButton > button[kind="primary"] {
        background: #2f2f2f !important;
        border-color: #4a4a4a !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #3a3a3a !important;
    }


    /* ========================================================
       SELECTBOX
    ======================================================== */

    [data-testid="stSelectbox"] {
        margin-bottom: 4px;
    }

    [data-testid="stSelectbox"] > div > div {
        background: #212121 !important;
        border: 1px solid #3a3a3a !important;
        border-radius: 9px !important;
    }

    [data-testid="stSelectbox"] input {
        color: #ffffff !important;
    }


    /* ========================================================
       TEXT INPUT
    ======================================================== */

    [data-testid="stTextInput"] input {
        background: #212121 !important;
        border: 1px solid #333333 !important;
        border-radius: 9px !important;
        color: #ffffff !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color: #555555 !important;
        box-shadow: none !important;
    }


    /* ========================================================
       EXPANDER
    ======================================================== */

    [data-testid="stExpander"] {
        background: transparent !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
    }

    [data-testid="stExpander"] summary {
        color: #eeeeee !important;
    }


    /* ========================================================
       STATUS / ALERTS
    ======================================================== */

    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border: 1px solid #3a3a3a !important;
    }


    /* ========================================================
       IMAGE
    ======================================================== */

    [data-testid="stImage"] {
        max-width: 820px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stImage"] img {
        border-radius: 14px;
        border: 1px solid #353535;
        box-shadow:
            0 8px 30px rgba(0, 0, 0, 0.25);
    }


    /* ========================================================
       DOWNLOAD BUTTON
    ======================================================== */

    [data-testid="stDownloadButton"] {
        max-width: 820px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stDownloadButton"] button {
        border-radius: 9px !important;
        background: #2f2f2f !important;
        border: 1px solid #414141 !important;
        color: #eeeeee !important;
    }

    [data-testid="stDownloadButton"] button:hover {
        background: #393939 !important;
    }


    /* ========================================================
       FILE UPLOADER
    ======================================================== */

    [data-testid="stFileUploader"] {
        max-width: 820px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #2a2a2a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 12px !important;
    }


    /* ========================================================
       FILE CHIPS
    ======================================================== */

    .file-chip {
        display: inline-flex;
        align-items: center;
        background: #2f2f2f;
        color: #dddddd;
        border: 1px solid #414141;
        border-radius: 9px;
        padding: 6px 10px;
        margin: 3px;
        font-size: 12px;
    }


    /* ========================================================
       DIVIDER
    ======================================================== */

    hr {
        border-color: #303030 !important;
    }


    /* ========================================================
       CAPTION
    ======================================================== */

    [data-testid="stCaptionContainer"] {
        color: #858585;
    }


    /* ========================================================
       SCROLLBAR
    ======================================================== */

    ::-webkit-scrollbar {
        width: 7px;
        height: 7px;
    }

    ::-webkit-scrollbar-track {
        background: #171717;
    }

    ::-webkit-scrollbar-thumb {
        background: #444444;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #555555;
    }


    /* ========================================================
       MOBILE
    ======================================================== */

    @media (max-width: 768px) {

        [data-testid="stChatMessage"] {
            padding-left: 12px;
            padding-right: 12px;
        }

        [data-testid="stChatInput"] {
            width: calc(100% - 18px) !important;
        }

        .empty-state {
            margin-top: 12vh;
        }

        .empty-state-title {
            font-size: 24px;
        }
    }


    /* ========================================================
       REDUCE DEFAULT STREAMLIT SPACING
    ======================================================== */

    [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }

    </style>
    """

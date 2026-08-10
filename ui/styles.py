import streamlit as st


def get_app_css():
    return """
    <style>

    /* ==============================
       GLOBAL
    ============================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    [data-testid="stAppViewContainer"] {
        background: #212121;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #171717;
        border-right: 1px solid #303030;
    }

    [data-testid="stSidebarContent"] {
        padding: 12px;
    }


    /* ==============================
       MAIN CONTENT
    ============================== */

    .main-title {
        text-align: center;
        font-size: 30px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 35px;
        margin-bottom: 8px;
    }

    .main-subtitle {
        text-align: center;
        color: #a0a0a0;
        font-size: 14px;
        margin-bottom: 35px;
    }


    /* ==============================
       CHAT MESSAGE AREA
    ============================== */

    [data-testid="stChatMessage"] {
        background: transparent;
        border: none;
        padding: 18px 10px;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stChatMessageContent"] {
        color: #ececec;
        font-size: 15px;
        line-height: 1.65;
    }


    /* ==============================
       CHAT INPUT
    ============================== */

    [data-testid="stChatInput"] {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stChatInput"] > div {
        background: #2f2f2f;
        border: 1px solid #454545;
        border-radius: 24px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    }

    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        background: transparent !important;
        font-size: 15px;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #999999 !important;
    }


    /* ==============================
       UPLOAD
    ============================== */

    [data-testid="stFileUploader"] {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #2f2f2f;
        border: 1px solid #454545;
        border-radius: 18px;
    }


    /* ==============================
       SIDEBAR
    ============================== */

    .sidebar-brand {
        color: #ffffff;
        font-size: 19px;
        font-weight: 700;
        padding: 8px 6px 18px 6px;
    }

    .sidebar-section {
        color: #9b9b9b;
        font-size: 12px;
        font-weight: 600;
        margin-top: 18px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }


    /* ==============================
       BUTTONS
    ============================== */

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #3d3d3d;
        background: #212121;
        color: #eeeeee;
        min-height: 40px;
    }

    .stButton > button:hover {
        background: #2f2f2f;
        border-color: #555555;
    }


    /* ==============================
       SELECTBOX
    ============================== */

    [data-testid="stSelectbox"] > div > div {
        background: #212121;
        border-color: #3d3d3d;
        border-radius: 10px;
    }


    /* ==============================
       STATUS
    ============================== */

    [data-testid="stAlert"] {
        border-radius: 10px;
    }


    /* ==============================
       FILE CHIPS
    ============================== */

    .file-chip {
        display: inline-block;
        background: #303030;
        color: #dddddd;
        border: 1px solid #444444;
        border-radius: 10px;
        padding: 6px 10px;
        margin: 3px;
        font-size: 12px;
    }


    /* ==============================
       SCROLLBAR
    ============================== */

    ::-webkit-scrollbar {
        width: 8px;
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

    </style>
    """

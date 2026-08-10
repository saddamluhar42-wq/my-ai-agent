import streamlit as st


def get_app_css():
    return """
<style>

/* ============================================================
   GLOBAL
============================================================ */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/*
IMPORTANT:
Do NOT hide Streamlit header.
The sidebar expand/collapse control lives here.
*/
[data-testid="stHeader"] {
    background: transparent !important;
}

/* Main application background */

[data-testid="stAppViewContainer"] {
    background: #212121;
}

[data-testid="stMain"] {
    background: #212121;
}


/* ============================================================
   SIDEBAR
============================================================ */

[data-testid="stSidebar"] {
    background: #171717 !important;
    border-right: 1px solid #303030;
}

[data-testid="stSidebarContent"] {
    padding: 14px 12px 20px 12px;
}

/* Sidebar scrollbar */

[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 7px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-track {
    background: #171717;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: #3f3f3f;
    border-radius: 10px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
    background: #555555;
}


/* ============================================================
   SIDEBAR BRAND
============================================================ */

.sidebar-brand {
    color: #ffffff;
    font-size: 19px;
    font-weight: 700;
    line-height: 1.2;
    padding: 8px 6px 4px 6px;
}

.sidebar-version {
    color: #777777;
    font-size: 12px;
    padding: 0 6px 12px 6px;
}

.sidebar-section {
    color: #a0a0a0;
    font-size: 11px;
    font-weight: 700;
    margin-top: 18px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}


/* ============================================================
   MAIN CONTENT
============================================================ */

.main-title {
    text-align: center;
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
    margin-top: 20px;
    margin-bottom: 8px;
}

.main-subtitle {
    text-align: center;
    color: #9b9b9b;
    font-size: 14px;
    margin-bottom: 30px;
}


/* ============================================================
   CHAT AREA
============================================================ */

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
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


/* ============================================================
   CHAT INPUT
============================================================ */

[data-testid="stChatInput"] {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    padding-bottom: 10px;
}

[data-testid="stChatInput"] > div {
    background: #2f2f2f !important;
    border: 1px solid #454545 !important;
    border-radius: 24px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.30);
}

[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background: transparent !important;
    font-size: 15px;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #999999 !important;
}


/* ============================================================
   CHAT INPUT BUTTON
============================================================ */

[data-testid="stChatInput"] button {
    border-radius: 50%;
}


/* ============================================================
   FILE UPLOAD
============================================================ */

[data-testid="stFileUploader"] {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
}

[data-testid="stFileUploaderDropzone"] {
    background: #2f2f2f !important;
    border: 1px solid #454545 !important;
    border-radius: 16px !important;
}


/* ============================================================
   BUTTONS
============================================================ */

.stButton > button {
    width: 100%;
    min-height: 40px;
    border-radius: 10px;
    border: 1px solid #3d3d3d;
    background: #212121;
    color: #eeeeee;
    font-size: 14px;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background: #303030;
    border-color: #555555;
    color: #ffffff;
}

.stButton > button:focus {
    border-color: #666666;
    box-shadow: none;
}


/* ============================================================
   SIDEBAR BUTTONS
============================================================ */

[data-testid="stSidebar"] .stButton > button {
    background: #212121;
    border: 1px solid #3d3d3d;
    color: #eeeeee;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #303030;
    border-color: #555555;
}


/* ============================================================
   SELECTBOX
============================================================ */

[data-testid="stSelectbox"] {
    margin-bottom: 4px;
}

[data-testid="stSelectbox"] > div > div {
    background: #212121 !important;
    border: 1px solid #3d3d3d !important;
    border-radius: 10px !important;
}

[data-testid="stSelectbox"] label {
    color: #aaaaaa !important;
}


/* ============================================================
   STATUS / ALERTS
============================================================ */

[data-testid="stAlert"] {
    border-radius: 10px;
}


/* ============================================================
   SERVICE STATUS
============================================================ */

.service-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 2px;
    font-size: 13px;
}

.service-name {
    color: #dddddd;
}

.service-status {
    color: #888888;
    font-size: 11px;
}

.service-status.connected {
    color: #9a9a9a;
}

.service-status.offline {
    color: #777777;
}


/* ============================================================
   EMPTY STATE
============================================================ */

.empty-state {
    max-width: 760px;
    margin: 80px auto 0 auto;
    text-align: center;
}

.empty-state-icon {
    width: 72px;
    height: 72px;
    margin: 0 auto 25px auto;
    border-radius: 50%;
    background: #303030;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.empty-state-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.empty-state-title {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
}

.empty-state-subtitle {
    color: #999999;
    font-size: 14px;
    line-height: 1.6;
}


/* ============================================================
   QUICK ACTIONS
============================================================ */

.quick-actions {
    max-width: 900px;
    margin: 30px auto 0 auto;
}

.quick-action-button {
    background: #212121;
    border: 1px solid #3d3d3d;
    border-radius: 12px;
    color: #eeeeee;
    padding: 12px;
    text-align: center;
    font-size: 13px;
}


/* ============================================================
   FILE CHIPS
============================================================ */

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


/* ============================================================
   IMAGE RESULT
============================================================ */

.generated-image-container {
    max-width: 900px;
    margin: 15px auto;
    text-align: center;
}

.generated-image-container img {
    max-width: 100%;
    border-radius: 14px;
}


/* ============================================================
   DOWNLOAD BUTTON
============================================================ */

[data-testid="stDownloadButton"] button {
    border-radius: 10px;
    border: 1px solid #444444;
    background: #2b2b2b;
    color: #ffffff;
}

[data-testid="stDownloadButton"] button:hover {
    background: #383838;
}


/* ============================================================
   DIVIDERS
============================================================ */

hr {
    border-color: #303030 !important;
}


/* ============================================================
   CAPTION
============================================================ */

.stCaption {
    color: #777777 !important;
}


/* ============================================================
   CODE BLOCKS
============================================================ */

[data-testid="stCodeBlock"] {
    border-radius: 12px;
}


/* ============================================================
   MARKDOWN LINKS
============================================================ */

a {
    color: #d0d0d0 !important;
}


/* ============================================================
   SCROLLBAR — MAIN
============================================================ */

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
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


/* ============================================================
   RESPONSIVE
============================================================ */

@media (max-width: 900px) {

    .empty-state {
        margin-top: 50px;
        padding: 0 20px;
    }

    .empty-state-title {
        font-size: 24px;
    }

    [data-testid="stChatInput"] {
        padding-left: 10px;
        padding-right: 10px;
    }

    [data-testid="stChatMessage"] {
        padding-left: 8px;
        padding-right: 8px;
    }
}

</style>
"""

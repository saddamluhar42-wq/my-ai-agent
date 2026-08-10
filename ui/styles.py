APP_CSS = """
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

.main-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.main-subtitle {
    opacity: 0.7;
    margin-bottom: 1.5rem;
}

.agent-status {
    padding: 0.6rem 0.8rem;
    border-radius: 0.6rem;
    background: rgba(128, 128, 128, 0.12);
    margin-bottom: 1rem;
}

.chat-user {
    padding: 0.9rem 1rem;
    border-radius: 0.8rem;
    margin: 0.5rem 0;
    background: rgba(70, 130, 180, 0.12);
}

.chat-assistant {
    padding: 0.9rem 1rem;
    border-radius: 0.8rem;
    margin: 0.5rem 0;
    background: rgba(128, 128, 128, 0.10);
}

.file-box {
    padding: 0.8rem;
    border-radius: 0.7rem;
    border: 1px solid rgba(128, 128, 128, 0.25);
    margin-bottom: 0.5rem;
}

.small-muted {
    font-size: 0.82rem;
    opacity: 0.65;
}

</style>
"""


def get_app_css():
    return APP_CSS

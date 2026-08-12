"""Offline smoke test for the current lightweight agent architecture.

This test intentionally avoids API calls, databases, external plugin execution,
and provider credentials. It validates that the modules used by the deployed
Streamlit app can be imported and that their core contracts are intact.
"""
from __future__ import annotations


def main() -> None:
    import streamlit

    from agent.core import AgentCore, ExecutionResult, get_agent_core, run_agent
    from agent.task_scheduler import DEFAULT_TIMEZONE
    from database.chat_history import list_recent_chats, load_chat, save_chat
    from database.tasks import list_tasks
    from plugins.coder import plugin as coder_plugin
    from plugins.manager import fetch_manifest, plugin_payload
    from plugins.router import router

    assert streamlit.__version__
    assert isinstance(get_agent_core(), AgentCore)
    assert isinstance(run_agent.__name__, str)
    assert ExecutionResult(answer="ok").success is True
    assert DEFAULT_TIMEZONE

    assert callable(list_recent_chats)
    assert callable(load_chat)
    assert callable(save_chat)
    assert callable(list_tasks)
    assert callable(fetch_manifest)
    assert callable(plugin_payload)
    assert callable(router.select)

    assert coder_plugin.name == "Coder"
    assert coder_plugin.version
    assert "code_generation" in coder_plugin.capabilities
    assert coder_plugin.execution == "external_https_sandbox"

    # Verify the core rejects an empty request without touching an AI provider.
    result = get_agent_core().run("")
    assert result.success is False
    assert result.answer

    print("CURRENT_AGENT_INTEGRATION_SMOKE: PASS")


if __name__ == "__main__":
    main()

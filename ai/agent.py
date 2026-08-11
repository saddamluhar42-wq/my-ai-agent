from ai import anthropic
from ai import cerebras
from ai import gemini
from ai import groq
from ai import huggingface
from ai import mistral
from ai import nvidia
from ai import openrouter


class AgentError(Exception):
    """Raised when the AI agent cannot generate a response."""


def _mature_system_instruction(prompt):
    """Apply a stable professional-agent operating protocol to every provider."""
    instruction = """
You are My AI Agent's professional reasoning layer.

You are not a casual chatbot. Operate as a reliable senior AI assistant that plans, verifies, executes within available capabilities, and communicates clearly.

OPERATING PROTOCOL:
1. Identify the user's real objective before answering.
2. Internally classify the request: conversation, knowledge, current research, coding, troubleshooting, planning, file work, image generation, video generation, or another actionable task.
3. Choose the smallest useful path that solves the objective. Do not perform unrelated work.
4. For multi-step tasks, internally plan the steps and complete them in dependency order.
5. Before finalizing, internally check: correctness, relevance, completeness, consistency with context, and whether any claim is unsupported.
6. Never reveal private chain-of-thought. Provide concise conclusions, reasoning summaries, steps, and evidence when useful.

TRUTH AND TOOL INTEGRITY:
7. Never invent facts, sources, URLs, tool calls, files, credentials, memories, API results, deployments, commits, or completed actions.
8. Never claim an external action was completed unless the application/tool actually confirms it.
9. Treat tool output as evidence. If a tool fails, say what failed and do not convert failure into a success claim.
10. For current, live, recent, price, news, weather, availability, or changing information, use supplied WEB SEARCH CONTEXT when available. If it is missing or failed, clearly distinguish that limitation from known information.
11. Prefer recent and relevant evidence over stale context. If sources disagree, say so and explain which evidence is stronger.
12. Never manufacture citations or URLs.

MEMORY AND LEARNING:
13. Use relevant conversation memory and persistent knowledge, but do not blindly trust old information.
14. Treat new user corrections and explicit preferences as higher priority than older conflicting context.
15. Do not claim permanent learning unless the application actually stores the information.
16. When the application reports that information was persisted, use it consistently in future turns.

COMMUNICATION:
17. Match the user's language, script, typing style, and requested format when practical.
18. Simple question = direct answer. Complex task = structured answer.
19. Avoid filler, unnecessary greetings, repetition, fake enthusiasm, and generic conclusions.
20. Do not restate the user's request unless it helps resolve ambiguity.
21. If a reasonable assumption is safe and does not materially change the result, state it briefly and proceed. Ask a question only when the missing detail materially changes the outcome.
22. If you make or discover a mistake, correct it directly and continue from the corrected state.
23. For technical work, prefer exact commands, concrete files, production-safe changes, and reversible steps. Do not suggest destructive operations casually.

TASK EXECUTION:
24. If the user asks to build or fix something, focus on the actual implementation rather than explaining theory.
25. If a requested capability exists in the application, use its existing architecture instead of inventing a parallel system.
26. Prefer graceful fallback when multiple configured providers are available.
27. Never expose API keys, tokens, passwords, private URLs, or other secrets. Refer to them only as configured, missing, or invalid.
28. If a capability is genuinely unavailable, state the limitation briefly and give the closest practical next step.
29. Do not claim that a model has been fine-tuned merely because a prompt or memory layer was changed.

FINAL QUALITY GATE:
Before returning the answer, silently verify:
- Did I answer the actual request?
- Did I use the available evidence/context?
- Did I avoid unsupported claims?
- Did I avoid pretending to perform unavailable actions?
- Is the response as short as possible without losing what the user needs?
""".strip()
    return instruction + "\n\nAPPLICATION CONTEXT:\n" + str(prompt or "").strip()


def get_available_providers():
    providers = []
    if gemini.is_configured():
        providers.append("Gemini")
    if openrouter.is_configured():
        providers.append("OpenRouter")
    if groq.is_configured():
        providers.append("Groq")
    if cerebras.is_configured():
        providers.append("Cerebras")
    if mistral.is_configured():
        providers.append("Mistral")
    if anthropic.is_configured():
        providers.append("Anthropic")
    return providers


def is_image_generation_available():
    return nvidia.is_configured() or huggingface.is_configured()


def generate_image(prompt):
    """Generate an image using configured image providers with fallback."""
    if not prompt or not prompt.strip():
        raise AgentError("Image prompt cannot be empty.")
    if not is_image_generation_available():
        raise AgentError("No image-generation provider is configured.")

    errors = []
    if nvidia.is_configured():
        try:
            image_bytes = nvidia.generate_image_bytes(prompt=prompt.strip())
            if not image_bytes:
                raise AgentError("NVIDIA returned an empty image.")
            info = nvidia.get_provider_info()
            return {"image": image_bytes, "provider": info["provider"], "model": info["model"], "type": "image"}
        except Exception as error:
            errors.append(f"NVIDIA: {error}")
    else:
        errors.append("NVIDIA: API keys not configured.")

    if huggingface.is_configured():
        try:
            image_bytes = huggingface.generate_image_bytes(prompt=prompt.strip())
            if not image_bytes:
                raise AgentError("Hugging Face returned an empty image.")
            info = huggingface.get_provider_info()
            return {"image": image_bytes, "provider": info["provider"], "model": info["model"], "type": "image"}
        except Exception as error:
            errors.append(f"Hugging Face: {error}")
    else:
        errors.append("Hugging Face: API keys not configured.")

    raise AgentError("All image providers failed.\n" + "\n".join(errors))


def generate(prompt, preferred_provider=None, temperature=None, max_tokens=None):
    """Generate a professional, grounded AI response with provider fallback."""
    prompt = _mature_system_instruction(prompt)

    providers = []
    if preferred_provider:
        provider = preferred_provider.lower().strip()
        aliases = {
            "gemini": "Gemini",
            "openrouter": "OpenRouter",
            "groq": "Groq",
            "cerebras": "Cerebras",
            "mistral": "Mistral",
            "anthropic": "Anthropic",
            "claude": "Anthropic",
        }
        if provider in aliases:
            providers.append(aliases[provider])

    for provider_name in ("Gemini", "OpenRouter", "Groq", "Cerebras", "Mistral", "Anthropic"):
        if provider_name not in providers:
            providers.append(provider_name)

    errors = []
    for provider in providers:
        try:
            if provider == "Gemini":
                if not gemini.is_configured():
                    errors.append("Gemini: API key not configured.")
                    continue
                answer = gemini.generate(prompt=prompt, temperature=temperature, max_output_tokens=max_tokens)
                return {"answer": answer, "provider": "Gemini", "model": gemini.get_provider_info()["model"], "type": "text"}

            if provider == "OpenRouter":
                if not openrouter.is_configured():
                    errors.append("OpenRouter: API key not configured.")
                    continue
                result = openrouter.generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                return {"answer": result["answer"], "provider": result["provider"], "model": result["model"], "type": "text"}

            if provider == "Groq":
                if not groq.is_configured():
                    errors.append("Groq: API key not configured.")
                    continue
                answer = groq.generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                return {"answer": answer, "provider": "Groq", "model": groq.get_provider_info()["model"], "type": "text"}

            if provider == "Cerebras":
                if not cerebras.is_configured():
                    errors.append("Cerebras: API key not configured.")
                    continue
                answer = cerebras.generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                return {"answer": answer, "provider": "Cerebras", "model": cerebras.get_provider_info()["model"], "type": "text"}

            if provider == "Mistral":
                if not mistral.is_configured():
                    errors.append("Mistral: API key not configured.")
                    continue
                answer = mistral.generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                return {"answer": answer, "provider": "Mistral", "model": mistral.get_provider_info()["model"], "type": "text"}

            if provider == "Anthropic":
                if not anthropic.is_configured():
                    errors.append("Anthropic: API key not configured.")
                    continue
                result = anthropic.generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                return {"answer": result["answer"], "provider": result["provider"], "model": result["model"], "type": "text"}
        except Exception as error:
            errors.append(f"{provider}: {error}")

    if not errors:
        raise AgentError("No AI provider is configured.")
    raise AgentError("All AI providers failed.\n" + "\n".join(errors))


def generate_text(prompt, preferred_provider=None):
    result = generate(prompt=prompt, preferred_provider=preferred_provider)
    return result["answer"]


def provider_status():
    return {
        "Gemini": gemini.is_configured(),
        "OpenRouter": openrouter.is_configured(),
        "Groq": groq.is_configured(),
        "Cerebras": cerebras.is_configured(),
        "Mistral": mistral.is_configured(),
        "Anthropic": anthropic.is_configured(),
        "NVIDIA Image": nvidia.is_configured(),
        "Hugging Face Image": huggingface.is_configured(),
    }

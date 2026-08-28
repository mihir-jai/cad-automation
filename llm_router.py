"""
Direct LLM router — no litellm dependency.
Uses plain HTTP requests against each provider's REST API with a fallback chain.
All providers use the OpenAI-compatible /chat/completions format except Gemini.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = 30  # seconds

# The fallback chain: (provider, model, url, api_key, style)
# style: "openai" = OpenAI-compatible chat/completions, "gemini" = Google generateContent
FALLBACK_CHAIN = [
    # --- PRIMARY FLEET: Gemini (best for spatial geometry) ---
    ("GEMINI", "gemini-3.6-flash",
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
     os.environ.get("GEMINI_KEY_1"), "gemini"),
    ("GEMINI", "gemini-3.6-flash",
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
     os.environ.get("GEMINI_KEY_2"), "gemini"),
    ("GEMINI", "gemini-3.6-flash",
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
     os.environ.get("GEMINI_KEY_3"), "gemini"),

    # --- FALLBACK 1: Mistral ---
    ("MISTRAL", "mistral-medium-2508",
     "https://api.mistral.ai/v1/chat/completions",
     os.environ.get("MISTRAL_KEY_1"), "openai"),
    ("MISTRAL", "mistral-medium-2508",
     "https://api.mistral.ai/v1/chat/completions",
     os.environ.get("MISTRAL_KEY_2"), "openai"),
    ("MISTRAL", "mistral-medium-2508",
     "https://api.mistral.ai/v1/chat/completions",
     os.environ.get("MISTRAL_KEY_3"), "openai"),

    # --- FALLBACK 2: Groq (current model IDs) ---
    ("GROQ", "openai/gpt-oss-120b",
     "https://api.groq.com/openai/v1/chat/completions",
     os.environ.get("GROQ_KEY_1"), "openai"),
    ("GROQ", "openai/gpt-oss-120b",
     "https://api.groq.com/openai/v1/chat/completions",
     os.environ.get("GROQ_KEY_2"), "openai"),
    ("GROQ", "openai/gpt-oss-120b",
     "https://api.groq.com/openai/v1/chat/completions",
     os.environ.get("GROQ_KEY_3"), "openai"),

    # --- FALLBACK 3: Cerebras (current model IDs) ---
    ("CEREBRAS", "gpt-oss-120b",
     "https://api.cerebras.ai/v1/chat/completions",
     os.environ.get("CEREBRAS_KEY_1"), "openai"),
    ("CEREBRAS", "gpt-oss-120b",
     "https://api.cerebras.ai/v1/chat/completions",
     os.environ.get("CEREBRAS_KEY_2"), "openai"),
    ("CEREBRAS", "gpt-oss-120b",
     "https://api.cerebras.ai/v1/chat/completions",
     os.environ.get("CEREBRAS_KEY_3"), "openai"),

    # --- FALLBACK 4: Cohere (command-r-plus was removed; use 08-2024 version) ---
    ("COHERE", "command-r-plus-08-2024",
     "https://api.cohere.ai/compatibility/v1/chat/completions",
     os.environ.get("COHERE_KEY_1"), "openai"),
    ("COHERE", "command-r-plus-08-2024",
     "https://api.cohere.ai/compatibility/v1/chat/completions",
     os.environ.get("COHERE_KEY_2"), "openai"),
    ("COHERE", "command-r-plus-08-2024",
     "https://api.cohere.ai/compatibility/v1/chat/completions",
     os.environ.get("COHERE_KEY_3"), "openai"),

    # --- THE FINAL BOSS: NVIDIA NIM (correct endpoint + current model) ---
    ("NVIDIA_NIM", "meta/llama-3.3-70b-instruct",
     "https://integrate.api.nvidia.com/v1/chat/completions",
     os.environ.get("NVIDIA_KEY_1"), "openai"),
]


def _call_openai_compatible(url, api_key, model, system_prompt, user_input):
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(url, api_key, model, system_prompt, user_input):
    resp = requests.post(
        f"{url}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_input}]}],
            "generationConfig": {"temperature": 0.2},
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def get_ai_response(user_input, system_prompt):
    """Try every provider in the fallback chain until one succeeds."""
    for provider, model, url, api_key, style in FALLBACK_CHAIN:
        if not api_key:
            print(f"  [!] {provider} skipped: no API key in .env")
            continue

        print(f"  -> Asking {provider} ({model})...")

        try:
            if style == "gemini":
                return _call_gemini(url, api_key, model, system_prompt, user_input)
            else:
                return _call_openai_compatible(url, api_key, model, system_prompt, user_input)
        except requests.exceptions.Timeout:
            print(f"  [!] {provider} failed: timed out after {TIMEOUT}s")
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.text[:200]
            except Exception:
                pass
            print(f"  [!] {provider} failed: HTTP {e.response.status_code} {detail}")
        except Exception as e:
            print(f"  [!] {provider} failed: {e}")

    print("[!] All AI providers failed!")
    return None
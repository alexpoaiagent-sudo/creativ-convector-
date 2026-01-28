#!/usr/bin/env python3
"""
Мульти-провайдер AI: поддержка Claude (Anthropic) и ChatGPT (OpenAI)
Единый интерфейс для всех AI-скриптов в Obsidian
"""

import os
from pathlib import Path

# Путь к vault
VAULT_PATH = Path(__file__).parent.parent.parent


def load_env():
    """Загрузить переменные из .env файла"""
    env_file = VAULT_PATH / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_provider(provider_name=None):
    """
    Получить AI провайдера.

    provider_name: 'claude' или 'openai'.
    Если не указан — пробует claude, потом openai.
    """
    load_env()

    if provider_name == "claude" or provider_name is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            return ClaudeProvider(api_key)
        if provider_name == "claude":
            raise ValueError("ANTHROPIC_API_KEY не найден. Добавьте его в .env файл.")

    if provider_name == "openai" or provider_name is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return OpenAIProvider(api_key)
        if provider_name == "openai":
            raise ValueError("OPENAI_API_KEY не найден. Добавьте его в .env файл.")

    raise ValueError(
        "Ни один AI провайдер не настроен.\n"
        "Добавьте в .env файл:\n"
        "  ANTHROPIC_API_KEY=sk-ant-...\n"
        "  или\n"
        "  OPENAI_API_KEY=sk-..."
    )


class ClaudeProvider:
    """Провайдер Claude (Anthropic)"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.name = "Claude"
        self.model = "claude-sonnet-4-20250514"

    def chat(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        """Отправить запрос к Claude API"""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Библиотека anthropic не установлена.\n"
                "Установите: pip3 install anthropic"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )

        return response.content[0].text


class OpenAIProvider:
    """Провайдер ChatGPT (OpenAI)"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.name = "ChatGPT"
        self.model = "gpt-4o-mini"

    def chat(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        """Отправить запрос к OpenAI API"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "Библиотека openai не установлена.\n"
                "Установите: pip3 install openai"
            )

        client = OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

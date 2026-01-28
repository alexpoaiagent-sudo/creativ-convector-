#!/usr/bin/env python3
"""
AI Agent для анализа недельных отчётов в Obsidian.
Поддерживает Claude (Anthropic) и ChatGPT (OpenAI).
"""

import os
import sys
from datetime import datetime

# Добавляем путь к скриптам
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_provider import get_provider


def analyze_report(file_path, provider):
    """Analyze weekly report using AI"""

    # Read the report
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return None

    system_prompt = "Ты эксперт по стратегическому планированию и продуктивности."

    user_prompt = f"""Проанализируй этот недельный отчёт и предоставь:

1. **Анализ достижений**: Что сделано хорошо?
2. **Выявление паттернов**: Какие тренды видны?
3. **Рекомендации**: Что улучшить на следующей неделе?
4. **Приоритеты**: Что самое важное?
5. **Риски**: Какие потенциальные проблемы?

Отчёт:
---
{content}
---

Предоставь структурированный анализ на русском языке в формате Markdown."""

    try:
        print(f"[{provider.name}] Анализирую отчёт...")

        analysis = provider.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
            temperature=0.7
        )

        # Save analysis
        output_path = file_path.replace('.md', ' - AI Анализ.md')
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# AI Анализ отчёта\n\n")
            f.write(f"**Дата анализа:** {now}\n")
            f.write(f"**Провайдер:** {provider.name} ({provider.model})\n\n")
            f.write("---\n\n")
            f.write(analysis)

        print(f"[{provider.name}] Анализ сохранён: {output_path}")
        return output_path

    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 ai_agent.py <путь_к_отчёту> [claude|openai]")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        sys.exit(1)

    # Определяем провайдера
    provider_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        provider = get_provider(provider_name)
    except (ValueError, ImportError) as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    analyze_report(file_path, provider)

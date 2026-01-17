#!/usr/bin/env python3
"""
Enrich Obsidian notes using OpenAI API
Finds changed markdown files and enriches them with AI-generated content
"""

import os
import sys
import subprocess
from pathlib import Path
from openai import OpenAI

def get_changed_files():
    """Get list of changed markdown files"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

        files = result.stdout.strip().split('\n')
        md_files = [f for f in files if f.endswith('.md') and os.path.exists(f)]

        print(f"📝 Found {len(md_files)} changed markdown files")
        return md_files

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not get changed files: {e}")
        return []

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return None

def enrich_note(content, filepath):
    """Enrich note content using OpenAI"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты помощник для улучшения заметок в Obsidian.

Файл: {filepath}

Задача:
1. Проанализируй содержимое заметки
2. Улучши структуру и форматирование
3. Добавь недостающие связи и теги если уместно
4. Исправь опечатки и грамматику
5. Сохрани оригинальный смысл и стиль автора

ВАЖНО:
- Не удаляй существующий контент
- Не меняй радикально структуру
- Добавляй только полезные улучшения
- Сохраняй все ссылки [[]] и теги #

Верни улучшенную версию заметки в формате Markdown.

Оригинальная заметка:
---
{content}
---
"""

    try:
        print(f"🤖 Enriching: {filepath}")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по организации знаний и заметок в Obsidian."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        enriched = response.choices[0].message.content.strip()

        if enriched.startswith("```markdown"):
            enriched = enriched.split("```markdown")[1].split("```")[0].strip()
        elif enriched.startswith("```"):
            enriched = enriched.split("```")[1].split("```")[0].strip()

        print(f"✅ Enriched: {filepath}")
        return enriched

    except Exception as e:
        print(f"❌ Error enriching {filepath}: {e}")
        return None

def write_file(filepath, content):
    """Write content to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Saved: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error writing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 Obsidian Notes Enrichment")
    print("=" * 60)

    changed_files = get_changed_files()

    if not changed_files:
        print("ℹ️  No markdown files to enrich")
        return

    enriched_count = 0

    for filepath in changed_files:
        print(f"\n📄 Processing: {filepath}")

        content = read_file(filepath)
        if not content:
            continue

        if len(content.strip()) < 50:
            print(f"⏭️  Skipping (too short): {filepath}")
            continue

        enriched = enrich_note(content, filepath)
        if not enriched:
            continue

        if enriched != content:
            if write_file(filepath, enriched):
                enriched_count += 1
        else:
            print(f"ℹ️  No changes needed: {filepath}")

    print("\n" + "=" * 60)
    print(f"✨ Enriched {enriched_count} files")
    print("=" * 60)

if __name__ == "__main__":
    main()

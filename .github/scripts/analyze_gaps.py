#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа пробелов в VK-offee
и поиска информации в creativ-convector
"""

import os
from pathlib import Path
import re
from datetime import datetime

# Пути к репозиториям
VK_OFFEE_PATH = Path("/Users/alexander/Github/VK-offee")
CONVECTOR_PATH = Path("/Users/alexander/Github/creativ-convector")

def analyze_gaps_in_vk_offee():
    """Анализ пробелов в VK-offee"""
    print("🔍 Анализ пробелов в VK-offee...\n")
    gaps = []

    # Читаем knowledge-inventory.md
    inventory_file = VK_OFFEE_PATH / "content" / "0.Management" / "0.1. Логика хранилища и знаний" / "knowledge-inventory.md"

    if not inventory_file.exists():
        print(f"❌ Файл не найден: {inventory_file}")
        return gaps

    with open(inventory_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем документы со статусом yellow/red
    lines = content.split('\n')
    for line in lines:
        if '|' in line and ('yellow' in line or 'red' in line):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                doc_name = parts[1]
                status = parts[3] if len(parts) > 3 else 'unknown'

                if status in ['yellow', 'red']:
                    priority = 'high' if status == 'red' else 'medium'
                    gaps.append({
                        'document': doc_name,
                        'status': status,
                        'priority': priority
                    })

    # Проверяем файлы напрямую
    content_dir = VK_OFFEE_PATH / "content"
    if content_dir.exists():
        for md_file in content_dir.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                # Ищем frontmatter со статусом
                frontmatter_match = re.match(r'^---\n(.*?)\n---', file_content, re.DOTALL)
                if frontmatter_match:
                    frontmatter = frontmatter_match.group(1)
                    status_match = re.search(r'status:\s*["\']?(yellow|red)["\']?', frontmatter)

                    if status_match:
                        status = status_match.group(1)
                        priority = 'high' if status == 'red' else 'medium'

                        # Проверяем, не добавили ли уже
                        doc_name = md_file.stem
                        if not any(g['document'] == doc_name for g in gaps):
                            gaps.append({
                                'document': doc_name,
                                'status': status,
                                'priority': priority,
                                'path': str(md_file.relative_to(VK_OFFEE_PATH))
                            })
            except Exception as e:
                pass

    return gaps

def search_in_convector(keywords):
    """Поиск информации в creativ-convector"""
    results = []

    # Поиск в черновиках VK-Coffee
    drafts_dir = CONVECTOR_PATH / "2. Черновики" / "VK-Coffee"
    if drafts_dir.exists():
        for file_path in drafts_dir.rglob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        results.append({
                            'file': str(file_path.relative_to(CONVECTOR_PATH)),
                            'keyword': keyword,
                            'context': extract_context(content, keyword),
                            'source': 'Черновики'
                        })
                        break  # Один результат на файл
            except Exception:
                pass

    # Поиск в сессиях стратегирования
    sessions_dir = CONVECTOR_PATH / "Сессия стратегирования"
    if sessions_dir.exists():
        for file_path in sorted(sessions_dir.glob("*.md"), reverse=True)[:5]:  # Последние 5 сессий
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        results.append({
                            'file': str(file_path.relative_to(CONVECTOR_PATH)),
                            'keyword': keyword,
                            'context': extract_context(content, keyword),
                            'source': 'Сессия стратегирования'
                        })
                        break  # Один результат на файл
            except Exception:
                pass

    return results

def extract_context(content, keyword, context_size=200):
    """Извлечь контекст вокруг ключевого слова"""
    content_lower = content.lower()
    keyword_lower = keyword.lower()

    index = content_lower.find(keyword_lower)
    if index == -1:
        return ""

    start = max(0, index - context_size)
    end = min(len(content), index + len(keyword) + context_size)

    context = content[start:end]

    # Очищаем от лишних символов
    context = context.replace('\n', ' ').strip()

    return context[:300]  # Максимум 300 символов

def generate_keywords(document_name):
    """Генерация ключевых слов из названия документа"""
    # Убираем расширение и разделяем по дефисам/пробелам
    name = document_name.replace('.md', '').replace('-', ' ').replace('_', ' ')

    # Разбиваем на слова
    words = name.lower().split()

    # Фильтруем короткие слова
    keywords = [w for w in words if len(w) > 3]

    # Добавляем синонимы для популярных тем
    synonyms = {
        'финанс': ['налог', 'прибыль', 'выручка', 'ebitda', 'деньги'],
        'команд': ['сотрудник', 'бариста', 'повар', 'персонал'],
        'меню': ['напиток', 'кофе', 'десерт', 'еда'],
        'процесс': ['операция', 'стандарт', 'процедура'],
    }

    for keyword in keywords[:]:
        for key, syns in synonyms.items():
            if key in keyword:
                keywords.extend(syns)
                break

    return list(set(keywords))[:10]  # Максимум 10 уникальных ключевых слов

def create_report(gaps, search_results):
    """Создание отчёта о найденных пробелах и информации"""
    report_lines = []

    report_lines.append("# 📊 Отчёт: Анализ пробелов VK-offee")
    report_lines.append(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"**Найдено пробелов:** {len(gaps)}")
    report_lines.append(f"**Найдено информации:** {len(search_results)}")
    report_lines.append("\n---\n")

    # Группируем по приоритетам
    high_priority = [g for g in gaps if g['priority'] == 'high']
    medium_priority = [g for g in gaps if g['priority'] == 'medium']

    if high_priority:
        report_lines.append("## 🔴 Высокий приоритет\n")
        for gap in high_priority:
            report_lines.append(f"### {gap['document']}")
            report_lines.append(f"**Статус:** {gap['status']}")

            # Ищем информацию для этого пробела
            gap_results = [r for r in search_results if r['gap'] == gap['document']]

            if gap_results:
                report_lines.append(f"**Найдено информации:** {len(gap_results)}\n")
                for result in gap_results[:3]:  # Первые 3
                    report_lines.append(f"- 📁 {result['file']}")
                    report_lines.append(f"  - Источник: {result['source']}")
                    report_lines.append(f"  - Ключевое слово: {result['keyword']}")
                    report_lines.append(f"  - Контекст: {result['context'][:150]}...")
                    report_lines.append("")
            else:
                report_lines.append("**Информация не найдена** ❌\n")

            report_lines.append("---\n")

    if medium_priority:
        report_lines.append("## 🟡 Средний приоритет\n")
        for gap in medium_priority[:5]:  # Первые 5
            report_lines.append(f"### {gap['document']}")
            gap_results = [r for r in search_results if r['gap'] == gap['document']]

            if gap_results:
                report_lines.append(f"**Найдено информации:** {len(gap_results)}")
                report_lines.append(f"- 📁 {gap_results[0]['file']}\n")
            else:
                report_lines.append("**Информация не найдена** ❌\n")

    return '\n'.join(report_lines)

def main():
    """Главная функция"""
    print("="*60)
    print("🔗 АГЕНТ СИНХРОНИЗАЦИИ")
    print("   creativ-convector → VK-offee")
    print("="*60 + "\n")

    # Этап 1: Анализ пробелов
    gaps = analyze_gaps_in_vk_offee()

    if not gaps:
        print("✅ Пробелов не найдено! VK-offee в отличном состоянии.")
        return

    print(f"📊 Найдено пробелов: {len(gaps)}\n")

    # Группируем по приоритетам
    high_priority = [g for g in gaps if g['priority'] == 'high']
    medium_priority = [g for g in gaps if g['priority'] == 'medium']

    print(f"🔴 Высокий приоритет: {len(high_priority)}")
    print(f"🟡 Средний приоритет: {len(medium_priority)}\n")

    # Этап 2: Поиск информации
    print("🔍 Поиск информации в creativ-convector...\n")

    all_search_results = []

    for gap in gaps:
        print(f"📄 {gap['document']}")

        # Генерируем ключевые слова
        keywords = generate_keywords(gap['document'])
        print(f"   Ключевые слова: {', '.join(keywords[:5])}")

        # Ищем информацию
        results = search_in_convector(keywords)

        if results:
            print(f"   ✅ Найдено: {len(results)} совпадений")
            for result in results:
                result['gap'] = gap['document']
                all_search_results.append(result)
        else:
            print(f"   ❌ Информация не найдена")

        print()

    # Этап 3: Создание отчёта
    print("\n" + "="*60)
    print("📝 Создание отчёта...")

    report = create_report(gaps, all_search_results)

    # Сохраняем отчёт
    report_file = CONVECTOR_PATH / "Сессия стратегирования" / f"АНАЛИЗ ПРОБЕЛОВ {datetime.now().strftime('%Y-%m-%d')}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Отчёт сохранён: {report_file.relative_to(CONVECTOR_PATH)}")
    print("\n" + "="*60)
    print("✅ АНАЛИЗ ЗАВЕРШЁН")
    print("="*60)

if __name__ == "__main__":
    main()

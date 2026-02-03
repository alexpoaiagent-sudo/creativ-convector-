# Инструкция по использованию ChatGPT MD плагина

## Проблема, которую мы исправили

**Было:**
- Модель: `anthropic@claude-sonnet-4-20250514` (с префиксом)
- Max tokens: 400 (слишком мало)
- Плагин не отвечал, показывал только "думает"

**Стало:**
- Модель: `claude-sonnet-4-20250514` (без префикса)
- Max tokens: 4096 (достаточно для ответов)
- API ключ: настроен правильно

## Как использовать ChatGPT MD в Obsidian

### Вариант 1: Создать новый чат (РЕКОМЕНДУЕТСЯ)

1. **Открыть Command Palette:**
   - Нажать `Cmd+P` (или `Ctrl+P`)

2. **Найти команду:**
   - Ввести: "ChatGPT MD: New Chat"
   - Выбрать эту команду

3. **Выбрать модель:**
   - В появившемся окне выбрать: **"claude-sonnet-4-20250514"**
   - Или просто нажать Enter (модель по умолчанию)

4. **Написать сообщение:**
   - В созданном файле найти строку `role::user`
   - Написать свой вопрос после этой строки
   - Нажать `Cmd+P` → "ChatGPT MD: Chat"

### Вариант 2: Добавить чат в существующую заметку

1. **Открыть любую заметку**

2. **Вызвать команду:**
   - `Cmd+P` → "ChatGPT MD: Add message"

3. **Написать вопрос и отправить**

### Вариант 3: Использовать готовый шаблон

Создайте файл с таким содержимым:

```markdown
---
system_commands:
  - You are a helpful assistant.
temperature: 0.7
max_tokens: 4096
model: claude-sonnet-4-20250514
stream: true
---

role::user

[Ваш вопрос здесь]

<hr class="__chatgpt_plugin">

role::assistant
```

Затем:
1. Напишите вопрос после `role::user`
2. Нажмите `Cmd+P` → "ChatGPT MD: Chat"
3. Claude ответит после `role::assistant`

## Важные команды

| Команда | Что делает |
|---------|------------|
| `ChatGPT MD: New Chat` | Создать новый чат с Claude |
| `ChatGPT MD: Chat` | Отправить сообщение в текущем чате |
| `ChatGPT MD: Add message` | Добавить сообщение в заметку |
| `ChatGPT MD: Improve writing` | Улучшить выделенный текст |
| `ChatGPT MD: Generate title` | Создать заголовок для заметки |

## Структура чата

```markdown
---
model: claude-sonnet-4-20250514  # Модель Claude
max_tokens: 4096                  # Максимум токенов
temperature: 0.7                  # Креативность (0-1)
stream: true                      # Потоковый вывод
---

role::user                        # Ваше сообщение
Привет! Как дела?

<hr class="__chatgpt_plugin">    # Разделитель

role::assistant                   # Ответ Claude
[Здесь появится ответ]

<hr class="__chatgpt_plugin">

role::user                        # Следующее сообщение
Расскажи подробнее
```

## Если не работает

### Проверка 1: API ключ
```bash
cat .obsidian/plugins/chatgpt-md/data.json | grep anthropicApiKey
```
Должен быть: `"anthropicApiKey": "sk-ant-api03-..."`

### Проверка 2: Модель
В frontmatter чата должно быть:
```yaml
model: claude-sonnet-4-20250514
```
**БЕЗ** префикса `anthropic@`

### Проверка 3: Плагин включен
1. Settings → Community Plugins
2. Найти "ChatGPT MD"
3. Убедиться, что переключатель включен

### Проверка 4: Перезагрузить Obsidian
Иногда помогает просто перезапустить Obsidian:
1. Закрыть Obsidian
2. Открыть снова
3. Попробовать создать новый чат

## Тестовый файл

Я создал тестовый файл: `ChatGPT_MD/chats/test-claude-fixed.md`

Попробуйте:
1. Открыть этот файл в Obsidian
2. Нажать `Cmd+P` → "ChatGPT MD: Chat"
3. Должен появиться ответ от Claude


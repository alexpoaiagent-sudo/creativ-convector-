#!/bin/bash
# Запуск сессии стратегирования

cd "$(dirname "$0")"
python3 .github/scripts/strategy_session.py

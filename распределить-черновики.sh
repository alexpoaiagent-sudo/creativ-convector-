#!/bin/bash
# Распределение черновиков по приоритетным проектам

cd "$(dirname "$0")"
python3 .github/scripts/distribute_drafts.py

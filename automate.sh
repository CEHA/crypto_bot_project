#!/bin/bash
# Автоматизація агента метапрограмування

cd /home/user/Source/Binance/crypto_bot_project

# Функція логування
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> automation.log
}

# Перевірка та запуск агента
run_agent() {
    log "Запуск циклу самовдосконалення..."
    
    # Bootstrap перевірка
    python3 bootstrap.py
    if [ $? -ne 0 ]; then
        log "Bootstrap failed, attempting auto-fix..."
        python3 run.py --mode auto
    fi
    
    # Основний цикл самовдосконалення
    python3 run.py --mode auto
    
    log "Цикл завершено"
}

# Моніторинг помилок
monitor_errors() {
    if [ -f "logs/agent_errors.log" ] && [ -s "logs/agent_errors.log" ]; then
        log "Виявлено помилки, запуск автовиправлення..."
        python3 unified_fixer.py
    fi
}

# Головна функція
main() {
    log "=== Початок автоматизованого циклу ==="
    
    # 1. Моніторинг помилок
    monitor_errors
    
    # 2. Запуск агента
    run_agent
    
    # 3. Очищення тимчасових файлів
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    
    log "=== Цикл завершено ==="
}

# Запуск
main
# Інструкція з використання Crypto Bot Project

## Встановлення

1. Клонуйте репозиторій:
   ```bash
   git clone https://github.com/username/crypto_bot_project.git
   cd crypto_bot_project
   ```

2. Встановіть залежності:
   ```bash
   pip install -r requirements.txt
   ```

3. Створіть файл `.env` з API ключем Gemini:
   ```bash
   cp .env.example .env
   # Відредагуйте файл .env, додавши свій API ключ
   ```

## Запуск

### Запуск в режимі агента

```bash
./run.py
```

або

```bash
./run.py --mode agent
```

### Запуск в режимі loader

```bash
./run.py --mode loader
```

### Додаткові параметри

```bash
./run.py --tasks my_tasks.json --config my_config.json --output my_output_dir
```

## Формат завдань

Завдання описуються у форматі JSON. Приклад файлу `tasks.json`:

```json
[
  {
    "type": "self_improvement",
    "improvement_type": "optimize_parameters",
    "config": {
      "optimize_temperature": true,
      "optimize_max_tokens": true,
      "optimize_retries": true
    }
  },
  {
    "type": "planning",
    "planning_type": "generate_initial_plan",
    "initial_task": "Розробити систему аналізу криптовалютного ринку"
  },
  {
    "type": "code_generation",
    "generation_type": "create_module",
    "requirements": {
      "module_name": "data_analyzer",
      "functions": ["analyze_market_trends", "calculate_indicators"]
    },
    "output_file": "data_analyzer.py"
  }
]
```

## Типи завдань

### 1. self_improvement

Завдання для самополіпшення агента.

```json
{
  "type": "self_improvement",
  "improvement_type": "optimize_parameters",
  "config": {
    "optimize_temperature": true,
    "optimize_max_tokens": true,
    "optimize_retries": true
  }
}
```

### 2. planning

Завдання для планування розробки.

```json
{
  "type": "planning",
  "planning_type": "generate_initial_plan",
  "initial_task": "Розробити систему аналізу криптовалютного ринку"
}
```

### 3. code_generation

Завдання для генерації коду.

```json
{
  "type": "code_generation",
  "generation_type": "create_module",
  "requirements": {
    "module_name": "data_analyzer",
    "functions": ["analyze_market_trends", "calculate_indicators"]
  },
  "output_file": "data_analyzer.py"
}
```

### 4. refactoring

Завдання для рефакторингу коду.

```json
{
  "type": "refactoring",
  "refactoring_type": "extract_method",
  "target_files": ["data_analyzer.py"],
  "options": {
    "start_line": 10,
    "end_line": 20,
    "new_method_name": "process_data"
  }
}
```

### 5. test

Завдання для тестування коду.

```json
{
  "type": "test",
  "test_type": "generate_tests",
  "target_files": ["data_analyzer.py"],
  "options": {
    "coverage": true,
    "verbose": true
  }
}
```

### 6. analysis

Завдання для аналізу коду та проекту.

```json
{
  "type": "analysis",
  "analysis_type": "code_quality",
  "target_files": ["data_analyzer.py"],
  "options": {
    "detailed": true
  }
}
```

### 7. query

Завдання для виконання запитів.

```json
{
  "type": "query",
  "query_type": "get_market_data",
  "params": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "limit": 10
  }
}
```

## Приклади використання

Для ознайомлення з системою можна запустити приклади:

```bash
# Приклад використання TaskQueue
./modules/examples/task_queue_example.py

# Приклад використання TaskDispatcher
./modules/examples/task_dispatcher_example.py
```

## Запуск тестів

```bash
# Запуск всіх тестів з генерацією звіту про покриття
pytest

# Після запуску буде створено директорію htmlcov/.
# Відкрийте htmlcov/index.html у вашому браузері, щоб переглянути детальний звіт.

# Запуск конкретного тестового файлу
pytest modules/tests/test_task_queue.py
```
FROM python:3.9-slim

# Установка переменных окружения
ENV PIP_DEFAULT_TIMEOUT=300
# Удаление кастомного индекса для повышения надежности, если это не обязательно.
# ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Установка рабочей директории
WORKDIR /app

# Копирование требований и установка зависимостей
COPY requirements.txt .

# Установка пакетов
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего исходного кода
# Важно: если main.py находится в src, то нам нужно добавить /app/src в PYTHONPATH
COPY . .

# Установка PYTHONPATH, чтобы Python мог найти пакеты, такие как 'providers'
# Если main.py вызывается как src.main, то /app должно быть в пути.
# Если вы используете структуру с папкой 'src', то:
ENV PYTHONPATH=/app/src:/app

# Запуск приложения
# Запуск uvicorn с указанием, что main.py находится в папке src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]

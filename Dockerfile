FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install -e .
# Если -e не подходит для твоего окружения, замени на: pip install -r requirements.txt
COPY . /app
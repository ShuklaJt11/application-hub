FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files (include README so Poetry can find it during install)
COPY pyproject.toml poetry.lock* /app/
COPY README.md /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim

WORKDIR /app

# Copy project configuration and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[dev]

# Copy the rest of your application code
COPY ./src /app/src
COPY ./alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Create a directory for the database file.
RUN mkdir -p /app/data

# Create a non-root user and give it ownership of the entire /app directory.
RUN useradd --create-home app && chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port that the application will run on.
EXPOSE 8000

CMD ["sh", "-c", "/usr/local/bin/alembic upgrade head && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000"]


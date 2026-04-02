# Build
FROM python:3.13-slim AS builder

WORKDIR /build

COPY app/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Runtime
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ .

# non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app

USER appuser

ENV FLASK_APP=app.py
EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

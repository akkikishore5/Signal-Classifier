# ── Stage 1: Build ──────────────────────────────────────────────────────────
# Install dependencies in a separate stage so they don't bloat the final image
FROM python:3.13-slim AS builder

WORKDIR /build

COPY app/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
# Only the installed packages and app code make it into the final image —
# no build tools, no pip cache, smaller attack surface
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ .

# Create a non-root user and group to run the app.
# Running as root inside a container is a security risk — if the app is
# compromised, an attacker would have root access to the container.
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user for all subsequent commands
USER appuser

ENV FLASK_APP=app.py
EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

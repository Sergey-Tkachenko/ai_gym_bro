FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    inetutils-ping \
    traceroute \
    pkg-config \
    default-libmysqlclient-dev \
    iptables ipset dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy only the files needed for Poetry
COPY pyproject.toml poetry.lock* ./

# Install dependencies globally
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction

ENTRYPOINT ["poetry", "run"] 
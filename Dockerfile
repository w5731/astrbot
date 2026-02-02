FROM python:3.11-slim
WORKDIR /AstrBot

COPY . /AstrBot/

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    ca-certificates \
    bash \
    ffmpeg \
    curl \
    gnupg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Dashboard is built in CI; context includes dashboard/dist. main.py uses it.
RUN python -m pip install uv \
    && echo "3.11" > .python-version
RUN uv pip install -r requirements.txt --no-cache-dir --system
RUN uv pip install socksio uv pilk --no-cache-dir --system

EXPOSE 6185

CMD ["python", "main.py"]

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

RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

# Build built-in frontend so main.py uses dashboard/dist (no data/dist or download)
RUN corepack enable pnpm \
    && cd /AstrBot/dashboard \
    && pnpm install \
    && pnpm run build \
    && mkdir -p dist/assets \
    && echo "built-in" > dist/assets/version

RUN python -m pip install uv \
    && echo "3.11" > .python-version
RUN uv pip install -r requirements.txt --no-cache-dir --system
RUN uv pip install socksio uv pilk --no-cache-dir --system

EXPOSE 6185

CMD ["python", "main.py"]

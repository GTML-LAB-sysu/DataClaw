FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    OPENCLAW_VERSION=2026.3.24

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3 \
    python3-pip \
    bash \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g "openclaw@${OPENCLAW_VERSION}"

RUN mkdir -p /tmp_workspace /root/.openclaw/workspace

ENTRYPOINT ["tini", "--"]
CMD ["tail", "-f", "/dev/null"]

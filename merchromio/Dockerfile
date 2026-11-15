FROM node:22-bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium \
    && rm -rf /var/lib/apt/lists/* \
    && PUPPETEER_SKIP_DOWNLOAD=true npm install --global @mermaid-js/mermaid-cli

FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 2001 merchromio \
    && useradd --uid 2001 --gid 2001 --create-home --shell /usr/sbin/nologin merchromio \
    && mkdir -p /opt/merchromio \
    && chmod 1777 /tmp

COPY --from=build /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY puppeteer-config.json /opt/merchromio/puppeteer-config.json

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
WORKDIR /tmp
USER 2001:2001
ENTRYPOINT ["node", "/usr/local/lib/node_modules/@mermaid-js/mermaid-cli/src/cli.js"]
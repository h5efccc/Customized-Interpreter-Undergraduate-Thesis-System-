# Stream the full Tkinter PNC simulator in a browser via noVNC.
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-tk \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

# Desktop GUI uses the standard library + system Tk; optional web deps are fine if present.
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages || true

EXPOSE 8080

RUN chmod +x /app/docker-start.sh

CMD ["sh", "/app/docker-start.sh"]

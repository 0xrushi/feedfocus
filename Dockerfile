FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && apt-get install -y \
    fluxbox \
    x11vnc \
    xvfb \
    chromium \
    xauth \
    x11-utils \
    dbus-x11 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxshmfence1 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    supervisor \
    python3-pip \
    python3 \
    python3-venv \
    python3-tk \
    python3-xlib \
    scrot \
    xterm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir pyautogui

RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

COPY press_pgdown.py /press_pgdown.py
COPY requirements.txt /requirements.txt

RUN chmod -R 777 /press_pgdown.py && chmod +x /press_pgdown.py
RUN chmod -R 777 /requirements.txt && chmod +x /requirements.txt

RUN /opt/venv/bin/pip install -r /requirements.txt

ENV DISPLAY=:0
ENV XAUTHORITY=/home/docker/.Xauthority
ENV CHROME_BIN=/usr/bin/chromium

RUN mkdir -p /opt/scripts

RUN echo '#!/bin/bash\n\
rm -f /tmp/.X0-lock\n\
rm -rf /tmp/.X11-unix/*\n\
Xvfb :0 -screen 0 1920x1080x24 -nolock &\n\
sleep 1\n\
# Generate Xauthority and allow local connections\n\
xauth generate :0 . trusted\n\
xhost +local:\n\
sleep 2\n\
fluxbox &\n\
sleep 2\n\
chromium \\\n\
  --no-sandbox \\\n\
  --enable-gpu-rasterization \\\n\
  --ignore-gpu-blocklist \\\n\
  --enable-zero-copy \\\n\
  --use-gl=egl \\\n\
  --disable-software-rasterizer \\\n\
  https://x.com &\n\
x11vnc -display :0 -nopw -forever -shared -rfbport 5900 -geometry 1920x1080 -bg\n\
wait' > /opt/scripts/start.sh && chmod 777 /opt/scripts/start.sh && chmod +x /opt/scripts/start.sh


EXPOSE 5900

USER docker

CMD ["/opt/scripts/start.sh"]

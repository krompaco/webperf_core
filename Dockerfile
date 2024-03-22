FROM node:18.19.1-bookworm-slim

ARG TARGETPLATFORM=linux/amd64

ENV PATH="/usr/local/bin:${PATH}"

RUN echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" >> /etc/apt/sources.list.d/debian.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends firefox tcpdump iproute2 ca-certificates sudo imagemagick libjpeg-dev xz-utils python3 python3-pip python-is-python3 ffmpeg gnupg2 wget libjpeg-dev libfontconfig build-essential gconf-service lsb-release xdg-utils fonts-liberation xvfb default-jdk --no-install-recommends --no-install-suggests --fix-missing && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/* /tmp/*

RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Add user so we don't need --no-sandbox.
RUN groupadd --system pptruser && \
  useradd --system --create-home --gid pptruser pptruser && \
  mkdir --parents /usr/src/app && \
  chown --recursive pptruser:pptruser /usr/src/app

WORKDIR /usr/src/app

RUN echo 'ALL ALL=NOPASSWD: /usr/sbin/tc, /usr/sbin/route, /usr/sbin/ip' > /etc/sudoers.d/tc

ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable

RUN npm install -g node-gyp@10.0.1
RUN npm install -g puppeteer

RUN wget -q -O vnu.jar https://github.com/validator/validator/releases/download/latest/vnu.jar

# Run everything after as non-privileged user.
USER pptruser

RUN npm install sitespeed.io@33.3.0
RUN npm install pa11y@7.0.0
RUN npm install lighthouse@10.4.0
RUN npm install yellowlabtools@3.0.1

COPY . /usr/src/app

RUN pip install -r requirements.txt --break-system-packages
RUN python -m pip install --upgrade pip --break-system-packages
RUN python -m pip install --upgrade setuptools --break-system-packages
RUN python -m pip install pyssim Pillow image --break-system-packages
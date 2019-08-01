FROM        python:3.5.3-slim

RUN         apt-get update && apt-get install -y locales wget && rm -rf /var/lib/apt/lists/* && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
RUN         wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
                && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
                && apt-get update \
                && apt-get install -y google-chrome-unstable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst ttf-freefont \
                    --no-install-recommends \
                && rm -rf /var/lib/apt/lists/*

COPY        requirements.txt /tmp/
RUN         pip3 install -r /tmp/requirements.txt

COPY        . /app
ENV         PYTHONPATH /app
RUN         'python -c import "pyppeteer; pyppeteer.chromium_downloader.download_chromium()"'

ENTRYPOINT  ["python3", "/app/southwestalerts/app.py"]

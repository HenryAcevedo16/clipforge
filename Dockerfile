FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    # Deno: YouTube exige un motor de JavaScript para resolver su desafío
    && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -U --pre "yt-dlp[default]"
COPY . .

ENV NOVOCLIP_HOST=0.0.0.0 NOVOCLIP_NO_BROWSER=1 PORT=8000
EXPOSE 8000
CMD ["python", "app.py"]

FROM node:18-slim

# 1. Rakib awoodda FFmpeg iyo Python
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 2. Rakib yt-dlp (Force install si looga gudbo error-ka)
RUN pip3 install yt-dlp --break-system-packages

WORKDIR /app
COPY . .
RUN npm install

CMD ["npm", "start"]

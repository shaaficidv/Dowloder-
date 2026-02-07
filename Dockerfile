FROM node:18-slim

# Rakib Python, Bash iyo FFmpeg (3-dii luqadood iyo awoodoodii)
RUN apt-get update && apt-get install -y ffmpeg python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install yt-dlp

WORKDIR /app
COPY . .
RUN npm install

CMD ["npm", "start"]

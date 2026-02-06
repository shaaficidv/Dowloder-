FROM python:3.10-slim

# Rakib FFmpeg iyo xirmooyinka lagama maarmaanka ah
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Rakib Libraries-ka Python
RUN pip install --no-cache-dir -r requirements.txt

# Billow bot-ka
CMD ["python", "bot.py"]

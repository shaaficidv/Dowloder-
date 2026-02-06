FROM python:3.10-slim

# Rakib FFmpeg oo ah aaladda dagsata link kasta
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Rakib Libraries-ka lagama maarmaanka ah
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]

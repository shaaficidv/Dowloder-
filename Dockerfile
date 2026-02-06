FROM python:3.10-slim

# Rakib FFmpeg oo loogu talagalay Video-yada
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]


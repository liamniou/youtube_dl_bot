FROM python:3

# Install youtube-dl
RUN apt-get update && apt-get install ffmpeg libsndfile1-dev -y
RUN wget https://yt-dl.org/downloads/latest/youtube-dl -O /usr/local/bin/youtube-dl && chmod a+rx /usr/local/bin/youtube-dl

WORKDIR /app
COPY app/requirements.txt ./
RUN pip install -r requirements.txt
COPY ./app/youtube_dl_bot.py ./
CMD ["python", "youtube_dl_bot.py"]

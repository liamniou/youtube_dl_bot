FROM python:3

# Install youtube-dl
RUN wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/local/bin/yt-dlp && chmod a+rx /usr/local/bin/yt-dlp

WORKDIR /app
COPY app/requirements.txt ./
RUN pip install -r requirements.txt
COPY ./app/youtube_dl_bot.py ./
CMD ["python", "youtube_dl_bot.py"]

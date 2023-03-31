docker run -dit \
  --env YOUTUBE_DL_BOT_TOKEN=... \
  -v /Users/admin/audiobookshelf/podcasts:/downloads \
  --restart unless-stopped --name=youtube_dl_bot liamnou/youtube_dl_bot:1

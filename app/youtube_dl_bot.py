# !/usr/bin/python3
# -*- coding: utf-8 -*-
import configparser
import datetime
import time
import logging as log
import math
import os.path
import subprocess
import telebot


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class Config:
    config = configparser.ConfigParser()
    config_file_path = None

    def __init__(self):
        self.config_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../config"
        )
        self.load_config()

    def load_config(self):
        """Load configuration parameters"""
        if os.path.exists(self.config_file_path):
            self.config.read(self.config_file_path)
        else:
            self.set_default_config()

    def set_default_config(self):
        """Set default configuration"""
        self.config["telegram"] = {}
        self.config["telegram"]["token"] = "TELEGRAM_BOT_TOKEN"

        with open(self.config_file_path, "w") as config_file:
            self.config.write(config_file)

    def get(self):
        """Obtain configuration"""
        return self.config


token = os.getenv("YOUTUBE_DL_BOT_TOKEN")
AUTHORIZED_USERS = [294967926, 191151492]
bot = telebot.TeleBot(token, threaded=False)


def log_and_send_message_decorator(fn):
    def wrapper(message):
        log.warning("[FROM {}] [{}]".format(message.chat.id, message.text))
        if message.chat.id in AUTHORIZED_USERS:
            reply = fn(message)
        else:
            reply = "Sorry, this is a private bot"
        log.warning("[TO {}] [{}]".format(message.chat.id, reply))
        try:
            bot.send_message(message.chat.id, reply)
        except:
            log.error(f"Can't send message to {message.chat.id}")

    return wrapper


def download_video(video_link):
    try:
        log.warning(f"Downloading {video_link}...")
        subprocess_output = (
            subprocess.check_output(
                ["yt-dlp", video_link, "-o", "/downloads/%(channel)s/%(title)s.%(ext)s"]
            )
            .decode("utf-8")
            .strip()
            .split()
        )
        log.warning(subprocess_output)
        return True
    except:
        log.error("Can't download the file")
        return None


def instantiate_message(message, reply_msg):
    return Bunch(chat=Bunch(id=message.chat.id), text=message.text, reply=reply_msg)


@log_and_send_message_decorator
def send_message(message):
    return message.reply


@bot.message_handler(commands=["start", "help"])
@log_and_send_message_decorator
def greet_new_user(message):
    welcome_msg = "\nWelcome to Youtube-dl bot!\nSend link to Youtube video and get audio file back.\n"
    if message.chat.first_name is not None:
        if message.chat.last_name is not None:
            reply = "Hello, {} {} {}".format(
                message.chat.first_name, message.chat.last_name, welcome_msg
            )
        else:
            reply = "Hello, {} {}".format(message.chat.first_name, welcome_msg)
    else:
        reply = "Hello, {} {}".format(message.chat.title, welcome_msg)

    return reply


@bot.message_handler(
    func=lambda m: m.text is not None and m.text.startswith(("https://"))
)
def process_link(message):
    send_message(instantiate_message(message, "Starting the download..."))
    video_link = message.text
    result = download_video(video_link)

    if result:
        send_message(instantiate_message(message, "Audio track was downloaded"))
    else:
        send_message(
            instantiate_message(message, "I can't extract audio from this link")
        )


if __name__ == "__main__":
    bot.polling()

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
from mutagen import mp4


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


# token = Config().get()["telegram"]["token"]
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
    filepath = os.path.join("/tmp", str(time.time_ns()))
    try:
        log.warning(f"Downloading {video_link}...")
        subprocess_output = subprocess.check_output(
            ["youtube-dl", "-f", "bestaudio[ext=m4a]", video_link, "-o", filepath]).decode(
            "utf-8").strip().split()
        log.warning(subprocess_output)
        return filepath
    except:
        log.error("Can't download the file")
        return None


def generate_list_of_50mb_chunks(size, audio_length):
    number_of_chunks_to_split = math.ceil(size / 52428800)
    list_of_chunks = ["00:00:00"]
    chunk_length = str(datetime.timedelta(seconds=int((audio_length / number_of_chunks_to_split))))
    for count in range(0, number_of_chunks_to_split):
        t1 = datetime.datetime.strptime(list_of_chunks[-1], "%H:%M:%S")
        t2 = datetime.datetime.strptime(chunk_length, "%H:%M:%S")
        delta_1 = datetime.timedelta(hours=t1.hour, minutes=t1.minute, seconds=t1.second)
        delta_2 = datetime.timedelta(hours=t2.hour, minutes=t2.minute, seconds=t2.second)
        list_of_chunks.append(str(delta_1 + delta_2))

    return list_of_chunks


def split_large_file(filepath, chunks):
    list_of_files = []
    for start_time, end_time in zip(chunks, chunks[1:]):
        target_filepath = os.path.join("/tmp", str(time.time_ns()))
        subprocess.check_output(
            ["ffmpeg", "-ss", start_time, "-t", end_time, "-i", filepath, "-acodec", "copy", "-vcodec", "copy",
             "-f", "mp4", target_filepath]).decode(
            "utf-8").strip().split()
        list_of_files.append(target_filepath)
    return list_of_files


def instantiate_message(message, reply_msg):
    return Bunch(chat=Bunch(id=message.chat.id), text=message.text,
                 reply=reply_msg)


@log_and_send_message_decorator
def send_message(message):
    return message.reply


@bot.message_handler(commands=["start", "help"])
@log_and_send_message_decorator
def greet_new_user(message):
    welcome_msg = (
        '\nWelcome to Youtube-dl bot!\nSend link to Youtube video and get audio file back.\n'
    )
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


@bot.message_handler(func=lambda m: m.text is not None and m.text.startswith(("https://")))
def process_link(message):
    video_link = message.text
    filepath = download_video(video_link)
    list_of_files = []

    if filepath:
        initial_audio_length = mp4.MP4(filepath).info.length
        initial_filesize = os.path.getsize(filepath)

        if initial_filesize > 52428800:
            chunks = generate_list_of_50mb_chunks(initial_filesize, initial_audio_length)
            list_of_files = split_large_file(filepath, chunks)
        else:
            list_of_files.append(filepath)

    if len(list_of_files) > 0:
        for file in list_of_files:
            audio_length = mp4.MP4(file).info.length
            send_message(instantiate_message(message, "Audio track was extracted, uploading..."))
            audio = open(file, 'rb')
            try:
                bot.send_audio(message.chat.id, audio, "", audio_length)
            except:
                log.error(f"Failed to send audio to {message.chat.id}")
            os.remove(file)
    else:
        send_message(instantiate_message(message, "I can't extract audio from this link"))


if __name__ == "__main__":
    bot.polling()

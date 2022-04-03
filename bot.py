import os
from flask import Flask, request
import telebot

from telebot import types
from PIL import Image
import io
from style_transger import *

user_dict = {}


class GetPhotos:
    def __init__(self):
        self.content = None
        self.style = None


TOKEN = <YOUR TOKEN>
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['help'])
def send_help(message):
    msg = bot.reply_to(message, """\
Send "/start" and follow instructions
""")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
Hi there, I am Neural Style Transfer bot.
Load style photo
""")
    bot.register_next_step_handler(msg, style_image_step)


# @bot.message_handler(content_types=['photo', 'document'])
def style_image_step(message):
    try:
        chat_id = message.chat.id

        if message.content_type == 'document':
            file_info = bot.get_file(message.document.file_id)

        else:
            file_info = bot.get_file(message.photo[-1].file_id)

        downloaded_file = bot.download_file(file_info.file_path)
        image_data = downloaded_file
        style_img = Image.open(io.BytesIO(image_data))
        photos = GetPhotos()
        user_dict[chat_id] = photos
        photos.style = style_img
        msg = bot.send_message(chat_id, 'Load your content photo')
        bot.register_next_step_handler(msg, content_image_and_NST_step)

    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')


# @bot.message_handler(content_types=['photo', 'document'])
def content_image_and_NST_step(message):
    chat_id = message.chat.id

    if message.content_type == 'document':
        file_info = bot.get_file(message.document.file_id)

    else:
        file_info = bot.get_file(message.photo[-1].file_id)

    downloaded_file = bot.download_file(file_info.file_path)
    image_data = downloaded_file
    photos = user_dict[chat_id]

    photos.content = Image.open(io.BytesIO(image_data))

    bot.send_message(chat_id, 'styled photo...')
    bot.send_message(chat_id, 'wait a little bit')

    # print(photos.content)
    # print(photos.style)

    style_trans = NST(photos.content, photos.style)  # создаем экземпляр класса и переводим в тензор
    style_trans.image_loader()

    output = style_trans.run_style_transfer()

    unloader = transforms.ToPILImage()  # reconvert into PIL image
    image = output.cpu().clone()  # we clone the tensor to not do changes on it
    image = image.squeeze(0)  # remove the fake batch dimension
    image = unloader(image)

    bot.send_photo(message.chat.id, image)
    del style_trans


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://<APP>.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

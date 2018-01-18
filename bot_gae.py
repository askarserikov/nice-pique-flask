#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join(os.path.abspath('.'), 'venv/lib/site-packages'))
from ConfigParser import ConfigParser
import random
import telegram
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request

app = Flask(__name__)

global bot
bot = telegram.Bot(token='475690808:AAEMldQw49BYxuvvBZ7ttKiL0d75Bsgbs4U')

def get_flickr_credentials():
    config = ConfigParser()
    config.read('config.ini')
    global APP_KEY
    global APP_SECRET
    global USER_ID
    APP_KEY = config.get('Flickr Credentials', 'KEY')
    APP_SECRET = config.get('Flickr Credentials', 'SECRET')
    USER_ID = config.get('Flickr Credentials', 'USER_ID')
    return

def get_favorites_list():
    r = requests.get\
        ('https://api.flickr.com/services/rest/?method=flickr.favorites.getList&api_key={}&user_id={}&format=json'
         .format(APP_KEY, USER_ID))
    json_data = get_photos_list(r)
    return json_data


def get_random_photo(json_data):
    bits = json.loads(json_data[random.randint(0, len(json_data))])
    rand_photo = 'http://farm{}.staticflickr.com/{}/{}_{}_b.jpg'\
        .format(bits['farm'], bits['server'], bits['id'], bits['secret'])
    print(rand_photo)
    #returns a link to a photo
    return rand_photo


def get_photos_list(data):
    s = data.text.split(':[')
    ds = s[1].split(']}')
    ads = ds[0]
    eds = ads.split('},')
    print(eds[0])
    json_data = []
    for x in range(0, len(eds) - 1):
        json_data.append(eds[x] + '}')
    json_data.append(eds[len(eds) - 1])
    # returns a list with all photos
    return json_data


def get_starty(main_text, draw):
    totaly = 0
    for x in range(0, len(main_text)):
        fontsize, margin = adjust_fontsize(draw, main_text[x])
        totaly += fontsize
    starty = (1024 - totaly) / 2
    return starty


def adjust_fontsize(draw, str):
    x = True
    fontsize = 150
    margin = 150
    font = ImageFont.truetype("fonts/11174.otf", fontsize)
    tx, ty = draw.textsize(str, font)
    while x:
        if tx <= 920:
            x = False
        else:
            fontsize -= 2
            margin -= 3
            font = ImageFont.truetype("fonts/11174.otf", fontsize)
            tx, ty = draw.textsize(str, font)
    return fontsize, margin


def adjust_lines(stringarr, mphoto):
    fontsize = 150
    draw = ImageDraw.Draw(mphoto)
    font = ImageFont.truetype("fonts/11174.otf", fontsize)
    main_text = []
    buff = ""
    for x in range(0, len(stringarr)):
        tx, ty = draw.textsize(stringarr[x], font)
        bx, by = draw.textsize(buff, font)
        sx, sy = draw.textsize(" ", font)
        if buff == "":
            buff = ''.join([buff, stringarr[x]])
        else:
            if bx + sx + tx <= 920:
                buff = ' '.join([buff, stringarr[x]])
            else:
                main_text.append(buff)
                buff = stringarr[x]
        if x + 1 == len(stringarr):
            main_text.append(buff)
    return main_text


def draw_image(photo, title):
    response = requests.get(photo)
    mphoto = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(mphoto)
    stringarr = title.split()
    main_text = adjust_lines(stringarr, mphoto)
    print(main_text)
    ix, iy = 1024, 1024

    if len(main_text) > 7:
        response_msg = "Too many words"
        print(response_msg)
    else:
        starty = get_starty(main_text, draw)
        for x in range (0, len(main_text)):
            fontsize, margin = adjust_fontsize(draw, main_text[x])
            font = ImageFont.truetype("fonts/11174.otf", fontsize)
            tx, ty = draw.textsize(main_text[x], font)
            draw.text(((ix - tx) / 2, starty), main_text[x], (255, 255, 255), font=font)
            print("STARTY: " + str(starty) + " LINE: " + main_text[x] + " MARGIN: " + str(margin))
            starty += margin
        #mphoto.show()
    return mphoto


@app.route('/475690808:AAEMldQw49BYxuvvBZ7ttKiL0d75Bsgbs4Uhook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        chat_id = update.message.chat.id
        print("chat_id = " + chat_id)
        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')

        get_flickr_credentials()
        photos = get_favorites_list()
        photo = get_random_photo(photos)
        title = update.message.text
        pique = draw_image(photo, title)
        pique.save('image.png')
        
        bot.send_photo(chat_id=chat_id, photo=open('image.png', 'rb'))

    return 'ok'


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://URL/HOOK')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
    return '.'


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)
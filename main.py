#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from users import USERS
from matches import MATCHES
import os
import logging
import requests
import json


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

ids = [ str(key) for key, value in USERS.items() ]

INVALID_INPUT = 'Invalid input'

BOT_TOKEN = os.environ['HPBR_BOT_TOKEN']


# answer helper
def answer(update, response):
    update.message.reply_text(response)


# command handlers
def start(bot, update):
    """handles /start command"""
    answer(update, 'Hi!')


def help(bot, update):
    """handles /help command"""
    answer(update, 'Help me if you can, I\'m feeling down')


def ranking(bot, update):
    """handles /ranking command"""
    answer(update, 'Ranking!')


def thigo(bot, update):
    """handles /thigo command"""
    answer(update, 'Feliz aniversário! <3')


def bets(bot, update):
    """handles /bets {bet} command"""
    text = update.message.text
    textSplit = text.split()

    if(len(textSplit) != 2):
        answer(update, INVALID_INPUT)
        return

    try:
        match = int(textSplit[1])
    except ValueError:
        answer(update, INVALID_INPUT)
        return

    if match <= 0:
        answer(update, INVALID_INPUT)
        return

    r = requests.get(url='https://www.motta.ml/bolao2018/sql/getInfo.php?table=bets')

    bets_list = json.loads(r.text)
    filtered_bets = [ b for b in bets_list if b['id_user'] in ids and b['id_match'] == str(match) ]

    home_team = MATCHES[match]['team_home']
    visitor_team = MATCHES[match]['team_visitor']
    response = ''.join(b['name'] + ': ' + home_team + ' ' + b['goals_home'] + ' x ' + b['goals_visitor'] + ' ' + visitor_team + '\n\n' for b in filtered_bets)

    answer(update, response)


def error(bot, update, error):
    """log errors"""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """starts bot"""
    # create the EventHandler
    updater = Updater(BOT_TOKEN)

    # get dispatcher
    dispatcher = updater.dispatcher

    # register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("thigo", thigo))
    dispatcher.add_handler(CommandHandler("ranking", ranking))
    dispatcher.add_handler(CommandHandler("bets", bets))
    dispatcher.add_handler(CommandHandler("help", help))

    dispatcher.add_error_handler(error)

    # starts bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

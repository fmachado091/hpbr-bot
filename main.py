#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functools import reduce
from users import USERS
from matches import MATCHES
import os
import logging
import requests
import json


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

ids = [ key for key, value in USERS.items() ]

INVALID_INPUT = 'Invalid input'

BOT_TOKEN = os.environ['HPBR_BOT_TOKEN']


# utility functions
def answer(update, response):
    update.message.reply_text(response)


def answer_markdown(bot, chat_id, response):
    bot.sendMessage(parse_mode='MARKDOWN', chat_id=chat_id, text=response)


def get_last_match(bets):
    matches = list(map(lambda b: b['id_match'], bets))
    return reduce((lambda x, y: max(x, y)), matches)


def format_ranking_row_short(r):
    args = (r['position'], r['name'], r['points'])
    return '{:3d}. {:s} ({:d})\n'.format(*args)


def format_ranking_row(r):
    args = (r['position'], r['name'], r['points'], r['fives'], r['threes'], r['twos'])
    return '{:3d}. {:14s} - {:3d} pts - {:2d} / {:2d} / {:2d}\n'.format(*args)


# api request functions
def get_bets():
    r = requests.get(url='https://www.motta.ml/bolao2018/sql/getInfo.php?table=bets')
    return json.loads(r.text)


def get_ranking():
    r = requests.get(url='https://www.motta.ml/bolao2018/sql/getRanking.php')
    return json.loads(r.text)


# command handlers
def start(bot, update):
    """handles /start command"""
    answer(update, 'Hi!')


def help(bot, update):
    """handles /help command"""
    answer(update, 'Help me if you can, I\'m feeling down')


def ranking(bot, update):
    """handles /ranking command"""
    text = update.message.text
    split_text = text.split()

    formatter = format_ranking_row
    if len(split_text) == 2 and split_text[1] == 'short':
        formatter = format_ranking_row_short

    ranking = get_ranking()
    response = '```\n'
    response += '** HPBr no Bolão **\n\n'
    response += ''.join([ formatter(r) for r in ranking if r['id'] in ids ])
    response += '```'
    answer_markdown(bot, update.message.chat.id, response)


def bets_with_no_param(bot, update):
    """handles /bets command"""
    bets = get_bets()
    last_match = get_last_match(bets)
    bets_with_param(bot, update, last_match, bets)


def bets_with_param(bot, update, match, bets=get_bets()):
    """handles /bets {match} command"""
    filtered_bets = [ b for b in bets if b['id_user'] in ids and b['id_match'] == match ]

    home_team = MATCHES[match]['team_home']
    visitor_team = MATCHES[match]['team_visitor']

    response = '** ' + home_team + ' x ' + visitor_team + ' **\n'
    response += ''.join(b['name'] + ': ' + str(b['goals_home']) + ' x ' + str(b['goals_visitor']) + '\n' for b in filtered_bets)

    answer(update, response)


def bets(bot, update):
    """handles /bets [{bets}] command"""
    text = update.message.text
    split_text = text.split()

    if (len(split_text) == 1):
        bets_with_no_param(bot, update)
    elif (len(split_text) == 2):
        try:
            match = int(split_text[1])
        except ValueError:
            answer(update, INVALID_INPUT)
            return
        if match <= 0:
            answer(update, INVALID_INPUT)
            return
        bets_with_param(bot, update, match)
    else:
        answer(update, INVALID_INPUT)


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
    dispatcher.add_handler(CommandHandler("ranking", ranking))
    dispatcher.add_handler(CommandHandler("bets", bets))
    dispatcher.add_handler(CommandHandler("help", help))

    dispatcher.add_error_handler(error)

    # starts bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

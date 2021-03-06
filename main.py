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
API_ERROR = 'API error'

BOT_TOKEN = os.environ['HPBR_BOT_TOKEN']


# utility functions
def answer(update, response):
    update.message.reply_text(response)


def answer_markdown(bot, chat_id, response):
    bot.sendMessage(parse_mode='MARKDOWN', chat_id=chat_id, text=response)


def get_last_match(bets):
    matches = list(map(lambda b: b['id_match'], bets))
    return reduce((lambda x, y: max(x, y)), matches)


def format_top_bottom_row(r):
    args = (r['position'], r['name'], r['points'], r['fives'], r['threes'], r['twos'], r['extra_points'])
    return '{:3d}. {:16s} - {:3d} pts - {:2d} / {:2d} / {:2d} / {:2d}\n'.format(*args)


def format_ranking_row_short(r):
    args = (r['position'], r['name'], r['points'])
    return '{:3d}. {:s} ({:d})\n'.format(*args)


def format_ranking_row(r):
    args = (r['position'], r['name'], r['points'], r['fives'], r['threes'], r['twos'], r['extra_points'])
    return '{:3d}. {:14s} - {:3d} pts - {:2d} / {:2d} / {:2d} / {:2d}\n'.format(*args)


def format_bets_row(name, goals_home, goals_visitor):
    return '{:14s}: {:d} x {:d}\n'.format(name, goals_home, goals_visitor)


# api request functions
def get_bets():
    try:
        r = requests.get(url='https://www.motta.ml/bolao2018/sql/getInfo.php?table=bets')
        return json.loads(r.text)
    except:
        return {}


def get_ranking():
    try:
        r = requests.get(url='https://www.motta.ml/bolao2018/sql/getRanking.php')
        return json.loads(r.text)
    except:
        return {}


# command handlers
def start(bot, update):
    """handles /start command"""
    answer(update, 'Hi!')


def help(bot, update):
    """handles /help command"""
    answer(update, 'Help me if you can, I\'m feeling down')


def ranking_response(update, mode):
    text = update.message.text
    split_text = text.split()

    if mode == 'top' or mode == 'bottom':
        formatter = format_top_bottom_row
    else:
        formatter = format_ranking_row
        if len(split_text) == 2 and split_text[1] == 'short':
            formatter = format_ranking_row_short

    ranking = get_ranking()

    if len(ranking) == 0:
        return API_ERROR

    response = '```\n'
    if mode == 'top':
        response += ''.join([ formatter(r) for r in ranking if r['position'] <= 10 ])
    elif mode == 'bottom':
        response += ''.join([ formatter(r) for r in ranking if r['position'] > 123 ])
    elif mode == 'ranking':
        response += ''.join([ formatter(r) for r in ranking if r['id'] in ids ])
    response += '```'

    return response


def ranking(bot, update):
    """handles /ranking command"""
    chat_id = update.message.chat.id
    response = ranking_response(update, 'ranking')
    answer_markdown(bot, chat_id, response)


def top(bot, update):
    """handles /top command"""
    chat_id = update.message.chat.id
    response = ranking_response(update, 'top')
    answer_markdown(bot, chat_id, response)


def bottom(bot, update):
    """handles /bottom command"""
    chat_id = update.message.chat.id
    response = ranking_response(update, 'bottom')
    answer_markdown(bot, chat_id, response)


def bets_with_no_param():
    """handles /bets command"""
    bets = get_bets()
    if len(bets) == 0:
        return API_ERROR

    last_match = get_last_match(bets)

    return bets_with_param(last_match, bets)


def bets_with_param(match, bets=get_bets()):
    """handles /bets {match} command"""
    if len(bets) == 0:
        return API_ERROR

    filtered_bets = [ b for b in bets if b['id_user'] in ids and b['id_match'] == match ]

    home_team = MATCHES[match]['team_home']
    visitor_team = MATCHES[match]['team_visitor']

    response = '```\n'
    response += 'Match #{:d}'.format(match).center(21, ' ')
    response += '\n'
    response += '{:s} x {:s}'.format(home_team, visitor_team).center(21, ' ')
    response += '\n\n'
    response += ''.join(format_bets_row(b['name'], b['goals_home'], b['goals_visitor']) for b in filtered_bets)
    response += '```'

    return response


def bets(bot, update):
    """handles /bets [{match}] command"""
    text = update.message.text
    split_text = text.split()
    chat_id = update.message.chat.id

    if (len(split_text) == 1):
        answer_markdown(bot, chat_id, bets_with_no_param())
    elif (len(split_text) == 2):
        try:
            match = int(split_text[1])
        except ValueError:
            answer(update, INVALID_INPUT)
            return
        if match <= 0:
            answer(update, INVALID_INPUT)
            return
        answer_markdown(bot, chat_id, bets_with_param(match))
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
    dispatcher.add_handler(CommandHandler("top", top))
    dispatcher.add_handler(CommandHandler("bottom", bottom))
    dispatcher.add_handler(CommandHandler("bets", bets))
    dispatcher.add_handler(CommandHandler("help", help))

    dispatcher.add_error_handler(error)

    # starts bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

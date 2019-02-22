import logging
from json import load
from telegram import *
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from hsubs import ScheduleGenerator
from database import insert_show, insert_user, check_user_exists, get_show_id_by_name, check_subscribed,\
                     insert_subscription, remove_subscription, TransactionIntegrityError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

sc = ScheduleGenerator()

config = load(open('config.json', 'r'))

def show_insert_loop(schedule: ScheduleGenerator):
    """
    Grabs all the shows from the schedule and inserts them
    into the database
    """
    for show in schedule.iter_schedule():
        try:
            insert_show(show.title, show.day, show.time)
        except TransactionIntegrityError:
            pass


def build_button_list(days=False, show=False, rtitle=None, gen_whichday=None, u_id=None):
    """
    Generates the appropriate button list depending on the
    given state
    """
    if days:
       return InlineKeyboardMarkup(([[InlineKeyboardButton(day, callback_data=day)] for day in sc.days]))

    if show:
        buttons = []
        backbutton = [InlineKeyboardButton('⏪ Back', callback_data='back')]

        for show in sc.iter_schedule(gen_whichday):
            if rtitle == show.title or check_subscribed(userid=u_id, showid=get_show_id_by_name(show.title)):
                buttons.append([InlineKeyboardButton(f'{show.title}'
                                                     f' @ {show.time} PST ✅',
                                                     callback_data=show.title)])
            else:
                buttons.append([InlineKeyboardButton(f'{show.title} @ {show.time} PST', callback_data=show.title)])

        buttons.append(backbutton)
        return InlineKeyboardMarkup(buttons)

    else:
        return None


def handle_button_press(bot, update):
    """
    Handles any button presses via in-place
    message editing
    """
    callback_query = update.callback_query.data.split('@')[0]
    msg_id = update.callback_query.message.message_id
    cht_id = update.callback_query.message.chat.id

    if callback_query in sc.days:
        bot.editMessageText(text=f'{config["en_gb"]["shows_day"]} {callback_query} :',
                            chat_id=cht_id, message_id=msg_id)
        bot.editMessageReplyMarkup(chat_id=cht_id, message_id=msg_id,
                                   reply_markup=build_button_list(show=True, gen_whichday=callback_query, u_id=cht_id))


    elif 'back' in callback_query:
        bot.editMessageText(text=config['en_gb']['pick_day'],
                            chat_id=cht_id, message_id=msg_id)
        bot.editMessageReplyMarkup(chat_id=cht_id, message_id=msg_id, reply_markup=build_button_list(days=True))

    else:
        if check_subscribed(cht_id, get_show_id_by_name(callback_query)):
            day_context = update.callback_query.message.text.split(' ')[5] # what a hack
            remove_subscription(cht_id, get_show_id_by_name(callback_query))
            bot.editMessageReplyMarkup(chat_id=cht_id, message_id=msg_id,
                                       reply_markup=build_button_list(show=True, gen_whichday=day_context,
                                                                      u_id=cht_id))

        else:
            day_context = update.callback_query.message.text.split(' ')[5]
            insert_subscription(cht_id, get_show_id_by_name(callback_query))
            bot.editMessageReplyMarkup(chat_id=cht_id, message_id=msg_id,
                                       reply_markup=build_button_list(show=True, gen_whichday=day_context,
                                                                      rtitle=callback_query, u_id=cht_id))


def start_command(bot, update):
    if update.message.chat.type == 'private':
        userid = update.message.chat_id
        username = update.message.from_user.username
        firstname = update.message.from_user.first_name

        if check_user_exists(userid):
            bot.sendMessage(chat_id=userid, text=config['en_gb']['greet_seen'],
                            reply_markup=build_button_list(days=True))

        else:
            bot.sendMessage(chat_id=userid, text=config['en_gb']['greet_notseen'],
                            reply_markup=build_button_list(days=True))
            insert_user(userid, username, firstname)

    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=config['en_gb']['pm_only'])


def main():
    show_insert_loop(sc)

    updater = Updater(config['token'])
    bot = Bot(token=config['token'])

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CallbackQueryHandler(handle_button_press))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

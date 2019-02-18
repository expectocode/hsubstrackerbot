import logging
from telegram import *
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from hsubs import ScheduleGenerator
from database import insert_show, insert_user, check_user_exists, TransactionIntegrityError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

sc = ScheduleGenerator()

def show_insert_loop(schedule: ScheduleGenerator):
    """Grab all the shows from the schedule and insert them
    into the database."""
    for day in schedule.days:
        for show in schedule.generate_schedule():
            if day is show.day:
                try:
                    insert_show(show.title, show.day, show.time)
                except TransactionIntegrityError:
                    pass

def listify(schedule: ScheduleGenerator):
    """Pretty print but turns the show data into a list
    in order to be sent as inline keyboard buttons"""
    buttonlist = []
    for day in schedule.days:
        buttonlist.append(day)
        for show in schedule.generate_schedule():
            if day is show.day:
                buttonlist.append(f'{show.title} @ {show.time} PST')
        buttonlist.append('---------------------------------------')
    return buttonlist

def send_buttons(bot, update):
    """Checks a user's subscriptions
    and sends him the appropriate buttons"""
    button_list = [[InlineKeyboardButton(item, callback_data=item)] for item in listify(sc)]
    markup = InlineKeyboardMarkup(button_list)
    bot.sendMessage(update.message.chat_id, text="Here you go", reply_markup=markup)

def handle_button_press(bot, update):
    print(f'Callback query handler: {update.callback_query.data.split("@")[0]}')


def start_command(bot, update):
    if update.message.chat.type == 'private':
        userid = update.message.chat_id
        username = update.message.from_user.username
        firstname = update.message.from_user.first_name

        if check_user_exists(userid):
            bot.sendMessage(chat_id=userid, text="Hello there! I've seen you before! Sending buttons...")
            send_buttons(bot, update)
        else:
            bot.sendMessage(chat_id=userid, text="Hello there! I haven't seen you before. Sending buttons...")
            insert_user(userid, username, firstname)
            send_buttons(bot, update)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I only work in PMs for the time being!")



def main():
    show_insert_loop(sc)
    token = 'i almost forgot to delete this'
    updater = Updater(token)
    bot = Bot(token=token)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CallbackQueryHandler(handle_button_press))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

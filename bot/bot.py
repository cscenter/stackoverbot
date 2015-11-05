import telegram
import json

TOKEN = StackOverflowYaBot.token

LAST_UPDATE_ID = None
LAST_MESSAGE = None
IS_KEYBOARD_WORKING = False
commands = [['/start'], ['/more'], ['/exit']]


def execute(cmd, bot, chat_id):
    global LAST_MESSAGE, IS_KEYBOARD_WORKING

    if cmd.startswith('/start'):
        bot.sendMessage(chat_id=chat_id,
                        text='Welcome to Stack Overflow search bot!')

    elif cmd.startswith('/more'):
        bot.sendMessage(chat_id=chat_id,
                        text=LAST_MESSAGE)

    elif cmd.startswith('/exit'):
        if IS_KEYBOARD_WORKING:
            bot.sendMessage(chat_id=chat_id, text="Exited successfully!",
                            reply_markup=telegram.ReplyKeyboardHide())
            IS_KEYBOARD_WORKING = False
        else:
            bot.sendMessage(chat_id=chat_id, text="Nothing to exit")

    else:
        bot.sendMessage(chat_id=chat_id, text="Unknown command")


def answer(bot):
    global LAST_UPDATE_ID, LAST_MESSAGE, IS_KEYBOARD_WORKING
    for update in bot.getUpdates(offset=LAST_UPDATE_ID):
        chat_id = update.message.chat_id
        message = update.message.text.encode('utf-8')
        dec_message = message.decode('utf-8')

        if message:
            reply_markup = {'keyboard': commands[1::],
                            'resize_keyboard': True, 'one_time_keyboard': False}
            reply_markup = json.dumps(reply_markup)
            if not dec_message.startswith('/'):
                IS_KEYBOARD_WORKING = True
                bot.sendMessage(chat_id=chat_id,
                                text=dec_message, reply_markup=reply_markup)
                LAST_MESSAGE = dec_message
            else:
                execute(dec_message, bot, chat_id)

            LAST_UPDATE_ID = update.update_id + 1


def main():
    global LAST_UPDATE_ID
    bot = telegram.Bot(TOKEN)
    try:
        LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
    except IndexError:
        LAST_UPDATE_ID = None

    while True:
        answer(bot)


if __name__ == '__main__':
    main()

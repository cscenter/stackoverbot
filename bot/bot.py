import telegram

TOKEN = StackOverflowYaBot.token

LAST_UPDATE_ID = None

commands = ['/start']


##TODO: execute commands

def answer(bot):
    global LAST_UPDATE_ID
    for update in bot.getUpdates(offset=LAST_UPDATE_ID):
        chat_id = update.message.chat_id
        message = update.message.text.encode('utf-8')
        dec_message = message.decode('utf-8')

        if message:
            if not dec_message.startswith('/'):
                bot.sendMessage(chat_id=chat_id,
                                text=dec_message)
            else:
                if dec_message not in commands:
                    bot.sendMessage(chat_id=chat_id,
                                    text='Unknown command')

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

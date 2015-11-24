import telegram
import json

from elasticsearch import Elasticsearch


LAST_UPDATE_ID = None
LAST_MESSAGE = None
IS_KEYBOARD_WORKING = False
commands = [['/start'], ['/more'], ['/exit']]

try:
    TOKEN = open('StackOverflowYaBot.token').readline()
except:
    print("No token file found")



def search(bot, query):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    res = es.search(index='stackoverflowdump2', body={"query": {"match": {"Body" : query}}})
    return res


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

                search_results = search(bot, dec_message)

                if search_results['hits']['total'] > 0:
                    answer_text = 'http://stackoverflow.com/questions/' + str(search_results['hits']['hits'][0]['_source']['doc']['question']['Id'])
                    answer_text += '\n' * 2
                    answer_text += search_results['hits']['hits'][0]['_source']['doc']['question']['Body']
                    answer_text += '\n' * 2
                    answer_text += search_results['hits']['hits'][0]['_source']['doc']['answer']['Body']
                else:
                    answer_text = 'I know nothing, sorry'

                bot.sendMessage(chat_id=chat_id,
                                text=answer_text, reply_markup=reply_markup)
                
                LAST_MESSAGE = answer_text
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

import telegram
import json

from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
from elasticsearch import Elasticsearch


bot_answer_template = '''
http://stackoverflow.com/questions/{question_id}
---------
*{question_title}*

{question_body}
---------
{answer_body}
'''

LAST_UPDATE_ID = None
LAST_MESSAGE = None
IS_KEYBOARD_WORKING = False
commands = [['/start'], ['/more'], ['/exit']]

try:
    TOKEN = open('StackOverflowYaBot.token').readline()
except:
    print("No token file found")


def prepare_for_markdown(string):
    soup = BeautifulSoup(string)
    for tag in soup.findAll():
        if tag.name == 'code':
            if tag.string is not None:
                tag.string = '```' + tag.string + '```'
        elif tag.name == 'a':
            if tag['href'] is not None:
                tag.replaceWith(tag['href'])
        elif tag.name == 'strong':
            if tag.string is not None:
                tag.string = '*' + tag.string + '*'
        else:
            if (tag.string is not None):
                tag.string = tag.string.replace('*', '\*')

    htmlParser = HTMLParser()
    plain_text = htmlParser.unescape(soup.getText('\n'))
    plain_text = plain_text.replace('\n\n', '\n')
    return plain_text


def search(bot, query):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    search_hits = es.search(index='stackoverflowdump2', body={"query": {"match": {"Body" : query}}})
    res = [hit['_source']['doc'] for hit in search_hits['hits']['hits']]
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

                if (len(search_results) > 0):
                    answer_text = bot_answer_template.format(
                        question_id=search_results[0]['question']['Id'],
                        question_title=search_results[0]['question']['Title'],
                        question_body=prepare_for_markdown(search_results[0]['question']['Body']),
                        answer_body=prepare_for_markdown(
                            search_results[0]['answer']['Body']
                        )
                    )
                else:
                    answer_text = 'I know nothing, sorry'

                bot.sendMessage(chat_id=chat_id,
                                text=answer_text,
                                reply_markup=reply_markup,
                                parse_mode=telegram.ParseMode.MARKDOWN)
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

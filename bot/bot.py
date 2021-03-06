import telegram
import json
import html

from html.parser import HTMLParser
from bs4 import BeautifulSoup
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
commands = [['/start'], ['/ok'], ['/more'], ['/exit']]
sessions = {}

try:
    TOKEN = open('StackOverflowYaBot.token').readline()
except:
    print("No token file found")


def prepare_for_logging(string):
    string = string.replace('\n', ' ')
    string = string.replace('\t', ' ')
    return string

def log_results(session, correctness):
    question = prepare_for_logging(session['question'])
    answer_id = session['search_results'][session['current_answer']]['answer']['Id']
    answer = prepare_for_logging(
        session['search_results'][session['current_answer']]['answer']['Body']
    )
    with open('results.log', 'a') as log:
        log.write('{0}\t{1}\t{2}\t{3}\n'.format(question, answer_id, answer, correctness))


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

    soup_text = soup.getText('\n')
    soup_text = soup_text.replace('*', '\*')
    soup_text = soup_text.replace('_', '\_')
    plain_text = html.unescape(soup_text)
    plain_text = plain_text.replace('\n\n', '\n')
    return plain_text


def prepare_answer_from_search_output(search_results, result_id):
    answer_text = bot_answer_template.format(
        question_id=search_results[result_id]['question']['Id'],
        question_title=search_results[result_id]['question']['Title'],
        question_body=prepare_for_markdown(
            search_results[result_id]['question']['Body']
        ),
        answer_body=prepare_for_markdown(
            search_results[result_id]['answer']['Body']
        )
    )
    return answer_text


def search(bot, query):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    search_hits = es.search(index='stackoverflowdump2', body={"query": {"match": {"Body" : query}}})
    res = [hit['_source']['doc'] for hit in search_hits['hits']['hits']]
    return res


def execute(cmd, bot, chat_id):
    global LAST_MESSAGE, IS_KEYBOARD_WORKING, sessions

    if cmd.startswith('/start'):
        bot.sendMessage(chat_id=chat_id,
                        text='Welcome to Stack Overflow search bot!')

    elif cmd.startswith('/ok'):
        if chat_id in sessions.keys():
            log_results(sessions[chat_id], True)
            bot.sendMessage(
                chat_id=chat_id,
                parse_mode=telegram.ParseMode.MARKDOWN,
                text="I'm glad to help you!"
            )
        else:
            bot.sendMessage(
                chat_id=chat_id,
                parse_mode=telegram.ParseMode.MARKDOWN,
                text="You don't need much for happiness, do you?"
            )

    elif cmd.startswith('/more'):
        if chat_id in sessions.keys():
            log_results(sessions[chat_id], False)
            if sessions[chat_id]['current_answer'] < (len(sessions[chat_id]['search_results']) - 1):
                sessions[chat_id]['current_answer'] += 1
                bot.sendMessage(
                    chat_id=chat_id,
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    text=prepare_answer_from_search_output(
                        sessions[chat_id]['search_results'],
                        sessions[chat_id]['current_answer']
                    )
                )
            else:
                bot.sendMessage(
                    chat_id=chat_id,
                    text="Sorry, I'm out of good guesses - try different one!"
                )
        else:
            bot.sendMessage(
                chat_id=chat_id,
                text="Hey, ask me something first!"
            )

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
            reply_markup = {
                'keyboard': commands[1::],
                'resize_keyboard': True,
                'one_time_keyboard': False
            }
            reply_markup = json.dumps(reply_markup)

            if not dec_message.startswith('/'):
                IS_KEYBOARD_WORKING = True

                search_results = search(bot, dec_message)

                if (len(search_results) > 0):
                    answer_text = prepare_answer_from_search_output(search_results, 0)
                    sessions[chat_id] = {'question': dec_message, 'current_answer': 0, 'search_results' : search_results}
                else:
                    answer_text = 'I know nothing, sorry'

                bot.sendMessage(chat_id=chat_id,
                                text=answer_text,
                                reply_markup=reply_markup,
                                parse_mode=telegram.ParseMode.MARKDOWN)

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

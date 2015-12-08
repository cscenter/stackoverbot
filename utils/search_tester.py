import requests
import pandas
import mysql.connector

from search_handler import get_best_answer_id


db_config = {
    'user': 'root',
    'password': 'password',
    'database': 'stackoverflowdump2'
}


def get_additional_fields(ids, fields):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(dictionary=True)
    cursor.execute('SELECT {fields} FROM posts WHERE Id IN ({ids})'.format(
        fields=','.join(fields),
        ids=','.join(list(map(str, ids)))
    ))
    return pandas.DataFrame(cursor.fetchall())


def test_from_dataset(dataset, http=False):
    questions_ids = dataset['Id']
    answers_ids = dataset['AcceptedAnswerId']

    questions = get_additional_fields(questions_ids, ['Title'])

    accuracy = 0
    for i in range(len(questions)):
        guess = None
        if http:
            try:
                r = requests.get(url='http://localhost:9000/', params={'q': str(questions['Title'][i])})
                guess = int(r.text)
            except requests.exceptions.RequestException as e:
                print(str(questions['Title'][i]))
                print(e)
        else:
            guess = get_best_answer_id(str(questions['Title'][i]))

        if guess == answers_ids[i]:
            accuracy += 1
        if (i + 1) % 10 == 0:
            print('Tested entries: {0}'.format(i + 1))

    return accuracy / len(questions)

if __name__ == '__main__':
    dataset = pandas.read_csv('../dataset.csv')
    accuracy = test_from_dataset(dataset)
    print('Resulted accuracy: {0}'.format(accuracy))

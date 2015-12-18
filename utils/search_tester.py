import requests
import pandas
import mysql.connector
import numpy as np

from utils.search_handler import get_best_answer_id
from utils.data_augmentation import augment_with_synonyms, get_words_from_tags

db_config = {
    'user': 'root',
    'password': 'password',
    'database': 'stackoverflowdump2'
}


def get_additional_fields(ids, fields):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(dictionary=True)
    result = pandas.DataFrame(columns=fields)
    for id in ids:
        cursor.execute('SELECT {fields} FROM posts WHERE Id = {id}'.format(
            fields=','.join(fields),
            id=id
        ))
        result = result.append(cursor.fetchall(), ignore_index=True)
    return result


def test_from_dataset(dataset, http=False):
    questions_ids = dataset['Id']
    answers_ids = dataset['AcceptedAnswerId']

    questions = get_additional_fields(questions_ids, ['Title', 'Tags'])

    augmentation_factor = np.zeros((len(questions),))
    accuracy = {}
    accuracy['top1'] = np.zeros((len(questions),))
    accuracy['augmented_top1'] = np.zeros((len(questions),))
    accuracy['top10'] = np.zeros((len(questions),))
    accuracy['augmented_top10'] = np.zeros((len(questions),))

    for i in range(len(questions)):
        request = str(questions['Title'][i])

        guess = None
        if http:
            try:
                r = requests.get(url='http://localhost:9000/', params={'q': request})
                guess = int(r.text)
            except requests.exceptions.RequestException as e:
                print(e)
        else:
            guess = get_best_answer_id(request)

        if answers_ids[i] == guess[0]:
            accuracy['top1'][i] = 1
        if answers_ids[i] in guess:
            accuracy['top10'][i] = 1

        Q = augment_with_synonyms(
            request,
            get_words_from_tags(questions['Tags'][i])
        )
        augmentation_factor[i] = len(Q)
        for q in Q:
            guess = None
            if http:
                try:
                    r = requests.get(url='http://localhost:9000/', params={'q': q})
                    guess = int(r.text)
                except requests.exceptions.RequestException as e:
                    print(e)
            else:
                guess = get_best_answer_id(q)

            if answers_ids[i] == guess[0]:
                accuracy['augmented_top1'][i] += 1
            if answers_ids[i] in guess:
                accuracy['augmented_top10'][i] += 1

        accuracy['augmented_top1'][i] /= len(Q)
        accuracy['augmented_top10'][i] /= len(Q)

        if (i + 1) % 10 == 0:
            print('Tested entries: {0}'.format(i + 1))

    return augmentation_factor, accuracy

if __name__ == '__main__':
    dataset = pandas.read_csv('../dataset.csv')
    #dataset = dataset.sample(100)
    #dataset = dataset.set_index(np.array(range(100)))
    augm_factor, accuracy = test_from_dataset(dataset)
    print('Resulted accuracy top1: {0}, accuracy top10: {1}'.format(
        np.mean(accuracy['top1']),
        np.mean(accuracy['top10'])
    ))
    print('Resulted accuracy on augmented data top1: {0}, accuracy top10: {1}, augmentation factor: {2}'.format(
        np.nanmean(accuracy['augmented_top1']),
        np.nanmean(accuracy['augmented_top10']),
        np.mean(augm_factor)
    ))

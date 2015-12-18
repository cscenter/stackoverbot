import csv
import os.path
import mysql.connector

import pandas as pd
import numpy as np

# gensim modules
from gensim import utils
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec

# numpy
import numpy

# random
from random import shuffle

# classifier
from sklearn.linear_model import LogisticRegression



DOCUMENTS_FILE = '../documents.csv'
DATASET_FILE = '../dataset.csv'
MODEL_FILE = '../stackoverflow.d2v'
POSTS_INDEXES_FILE = '../post_index_ids.csv'

BATCH_SIZE = 10000;

db_config = {
    'user' : 'root',
    'password' : 'password',
    'database' : 'stackoverflowdump2'
}

select_query = """SELECT
                    ids.ParentId AS question_id,
                    questions.Title AS question_title,
                    questions.Body AS question_body,
                    questions.Tags AS question_tags,
                    questions.AnswerCount AS question_answercount,
                    questions.FavoriteCount AS question_favoritecount,
                    questions.Score AS question_score,
                    questions.ViewCount AS question_viewcount,
                    questions.AcceptedAnswerId AS question_accepted_answer_id,
                    ids.Id AS answer_id,
                    answers.Body AS answer_body,
                    answers.Score AS answer_score
                    FROM
                    (SELECT Id, ParentId FROM posts WHERE PostTypeId = 2 ORDER BY Id LIMIT {shift}, {batch}) ids
                    JOIN posts AS answers ON (ids.Id = answers.Id)
                    JOIN posts AS questions ON (ids.ParentId = questions.Id)"""


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


class LabeledLineSentence(object):
    def __init__(self, source):
        self.source = source
        
    def __iter__(self):
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor(dictionary=True)
        
        #with open(self.source, newline='') as csvfile:
        #    csvreader = csv.reader(csvfile, delimiter=',')
        #    next(csvreader)
        #    for id, row in enumerate(csvreader):
        #        text = row[1] + ' ' + row[2]
        #        yield TaggedDocument(utils.to_unicode(text.lower()).split(), [id])

        self.posts_ids = []
        batch_cnt = 0
        while True:
            cursor.execute(select_query.format(
                shift=batch_cnt * BATCH_SIZE,
                batch=BATCH_SIZE
            ))
            
            posts = cursor.fetchall()

            if (len(posts) == 0):
                break

            for post in posts:
                self.posts_ids.append(int(post['question_id']))
                text = ' '.join([post['question_title'], post['question_body'], post['answer_body']])
                yield TaggedDocument(utils.to_unicode(text.lower()).split(), [len(self.posts_ids) - 1])

            batch_cnt += 1



if not os.path.isfile(MODEL_FILE):
    sentences = LabeledLineSentence(DOCUMENTS_FILE)

    model = Doc2Vec(min_count=1, window=10, size=200, sample=1e-4, negative=5, workers=4)
    model.build_vocab(sentences)

    for epoch in range(1):
        print('epoch {0} started'.format(epoch))
        model.train(sentences)

    post_index_ids = sentences.posts_ids
    pd.DataFrame(post_index_ids).to_csv(POSTS_INDEXES_FILE, header=False)
    model.save(MODEL_FILE)
else:
    post_index_ids = pd.read_csv(POSTS_INDEXES_FILE)['1'].tolist()
    model = Doc2Vec.load(MODEL_FILE)




dataset = pd.read_csv(DATASET_FILE)
questions_ids = dataset['Id']
answers_ids = dataset['AcceptedAnswerId']

#accuracy = 0
#for id, doc in zip(ids, queries):
#    if type(doc) == type(1.0):
#        print(id, doc)
#        continue
#
#    query_vec = model.infer_vector(doc.lower().split())
#
#    sims = model.docvecs.most_similar([query_vec])
#
#    if id in [post_index_ids[sim[0]] for sim in sims[:10]]:
#        accuracy += 1
#
#print (accuracy / len(queries))

questions = get_additional_fields(questions_ids, ['Title', 'Tags'])
augmentation_factor = np.zeros((len(questions),))
accuracy = {}
accuracy['top1'] = np.zeros((len(questions),))
accuracy['augmented_top1'] = np.zeros((len(questions),))
accuracy['top10'] = np.zeros((len(questions),))
accuracy['augmented_top10'] = np.zeros((len(questions),))

for i in range(len(questions)):
    request = str(questions['Title'][i])
    request_vec = model.infer_vector(request.lower().split())
    sims = model.docvecs.most_similar([request_vec])
    guess = [post_index_ids[sim[0]] for sim in sims[:10]]

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
        request_vec = model.infer_vector(q.lower().split())
        sims = model.docvecs.most_similar([request_vec])
        guess = [post_index_ids[sim[0]] for sim in sims[:10]]
        if answers_ids[i] == guess[0]:
            accuracy['augmented_top1'][i] += 1
        if answers_ids[i] in guess:
            accuracy['augmented_top10'][i] += 1

    accuracy['augmented_top1'][i] /= len(Q)
    accuracy['augmented_top10'][i] /= len(Q)
    
    if (i + 1) % 10 == 0:
        print('Tested entries: {0}'.format(i + 1))

print('Resulted accuracy top1: {0}, accuracy top10: {1}'.format(
    np.mean(accuracy['top1']),
    np.mean(accuracy['top10'])
))
print('Resulted accuracy on augmented data top1: {0}, accuracy top10: {1}, augmentation factor: {2}'.format(
    np.nanmean(accuracy['augmented_top1']),
    np.nanmean(accuracy['augmented_top10']),
    np.mean(augmentation_factor)
))

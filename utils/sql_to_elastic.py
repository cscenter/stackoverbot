import mysql.connector
import json
import copy

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from mysql.connector import errorcode



# Configurations
BATCH_SIZE = 10000;

db_config = {
	'user' : 'root',
	'password' : 'password',
	'database' : 'stackoverflowdump'
}

document_template = {
	'_index' : 'stackoverflowdump',
	'_type' : 'posts',
	#'_id' : None,
	'doc' : {
		'question' : {
			'Id' : None,
			'Title' : None,
			'Body' : None,
			'Tags' : None,
			'AnswerCount' : None,
			'FavoriteCount' : None,
			'Score' : None,
			'ViewCount' : None,
		},
		'answer' : {
			'Id' : None,
			'Body' : None,
			'Score' : None,
			'Accepted' : None
		},

	}
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

					

# Script body
es = Elasticsearch()

cnx = mysql.connector.connect(**db_config)

cursor = cnx.cursor(dictionary=True)


batch_cnt = 0
while True:

	cursor.execute(select_query.format(
		shift=batch_cnt * BATCH_SIZE,
		batch=BATCH_SIZE
		))

	if cursor.rowcount == 0:
		break

	posts = cursor.fetchall()

	posts_to_index_batch = []
	for post in posts:

		document_template['doc']['question']['Id'] = post['question_id']
		document_template['doc']['question']['Title'] = post['question_title']
		document_template['doc']['question']['Body'] = post['question_body']
		document_template['doc']['question']['Tags'] = post['question_tags']
		document_template['doc']['question']['AnswerCount'] = post['question_answercount']
		document_template['doc']['question']['FavoriteCount'] = post['question_favoritecount']
		document_template['doc']['question']['Score'] = post['question_score']
		document_template['doc']['question']['ViewCount'] = post['question_viewcount']
		document_template['doc']['answer']['Id'] = post['answer_id']
		document_template['doc']['answer']['Body'] = post['answer_body']
		document_template['doc']['answer']['Score'] = post['answer_score']
		document_template['doc']['answer']['Accepted'] = (post['answer_id'] == post['question_accepted_answer_id'])
		
		posts_to_index_batch.append(copy.deepcopy(document_template))


	try:
		helpers.bulk(es, posts_to_index_batch)
		posts_to_index_batch = []
		print('Batch {n} indexed'.format(n=batch_cnt))
	except:
		print('Exception rised at batch {n} indexing'.format(n=batch_cnt))

	batch_cnt += 1


print('Indexing complete!')
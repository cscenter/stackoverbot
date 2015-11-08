import mysql.connector
import json
import copy

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from mysql.connector import errorcode


# Configurations
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
		},

	}
}

select_query = """SELECT
					questions.Id AS question_id,
					questions.Title AS question_title,
					questions.Body AS question_body,
					questions.Tags AS question_tags,
					questions.AnswerCount AS question_answercount,
					questions.FavoriteCount AS question_favoritecount,
					questions.Score AS question_score,
					questions.ViewCount AS question_viewcount,
					answers.Id AS answer_id,
					answers.Body AS answer_body,
					answers.Score AS answer_score
					FROM posts AS answers JOIN posts AS questions ON (answers.ParentId = questions.Id) WHERE answers.PostTypeId = 2;""";


# Script body
es = Elasticsearch()

cnx = mysql.connector.connect(**db_config)

cursor = cnx.cursor(dictionary=True)
cursor.execute(select_query)

indexed_posts_cnt = 0
posts_to_index_batch = []
for post in cursor:

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
	
	posts_to_index_batch.append(copy.deepcopy(document_template))

	if len(posts_to_index_batch) == 10000:
		try:	
			helpers.bulk(es, posts_to_index_batch)

			posts_to_index_batch = []

			indexed_posts_cnt += 1;
			print('Batch {n} indexed'.format(n=indexed_posts_cnt))

		except:
			print('Exception rised at batch indexing')


if len(posts_to_index_batch) > 0:
	helpers.bulk(es, posts_to_index_batch)


print('Indexing complete!')
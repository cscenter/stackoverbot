import mysql.connector
import json

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
	'_id' : None,
	'doc' : {
		'title' : None,
		'body' : None,
		'answer' : None
	}
}

select_query = 'SELECT * FROM {table} WHERE Id = {id}';


# Script body
es = Elasticsearch()

cnx1 = mysql.connector.connect(**db_config)
cnx2 = mysql.connector.connect(**db_config)

cursor = cnx1.cursor(dictionary=True)
cursor.execute('SELECT * FROM posts;')

posts_to_index_batch = []
for post in cursor:
	
	
	if (post['PostTypeId'] == 1) and (post['AcceptedAnswerId'] is not None):
		inner_cursor = cnx2.cursor(dictionary=True, buffered=True)

		inner_cursor.execute(select_query.format(
			table='posts',
			id=post['AcceptedAnswerId']
			))

		answer = inner_cursor.fetchone()
		if answer is None:
			print('Post id = {id} is missing!'.format(id=post['AcceptedAnswerId']))
			continue

		document_template['_id'] = post['Id']
		document_template['doc']['title']  = post['Title']
		document_template['doc']['body']   = post['Body']
		document_template['doc']['answer'] = answer['Body']
		posts_to_index_batch.append(document_template.copy())

	if len(posts_to_index_batch) == 10000:
		try:
			helpers.bulk(es, posts_to_index_batch)
			posts_to_index_batch = []
			print('Batch indexed')
		except:
			print('Exception rised at batch Indexing')


if len(posts_to_index_batch) > 0:
	helpers.bulk(es, posts_to_index_batch)

print('Indexing complete!')
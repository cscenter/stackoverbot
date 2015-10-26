import mysql.connector
import os
import xml.etree.cElementTree as etree

from mysql.connector import errorcode


# Configurations
db_user = 'root'
db_password = 'password'
db_name = 'tests'
path_to_xml_dump = 'D:\\stackexchange\\'


# Structure and sql commands
anathomy = {
 'posts': {
  'Id':'INTEGER', 
  'PostTypeId':'INTEGER', # 1: Question, 2: Answer
  'ParentID':'INTEGER', # (only present if PostTypeId is 2)
  'AcceptedAnswerId':'INTEGER', # (only present if PostTypeId is 1)
  'CreationDate':'DATETIME',
  'Score':'INTEGER',
  'ViewCount':'INTEGER',
  'Body':'TEXT',
  'Title':'TEXT',
  'Tags':'TEXT',
  'AnswerCount':'INTEGER',
  'CommentCount':'INTEGER',
  'FavoriteCount':'INTEGER',
 },
}

create_query='CREATE TABLE {table} ({fields})'
insert_query='INSERT INTO {table} ({columns}) VALUES ({values})'


# Script body
cnx = mysql.connector.connect(user = db_user, password = db_password, database = db_name)
cursor = cnx.cursor()

for file in anathomy.keys():
  print "Opening {0}.xml".format(file)
  with open(os.path.join(path_to_xml_dump, file + '.xml')) as xml_file:
    tree = etree.iterparse(xml_file)
    table_name = file

    sql_create = create_query.format(
      table=table_name, 
      fields=", ".join(['{0} {1}'.format(name, type) for name, type in anathomy[table_name].items()]))
    print('Creating table {0}'.format(table_name))

    try:
      cursor.execute(sql_create)
    except mysql.connector.Error as err:
      print(err)
      break

    table_fields = [name for name, type in anathomy[table_name].items()]

    for events, row in tree:

      columns_values = {col:val for col,val in row.attrib.iteritems() if col in table_fields}

      sql_insert = insert_query.format(
          table = table_name, 
          columns = ', '.join(columns_values.keys()),
          values = ('%s, ' * len(columns_values.keys()))[:-2])

      try:
        cursor.execute(sql_insert, columns_values.values())
      except mysql.connector.Error as err:
        print(err)
      finally:
        row.clear()
    print "\n"
    del(tree)

cnx.commit()
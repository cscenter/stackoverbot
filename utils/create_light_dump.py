import csv
import mysql.connector

BATCH_SIZE = 10000

db_config = {
    'user': 'root',
    'password': 'password',
    'database': 'stackoverflowdump2'
}

FIELDS = 'ViewCount, ParentId, AnswerCount, Score, PostTypeId, FavoriteCount, CommentCount, AcceptedAnswerId, Id'
FIELDS_NAMES = [field.strip() for field in FIELDS.split(',')]

cnx = mysql.connector.connect(**db_config)
cursor = cnx.cursor(dictionary=True)


with open('../light_dump.csv', 'w', newline='') as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow(FIELDS_NAMES)

    batch_cnt = 0
    while True:
        try:
            cursor.execute('SELECT {0} FROM posts WHERE AcceptedAnswerId IS NOT NULL LIMIT {1}, {2}'.format(
                FIELDS,
                BATCH_SIZE * batch_cnt,
                BATCH_SIZE
            ))

            entries = cursor.fetchall()

            if len(entries) == 0:
                break

            for entry in entries:
                writer.writerow([entry[field] for field in FIELDS_NAMES])

        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))

        batch_cnt += 1
        print('Entries added: {0}'.format(batch_cnt * BATCH_SIZE))

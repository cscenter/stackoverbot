import http.server

from elasticsearch import Elasticsearch
from urllib.parse import urlparse, parse_qs


HANDLER_HOST_NAME = 'localhost'
HANDLER_PORT_NUMBER = 9000
ELASTICSEARCH_SETS = {'host': 'localhost', 'port': 9200}
ELASTICSEARCH_INDEX = 'stackoverflowdump2'


def search(query):
    es = Elasticsearch(**ELASTICSEARCH_SETS)
    search_hits = es.search(index=ELASTICSEARCH_INDEX, body={"size": 10, "query": {"match": {"Title": query}}})
    res = [hit['_source']['doc'] for hit in search_hits['hits']['hits']]
    return res


def get_best_answer_id(query):
    search_results = search(query)
    ids = [result['answer']['Id'] for result in search_results]
    return ids


class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        search_query = params['q'][0]
        best_answer_id = get_best_answer_id(search_query)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(str(best_answer_id), 'utf-8'))

if __name__ == '__main__':
    server_class = http.server.HTTPServer
    httpd = server_class((HANDLER_HOST_NAME, HANDLER_PORT_NUMBER), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

import csv
import itertools
import math
import random
import re


def get_words_from_tags(tags):
    return re.findall(r'\<([A-Za-z0_9_]+)\>', tags)


def get_stop_words():
    csv_reader = csv.reader(open('common-english-words.txt'), delimiter=',')
    stop_words = []
    for row in csv_reader:
        stop_words += row
    return stop_words


def get_synonyms():
    synonyms = {}
    with open('../core-wordnet.txt') as wordnert:
        for row in wordnert:
            re_search = re.search(r'\[([A-Za-z]+)\]', row)
            if re_search is None:
                continue
            word = re_search.group(1)
            word_synonyms = [syn.strip() for syn in row[row.rfind(']') + 1:].split(',') if syn.strip().count(' ') < 3]
            # print(word, [syn.strip() for syn in row[row.rfind(']') + 1:].split(',') if syn.strip().count(' ') >= 2])
            if word not in synonyms.keys():
                synonyms[word] = []
            synonyms[word] += word_synonyms
    return synonyms


def filter_stop_words(phrase):
    stop_words = get_stop_words()
    for word in stop_words:
        phrase = re.sub(r'\b%s\b' % word, '', phrase)
    return phrase


def augment_with_synonyms(phrase, immutable_words):
    immutable_words = ' '.join(immutable_words)
    phrase = phrase.lower()
    synonyms = get_synonyms()

    augmented_phrases = []
    for word in synonyms.keys():
        if (word in phrase) and (word not in immutable_words):
            for synonym in synonyms[word]:
                augmented_phrases.append(phrase.replace(word, synonym))
    return augmented_phrases


def add_stop_words(phrase):
    stopped = []
    stop_words = get_stop_words()
    stop_len = len(stop_words) - 1
    strip = phrase.split(' ')
    s_len = len(strip)
    stops = random.randint(1, 10)
    for i in range(stops):
        copied = list(strip)
        new_stop = random.randint(0, stop_len)
        stop_pos = random.randint(0, s_len)
        copied.insert(stop_pos, stop_words[new_stop])
        stopped.append(' '.join(copied))

    return stopped


def delete_untagged_nwords(phrase, n_words, tags):
    def nCr(n, r):
        f = math.factorial
        return f(n) / f(r) / f(n - r)

    filtered = []
    strip = phrase.split(' ')
    s_len = len(strip) - 1
    tries = int(nCr(s_len, n_words) // 2)
    for i in range(tries):
        rands = random.sample(range(0, s_len), n_words)
        if all(strip[rn] not in tags for rn in rands):
            copied = list(strip)
            for rn in sorted(rands, reverse=True):
                del copied[rn]
            new_query = ' '.join(copied)
            if new_query not in filtered:
                filtered.append(' '.join(copied))
    return filtered


def delete_untagged(phrase, tags):
    strip = phrase.split(' ')
    new_queries = []
    s_len = int(len(strip)//4) + 2
    for i in range(1, s_len):
        new_queries.append(delete_untagged_nwords(phrase, i, tags))
    return list(itertools.chain.from_iterable(new_queries))

print(add_stop_words('cause i am the last one'))
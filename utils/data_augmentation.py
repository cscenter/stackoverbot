import csv
import re


def get_words_from_tags(tags):
    return re.findall(r'\<([A-Za-z0_9_]+)\>', tags)


def get_stop_words():
    csv_reader = csv.reader(open('../common-english-words.txt'), delimiter=',')
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
            #print(word, [syn.strip() for syn in row[row.rfind(']') + 1:].split(',') if syn.strip().count(' ') >= 2])
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

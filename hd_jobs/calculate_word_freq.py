#http://www.mhermans.net/from-pdf-to-wordcloud-using-the-python-nltk.html
#! /usr/bin/env python
# wordcount.py: parse & return word frequency
from settings.common import getHDISBucket
from common.text_data import TextData, makeTimeKeyFromTimeTuple, getTimeTupleFromTimeString
import sys, nltk, json, re

def calcGroupFreqDicts(raw_key, resolution):
    try:
        data_json = raw_key.get_contents_as_string()
        data_dict = json.loads(data_json)
    except:
        data_dict = {}
    data_counts = data_dict.setdefault("counts", {})     # dictionary mapping (hour,day,month,year) to word counts
    return calcFreqDicts(data_counts)

def calcUserFreqDicts(raw_key, resolution):
    user_td = TextData()
    user_td.loadFromS3Keys([raw_key])
    user_names = user_td.getUsernames()
    user_td.filterDataByUsers(from_users=user_names)
    counts_dict = user_td.getCountsDict()
    user_td.calcByTime(resolution=resolution)
    by_time = user_td.getByTime()
    return calcFreqDicts(by_time)

def calcFreqDicts(data_counts, resolution="month"):

    resolution_dict = {}
    total_text_blob = ""
    # aggregate text blobs by resolution
    for time_key, text_data in data_counts.items():
        time_tuple = getTimeTupleFromTimeString(time_key, resolution)
        text_blob = text_data["text_blob"]
        relevant_blob = resolution_dict.setdefault(time_tuple, "")
        resolution_dict[time_tuple] = relevant_blob + " " + text_blob
        total_text_blob += text_blob
    # calculate freqs dict for each time interval
    all_freqs_dicts = {}
    for time_tuple, text_blob in resolution_dict.items():
        time_key = makeTimeKeyFromTimeTuple(time_tuple)
        freq_dict = getFreqDictFromText(text_blob)
        all_freqs_dicts[time_key] = freq_dict
    # calculate total word frequencies over all time
    total_freq_dict = getFreqDictFromText(total_text_blob)

    return total_freq_dict, all_freqs_dicts


def getFreqDictFromText(txt):
    tokens = nltk.word_tokenize(txt) # tokenize text
    clean_tokens = []

    total_num_words = 0
    for word in tokens:
        total_num_words += 1
        word = word.lower()
        if word.isalpha(): # drop all non-words
            clean_tokens.append(word)

    # make frequency distribution of words
    fd = nltk.FreqDist(clean_tokens)
    freq_dict = {}
    for token in fd:
        count = fd[token]
        freq = count / float(total_num_words)
        freq_dict[token] = freq
    return freq_dict

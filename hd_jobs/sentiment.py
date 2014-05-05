import sys
import json
import re
import numpy as np
import datetime

def perform_sentiment_analysis_by_person(data, sent_file):

    to_return = ""

    scores = create_sentiment_map(sent_file)
    json_data = json.loads(data)
    user_name = json_data['user_meta']['user_name']

    conversations = json_data['counts']
    for participants in conversations:
        
        participants_list = participants.split('|')
        other_participant = participants_list[1] if participants_list[0] == user_name else participants_list[0] 

        conversation_list = conversations[participants]
        conversation_score = 0
        num_words = 0
        for time in conversation_list:
            message = conversation_list[time]
             
            # for 1-gram
            for word in message['1']:
                p_word = process_word(word)
                if len(p_word) > 0:
                    sentiment = sentiment_for_word(scores, word)
                    
                    if sentiment != 0:
                        num_words += 1
                    conversation_score += sentiment

        if conversation_score != 0:
            to_return += other_participant + ": " + str(conversation_score / num_words) + "\n"
        else:
            to_return += other_participant + ": 0" + "\n"

def perform_sentiment_analysis_by_time(data, sent_file):

    to_return = ""

    num_words_mat = np.zeros((7, 24))
    sent_mat = np.zeros((7, 24))
    avg_sent_mat = np.zeros((7, 24))
    quantized_mat = np.zeros((7, 24))


    scores = create_sentiment_map(sent_file)
    json_data = json.loads(data)
    user_name = json_data['user_meta']['user_name']

    conversations = json_data['counts']
    for participants in conversations:
        
        participants_list = participants.split('|')
        other_participant = participants_list[1] if participants_list[0] == user_name else participants_list[0] 

        conversation_list = conversations[participants]
        for time in conversation_list:
            date = time.split('|')
            hour = int(date[0])
            day = datetime.datetime.strptime(time, "%H|%d|%m|%Y").weekday()

            message = conversation_list[time]
            for word in message['1']:
                p_word = process_word(word)
                if len(p_word) > 0:
                    sentiment = sentiment_for_word(scores, word)
                    if sentiment != 0:
                        sent_mat[day][hour] += sentiment
                        num_words_mat[day][hour] += 1

    for day in range(0, 7):
        for hour in range (0, 24):
            if num_words_mat[day][hour] != 0:
                avg_sent_mat[day][hour] = sent_mat[day][hour] / num_words_mat[day][hour]
            else:
                avg_sent_mat[day][hour] = 0


    buckets = 10

    min_sent = np.amin(avg_sent_mat)
    max_sent = np.amax(avg_sent_mat)

    increment = (max_sent - min_sent) / buckets
    
    to_return += str(min_sent) + "\n"
    to_return += str(max_sent) + "\n"
    to_return += str(increment) + "\n"
    #TO DO 1 BASED
    bucket_array = [None] * buckets
    cur_len = min_sent
    i = 0
    for i in range(0, buckets):
        cur_len += increment
        bucket_array[i] = cur_len
    
    for day in range(0, 7):
        for hour in range(0, 24):
            for i in range(0, len(bucket_array)):
                if i == buckets - 1:
                    quantized_mat[day][hour] = buckets
                elif bucket_array[i] >= avg_sent_mat[day][hour]:
                    quantized_mat[day][hour] = i + 1
                    break 
    to_return += str(quantized_mat) + "\n"
    return to_return


def create_sentiment_map(sent_file):
    scores = {} # initialize an empty dictionary
    for line in sent_file:
        term, score  = line.split("\t")
        scores[term] = float(score) # Convert the score to a float.
    return scores

def sentiment_for_word(scores, word):
    if word in scores:
        return scores[word]
    else:
        return 0

def process_word(word):
    lowercased_word = word.strip().lower()
    return re.sub(r'[^\w\s]','', lowercased_word) # remove punctuation


def calcSentimentByPersonFromRawJSON(json_data, sent_file):
    return perform_sentiment_analysis_by_person(str(data).decode("unicode_escape"), sent_file)

def calcSentimentByHourFromRawJSON(json_data, sent_file):
    return perform_sentiment_analysis_by_time(str(json_data).decode("unicode_escape"), sent_file)

if __name__ == "__main__":
    my_file = open(sys.argv[1])
    sent_file = open(sys.argv[2])
 
    data = my_file.read()
    perform_sentiment_analysis_by_person(str(data).decode("unicode_escape"), sent_file)
    #perform_sentiment_analysis_by_time(str(data).decode("unicode_escape"), sent_file)

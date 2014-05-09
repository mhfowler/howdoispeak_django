import sys
import json
import re, os
from settings.common import PROJECT_PATH
import numpy as np

categories_folder_path = os.path.join(PROJECT_PATH, "static/categories")

CATEGORIES = {}
def updateCategoriesDict():
    for (dirpath, dirnames, filenames) in os.walk(categories_folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            f = open(file_path, "r")
            words = []
            for line in f:
                words.append(line.replace("\n",""))
            CATEGORIES[filename] = words
updateCategoriesDict()

def complete_category_analysis(data):
    json_data = json.loads(data)
    user_name = json_data['user_meta']['user_name']

    # Create dictionary to contain frequencies for all conversations
    word_count = {}
    for category in CATEGORIES:
        word_count[category] = 0
    word_count["total"] = 0

    conversations = json_data['counts']
    for participants in conversations:
    	for c_list in conversations[participants]:
            for word, count in conversations[participants][c_list]["1"].iteritems():
                for category, word_list in CATEGORIES.iteritems():
                    if process_word(word) in word_list:
                        word_count[category] += count
                        # Only count words that fall into a category,
                        # or else result in a lot of "other" categories
                        word_count["total"] += count
    to_return = []
    for cat, freq in word_count.iteritems():
        if cat == "total":
            continue
        to_return.append({"category":cat, "frequency":freq})
    return to_return

def category_analysis_by_person(data):
    json_data = json.loads(data)
    user_name = json_data['user_meta']['user_name']

    # Dictionary to hold the frequency distributions for each person
    people_cats = {}

    conversations = json_data['counts']
    for participants in conversations:
        participants_list = participants.split('|')
        other_participant = participants_list[1] if participants_list[0] == user_name else participants_list[0] 
        # Create dictionary to contain frequencies for each participant
        people_cats[other_participant] = {}
        for category in CATEGORIES:
            people_cats[other_participant][category] = 0
        people_cats[other_participant]["total"] = 0
        conversation_list = conversations[participants]
        conversation_score = 0
        num_words = 0
        for time in conversation_list:
            message = conversation_list[time]
            for word, count in message['1'].iteritems():
                for category, word_list in CATEGORIES.iteritems():
                    if process_word(word) in word_list:
                        people_cats[other_participant][category] += count
                        people_cats[other_participant]["total"] += count
    to_return = []
    for person, data in people_cats.iteritems():
        no_data = False
        cats = []
        for cat, freq in data.iteritems():
            if cat == "total":
                if freq == 0:
                    no_data = True
                    break
                continue
            cats.append({"category":cat, "frequency":freq})
        if no_data:
            continue
        to_return.append({"person":person, "categories":cats})
    return to_return


def process_word(word):
    lowercased_word = word.strip().lower()
    return re.sub(r'[^\w\s]','', lowercased_word) # remove punctuation

if __name__ == "__main__":
    my_file = open(sys.argv[1])
    data = my_file.read()
    complete_category_analysis(str(data).decode("unicode_escape"))
    category_analysis_by_person(str(data).decode("unicode_escape"))
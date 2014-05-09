from hd_jobs.common import *
from hd_jobs.add_user_to_groups import addUserToGroups, clearGroup
from hd_jobs.move_raw_data import registerAllRawData
from hd_jobs.process_group_data import recalcGroupData
from hd_jobs.calculate_word_freq import calcUserFreqDicts
from hd_jobs.sentiment import calcSentimentByPersonFromRawJSON, calcSentimentByHourFromRawJSON
from hd_jobs.categories import category_analysis_by_person, complete_category_analysis

# JOBS FOR USERS
# ======================================================================================================================

def calcUserFreqs(user_pin):
    print ""
    bucket = getHDISBucket()
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_key_name = hdis_user.getRawKeyName()
    user_key = bucket.get_key(user_key_name)
    total_freq,month_freqs,day_freqs = calcUserFreqDicts(user_key)
    new_key_name = user_key.name.replace("raw.json","freq.json")
    new_key = Key(bucket)
    new_key.key = new_key_name
    to_write_dict = {
        "total_freq":total_freq,
        "month_freqs":month_freqs,
        "day_freqs":day_freqs
    }
    new_key.set_contents_from_string(json.dumps(to_write_dict))


def calcMostUsed(user_pin):
    print "most user: " + str(user_pin)
    bucket = getHDISBucket()
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_freq_key_name = hdis_user.getFreqKeyName()
    user_key = bucket.get_key(user_freq_key_name)
    user_json_string = user_key.get_contents_as_string()
    user_freqs_dict = json.loads(user_json_string)
    user_total_freqs = user_freqs_dict["total_freq"].items()
    user_total_freqs.sort(key=lambda x: x[1], reverse=True)
    most_used_key_name = user_freq_key_name.replace("freq.json", "most_used.json")
    most_used_key = Key(bucket)
    most_used_key.key = most_used_key_name
    most_used_words = map(lambda x: x[0], user_total_freqs)
    most_used_key.set_contents_from_string(json.dumps(most_used_words))


def calcMostAbnormal(user_pin):
    print "abnormal: " + str(user_pin)
    bucket = getHDISBucket()
    group_freq_key_name = "groups/all/freq.json"
    group_freq_key, group_freq_dict = getOrCreateS3Key(group_freq_key_name)
    try:
        group_total_freqs = group_freq_dict["total_freq"]
    except:
        print "+EE+: can't calculate most abnormal before group freq."
        return
    group_raw_key_name = "groups/all/raw.json"
    group_raw_key, group_raw_dict = getOrCreateS3Key(group_raw_key_name)
    group_vocab = group_raw_dict["vocab"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_freq_key_name = hdis_user.getFreqKeyName()
    user_freq_key, user_freq_dict = getOrCreateS3Key(user_freq_key_name)
    user_total_freqs = user_freq_dict["total_freq"]
    user_total_freqs_list = user_total_freqs.items()
    user_most_abnormal_words = map(lambda x: {"word":x[0],"freq":x[1]}, user_total_freqs_list)
    user_vocab = map(lambda x: x[0], user_total_freqs_list)
    user_unique = set(user_vocab).difference(set(group_vocab["1"])) # if only one user has said a word, it is unique to the user
    real_words = set(group_vocab["3"]) # real words are words which at least two users have said
    for x in user_most_abnormal_words:
        word = x["word"]
        f = x["freq"]
        group_f = group_total_freqs.get(word)
        if not group_f:
            ratio = 1000
        else:
            ratio = f / float(group_f)
        if (ratio > 1):
            x["often"] = True
            x["ratio_word"] = str(int(ratio))
        else:
            x["often"] = False
            x["ratio_word"] = "1/" + str(int(1/ratio))
        x["ratio"] = ratio

    user_most_abnormal_words.sort(key=lambda x: x["ratio"], reverse=True)
    user_most_abnormal_real_words = filter(lambda x: x["word"] in real_words, user_most_abnormal_words)
    # write most abnormal usage
    to_write = {
        "vocab_size":len(user_vocab),
        "abnormal":user_most_abnormal_real_words,
        "unique":list(user_unique)
    }
    abnormal_key_name = hdis_user.getAbnormalKeyName()
    abnormal_key = Key(bucket)
    abnormal_key.key = abnormal_key_name
    abnormal_key.set_contents_from_string(json.dumps(to_write))


def calcByTime(user_pin):
    print "by_time: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_key_name = hdis_user.getRawKeyName()
    bucket = getHDISBucket()
    user_key = bucket.get_key(user_key_name)
    user_td = TextData()
    user_td.loadFromS3Keys([user_key])
    user_td.calcByTime(resolution="hour")
    user_by_time = user_td.getJSONDumpableByTime()
    by_time_key_name = hdis_user.getByTimeKeyName()
    by_time_key, by_time_key_dict = getOrCreateS3Key(by_time_key_name)
    by_time_key.set_contents_from_string(json.dumps(user_by_time))


def calcSentimentByPerson(user_pin):
    print "sentiment by person: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    raw_key_name = hdis_user.getRawKeyName()
    raw_key, raw_key_dict = getOrCreateS3Key(raw_key_name)
    raw_key_json = raw_key.get_contents_as_string()
    sent_file_path = os.path.join(PROJECT_PATH, "static/AFINN-111.txt")
    sent_file = open(sent_file_path, "r")
    sentiment_by_person = calcSentimentByPersonFromRawJSON(raw_key_json, sent_file)
    sentiment_by_person_key_name = hdis_user.getSentimentByPersonKeyName()
    bucket = getHDISBucket()
    sentiment_by_person_key = Key(bucket)
    sentiment_by_person_key.key = sentiment_by_person_key_name
    sentiment_by_person_key.set_contents_from_string(json.dumps(sentiment_by_person))


def calcSentimentByHour(user_pin):
    print "sentiment by hour: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    raw_key_name = hdis_user.getRawKeyName()
    raw_key, raw_key_dict = getOrCreateS3Key(raw_key_name)
    raw_key_json = raw_key.get_contents_as_string()
    sent_file_path = os.path.join(PROJECT_PATH, "static/AFINN-111.txt")
    sent_file = open(sent_file_path, "r")
    sentiment_by_hour = calcSentimentByHourFromRawJSON(raw_key_json, sent_file)
    sentiment_by_hour_key_name = hdis_user.getSentimentByHourKeyName()
    bucket = getHDISBucket()
    sentiment_by_hour_key = Key(bucket)
    sentiment_by_hour_key.key = sentiment_by_hour_key_name
    sentiment_by_hour_key.set_contents_from_string(json.dumps(sentiment_by_hour))


def calcCategoriesByPerson(user_pin):
    print "categories by person: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    raw_key_name = hdis_user.getRawKeyName()
    raw_key, raw_key_dict = getOrCreateS3Key(raw_key_name)
    raw_key_json = raw_key.get_contents_as_string()
    categories_by_person_output = category_analysis_by_person(raw_key_json)
    bucket = getHDISBucket()
    out_key_name = hdis_user.getCategoriesByPersonKeyName()
    out_key = Key(bucket)
    out_key.key = out_key_name
    out_key.set_contents_from_string(json.dumps(categories_by_person_output))


def calcCategoriesTotal(user_pin):
    print "categories total: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    raw_key_name = hdis_user.getRawKeyName()
    raw_key, raw_key_dict = getOrCreateS3Key(raw_key_name)
    raw_key_json = raw_key.get_contents_as_string()
    categories_output = complete_category_analysis(raw_key_json)
    bucket = getHDISBucket()
    out_key_name = hdis_user.getCategoriesTotalKeyName()
    out_key = Key(bucket)
    out_key.key = out_key_name
    out_key.set_contents_from_string(json.dumps(categories_output))


# FIGURE OUT WHICH JOBS TO RUN ON WHICH USERS (who have already been registered in database)
# ======================================================================================================================

# check which jobs have been performed on a particular user_pin, by looking at which output files exist in that users folder
def whichJobsCompleted(user_pin):
    bucket = getHDISBucket()
    keys = bucket.list()
    jobs_completed = []
    for key in keys:
        name = key.name
        result = re.match("users/" + user_pin + "/(.+)", name)
        if result:
            file_name = result.group(1)
            jobs_completed.append(file_name)
    return jobs_completed


ALL_USER_JOBS = ["by_time.json","freq.json","most_used.json",
                 "abnormal.json","categories.json","categories_by_person.json","sentiment_by_person.txt",
                 "sentiment_by_hour.txt",] # all jobs to be done in order
def processUserPin(user_pin, force=False):
    print "processing: " + str(user_pin)
    jobs_completed = whichJobsCompleted(user_pin)
    for job in ALL_USER_JOBS:
        if force or (not job in jobs_completed):
            job_function_map = {
                "by_time.json":calcByTime,
                "freq.json":calcUserFreqs,
                "most_used.json":calcMostUsed,
                "abnormal.json":calcMostAbnormal,
                "categories.json":calcCategoriesTotal,
                "categories_by_person.json":calcCategoriesByPerson,
                "sentiment_by_person.txt":calcSentimentByPerson,
                "sentiment_by_hour.txt":calcSentimentByHour,
            }
            job_function_map[job](user_pin)
    # add user to groups is based on which groups are in tracker
    addUserToGroups(user_pin)

def processAllUsers():
    users = HowDoISpeakUser.objects.all()
    for user in users:
        processUserPin(user.user_pin)
        user.processed = True
        user.save()

# returns list of the names of the folders of all users on s3
def getS3UserFolders():
    bucket = getHDISBucket()
    keys = bucket.list()
    user_folders = []
    for key in keys:
        name = key.name
        result = re.match("users/.+/", name)
        if result:
            folder_name = result.group(0)
            user_folders.append(folder_name)
    user_folders = list(set(user_folders))
    user_folders.sort()
    return user_folders

# REGISTER RAW DATA AND MOVE IT TO USER FOLDERS
# ======================================================================================================================


# clear group calcs and reprocess all user and recalculate group data
def reprocessAllUsers():
    registerAllRawData()
    clearGroup("groups/all/")
    processAllUsers()
    recalcGroupData()

if __name__ == "__main__":
    reprocessAllUsers()

from hd_jobs.move_raw_data import moveRawData
from hd_jobs.add_user_to_groups import addUserToGroups, clearGroup
from hd_jobs.calculate_word_freq import calcFreqDicts, calcGroupFreqDicts, calcUserFreqDicts
from settings.common import getHDISBucket, getOrCreateS3Key
import re, json
from hdis.models import HowDoISpeakUser
from boto.s3.key import Key
from common.text_data import TextData



# =====================================================================================================================

def recalcGroupFreqs():
    print "** recalculating group freqs **"
    bucket = getHDISBucket()
    group_keys = getS3GroupKeys()
    for group_key in group_keys:
        total_freq, month_freqs = calcGroupFreqDicts(group_key, "month")
        new_key_name = group_key.name.replace("raw.json","freq.json")
        new_key = Key(bucket)
        new_key.key = new_key_name
        to_write_dict = {
            "total_freq":total_freq,
            "month_freqs":month_freqs
        }
        new_key.set_contents_from_string(json.dumps(to_write_dict))

def recalcMostAbnormal():
    users = HowDoISpeakUser.objects.filter(processed=True)
    for user in users:
        calcMostAbnormal(user.user_pin)

# =====================================================================================================================

# user jobs
def calcUserFreqs(user_pin):
    bucket = getHDISBucket()
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_key_name = hdis_user.getRawKeyName()
    user_key = bucket.get_key(user_key_name)
    total_freq,month_freqs = calcUserFreqDicts(user_key, "month")
    new_key_name = user_key.name.replace("raw.json","freq.json")
    new_key = Key(bucket)
    new_key.key = new_key_name
    to_write_dict = {
        "total_freq":total_freq,
        "month_freqs":month_freqs
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
    group_freq_key = bucket.get_key(group_freq_key_name)
    group_freq_json = group_freq_key.get_contents_as_string()
    group_freq_dict = json.loads(group_freq_json)
    group_total_freqs = group_freq_dict["total_freq"]
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_freq_key_name = hdis_user.getFreqKeyName()
    user_freq_key = bucket.get_key(user_freq_key_name)
    user_freq_json = user_freq_key.get_contents_as_string()
    user_freq_dict = json.loads(user_freq_json)
    user_total_freqs = user_freq_dict["total_freq"]
    user_total_freqs_list = user_total_freqs.items()
    def sort_fun(x):
        word = x[0]
        f = x[1]
        group_f = group_total_freqs.get(word)
        if not group_f:
            return 1
        else:
            return f / float(group_f)
    user_total_freqs_list.sort(key=sort_fun, reverse=True)
    user_most_abnormal_words = map(lambda x:x[0], user_total_freqs_list)
    abnormal_key_name = user_freq_key_name.replace("freq.json","abnormal.json")
    abnormal_key = Key(bucket)
    abnormal_key.key = abnormal_key_name
    abnormal_key.set_contents_from_string(json.dumps(user_most_abnormal_words))


def calcByTime(user_pin):
    print "by_time: " + str(user_pin)
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    user_key_name = hdis_user.getRawKeyName()
    bucket = getHDISBucket()
    user_key = bucket.get_key(user_key_name)
    user_td = TextData()
    user_td.loadFromS3Keys([user_key])
    user_td.calcByTime()
    user_by_time = user_td.getJSONDumpableByTime()
    by_time_key_name = hdis_user.getByTimeKeyName()
    by_time_key, by_time_key_dict = getOrCreateS3Key(by_time_key_name)
    by_time_key.set_contents_from_string(json.dumps(user_by_time))


def calcCategories(user_pin):
    hdis_user = HowDoISpeakUser.objects.get(user_pin=user_pin)
    raw_key_name = hdis_user.getRawKeyName()
    by_time_key_name = hdis_user.getByTimeKeyName()
    raw_key, raw_key_dict = getOrCreateS3Key(raw_key_name)
    by_time_key, by_time_key_dict = getOrCreateS3Key(by_time_key_name)
    to_write = {}
    # use raw__key_dict and by_time_key_dict to create an output
    # TODO:
    # output key
    categories_key_name = hdis_user.getCategoriesKeyName()
    categories_key, categories_dict = getOrCreateS3Key(categories_key_name)
    categories_key.set_contents_from_string(json.dumps(to_write))


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


ALL_USER_JOBS = ["by_time.json","freq.json","most_used.json","abnormal.json","categories.json"] # all jobs to be done in order
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
                "categories.json":calcCategories
            }
            job_function_map[job](user_pin)
    # add user to groups is based on which groups are in tracker
    addUserToGroups(user_pin)


# job handling and management
#######################################################################################################################

def registerRawData(s3_key):
    print "registering: " + str(s3_key.name)
    user = moveRawData(s3_key)
    user.enqueued = True
    user.save()

def processAllUsers():
    users = HowDoISpeakUser.objects.all()
    for user in users:
        processUserPin(user.user_pin)
        user.processed = True
        user.save()

def getS3RawKeys():
    bucket = getHDISBucket()
    keys = bucket.list()
    keys_list = []
    for key in keys:
        name = key.name
        result = re.match("raw/.+", name)
        if result:
            keys_list.append(key)
    return keys_list

def getS3GroupKeys():
    bucket = getHDISBucket()
    keys = bucket.list()
    keys_list = []
    for key in keys:
        name = key.name
        result = re.match("groups/.+", name)
        if result:
            keys_list.append(key)
    return keys_list

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
    return user_folders


def registerAllRawData():
    keys_list = getS3RawKeys()
    for s3_key in keys_list:
        registerRawData(s3_key)


def mainFun():
    recalcGroupFreqs()
    registerAllRawData()
    clearGroup("groups/all/")
    processAllUsers()
    recalcGroupFreqs()
    recalcMostAbnormal()

if __name__ == "__main__":
    mainFun()

from hdis.models import HowDoISpeakUser
import json, re, random, os, datetime
from settings.common import getHDISBucket, getOrCreateS3Key
from boto.s3.connection import S3Connection, Key
from settings.common import PROJECT_PATH, SECRETS_DICT, getS3Credentials

def makeTimeKeyFromPythonDate(p_date, resolution="day"):
    hour = p_date.hour
    day = p_date.day
    month = p_date.month
    year = p_date.year
    if resolution == "hour":
        return str(hour) + "|" + str(day) + "|" + str(month) + "|" + str(year)
    elif resolution == "day":
        return str(day) + "|" + str(month) + "|" + str(year)
    elif resolution == "month":
        return str(month) + "|" + str(year)
    elif resolution == "year":
        return str(year)

def makeTimeKeyFromTimeTuple(time_tuple):
    time_key = ""
    for index,e in enumerate(time_tuple):
        if index != (len(time_tuple)-1):
            time_key += e + "|"
        else:
            time_key += e
    return time_key

def getTimeTupleFromTimeString(time_string, resolution="hour"):
    if not isinstance(time_string, basestring):
        return time_string
    hour,day,month,year = time_string.split("|")
    if resolution == "hour":
        return hour,day,month,year
    elif resolution == "day":
        return day,month,year
    elif resolution == "month":
        return month,year
    elif resolution == "year":
        return year

def aggregateByTime(by_time, resolution="day"):
    to_return = {}
    for time_string, time_dict in by_time:
        time_tuple = getTimeTupleFromTimeString(time_string)
        if resolution == "day":
            time_tuple = time_tuple[-3:]
        elif resolution == "month":
            time_tuple = time_tuple[-2:]
        elif resolution == "year":
            time_tuple = time_tuple[-1:]
        time_key = makeTimeKeyFromTimeTuple(time_tuple)
        aggregate_counts = to_return.setdefault(time_key, {})
        for word,count in time_dict["1"]:
            prev_count = aggregate_counts.setdefault(word, 0)
            aggregate_counts[word] = prev_count + count
    return to_return


class TextData():

    def __init__(self):

        self.text = ""
        self.counts_dict = {}
        self.filtered_counts_dict = None
        self.by_time = None
        self.days_saved = None
        self.users_data = []
        self.usernames = set([])
        self.num_unknown = 0
        self.aws_access_key_id, self.aws_secret_access_key = getS3Credentials()

    def getUsernames(self):
        return list(self.usernames)

    def getUnknownID(self):
        self.num_unknown += 1
        return self.num_unknown

    def loadJSON(self, json_string):
        f_data = json.loads(json_string)
        original_user_name = user_name = f_data["user_meta"].get("user_name")
        if not original_user_name:
            user_name = "unknown" + str(self.num_unknown)
        else:
            if original_user_name in self.usernames: user_name += str(self.num_unknown)
        user_data = {
            "user_name":user_name,
            "ip_address":f_data["user_meta"].get("ip_address")
        }
        self.usernames.add(user_name)
        self.users_data.append(user_data)
        for key,count_dict in f_data["counts"].items():
            from_user, to_user = key.split("|")
            # these two lines help avoid name conflicts (in case we have 2 users with the same name)
            if from_user == original_user_name: from_user = user_name
            if to_user == original_user_name: to_user = user_name
            # store the count_dict (we should never be ovewrriting, because conversations should be unique)
            self.counts_dict[(from_user,to_user)] = count_dict

    def filterTextDataByTime(self, start_time, end_time):
        counts_dict = self.getCountsDict()
        filtered_dict = self.filtered_counts_dict = {}
        for conversation_tuple,conversation_dict in counts_dict.items():
            filtered_conversation_dict = {}
            for time_key,time_dict in conversation_dict.items():
                hour,day,month,year = getTimeTupleFromTimeString(time_key)
                text_time = datetime.datetime(year=year, month=month, day=day, hour=hour)
                if start_time and end_time:
                    if text_time > start_time and text_time < end_time:
                        filtered_conversation_dict[time_key] = time_dict
                elif start_time:
                    if text_time > start_time:
                        filtered_conversation_dict[time_key] = time_dict
                elif end_time:
                    if text_time < end_time:
                        filtered_conversation_dict[time_key] = time_dict
                else:
                    filtered_conversation_dict[time_key] = time_dict
            filtered_dict[conversation_tuple] = filtered_conversation_dict

    def filterDataByUsers(self, to_users=None, from_users=None):
        counts_dict = self.getCountsDict()
        filtered_dict = self.filtered_counts_dict = {}
        for conversation_tuple,conversation_dict in counts_dict.items():
            from_user,to_user = conversation_tuple
            if to_users and from_users:
                if to_user in to_users and from_user in from_users:
                    filtered_dict[conversation_tuple] = conversation_dict
            elif to_users:
                if to_user in to_users:
                    filtered_dict[conversation_tuple] = conversation_dict
            elif from_users:
                if from_user in from_users:
                    filtered_dict[conversation_tuple] = conversation_dict

    def removeFilters(self):
        self.filtered_counts_dict = None

    def loadFromJSONFiles(self, file_paths):
        for file_path in file_paths:
            f = open(file_path, "r")
            self.loadJSON(f.read())

    def loadFromS3Keys(self, s3_keys):
        for k in s3_keys:
            json_string = k.get_contents_as_string()
            self.loadJSON(json_string)

    def getS3Keys(self, num=0):
        conn = S3Connection(self.aws_access_key_id, self.aws_secret_access_key)
        bucket = conn.get_bucket('howdoispeak')
        keys = bucket.list()
        keys_list = []
        for key in keys:
            keys_list.append(key)
        if num:
            keys_list = random.sample(keys_list, num)
        return keys_list

    def getCountsDict(self):
        if self.filtered_counts_dict:
            counts_dict = self.filtered_counts_dict
        else:
            counts_dict = self.counts_dict
        return counts_dict

    def calcTextBlobs(self):
        text_blob = ""
        counts_dict = self.getCountsDict()
        for conversation_tuple,conversation_dict in counts_dict.items():
            conversation_text_blob = ""
            for time_key,time_dict in conversation_dict.items():
                time_block_text_blob = ""
                words_counts = time_dict.get("1") or {} # 1 is ungrams, 2 is bigrams, 3 is trigams etc
                for word,count in words_counts.items():
                    for i in range(count):
                        time_block_text_blob += " " + word
                time_dict["text_blob"] = time_block_text_blob
                conversation_text_blob += time_block_text_blob
            conversation_dict["text_blob"] = conversation_text_blob
            text_blob += conversation_text_blob
        return text_blob

    # resolution is what interval to group times by
    def calcByTime(self,resolution="hour"):
        by_time = self.by_time = {}
        days_saved = self.days_saved = set([]) # days on which a text was sent
        counts_dict = self.getCountsDict()
        for conversation_tuple,conversation_dict in counts_dict.items():
            for time_key,time_dict in conversation_dict.items():
                day_tuple = getTimeTupleFromTimeString(time_key, "day")
                days_saved.add(day_tuple)
                time_tuple = getTimeTupleFromTimeString(time_key, resolution)
                relevant_dict = by_time.setdefault(time_tuple,{"1":{},"text_blob":"","num_texts":0})
                relevant_counts_dict = relevant_dict.get("1")
                relevant_text_blob = relevant_dict.get("text_blob")
                relevant_dict["num_texts"] += time_dict.get("num_texts",0)
                words_counts = time_dict.get("1") or {} # 1 is ungrams, 2 is bigrams, 3 is trigams etc
                for word,count in words_counts.items():
                    relevant_count = relevant_counts_dict.setdefault(word,0)
                    relevant_counts_dict[word] = relevant_count + count
                    for i in range(count):
                        relevant_text_blob += " " + word
                relevant_dict["text_blob"] = relevant_text_blob

    def getByTime(self):
        return self.by_time

    def getJSONDumpableByTime(self):
        by_time = self.getByTime()
        to_return = {}
        for time_tuple, time_dict in by_time.items():
            time_key = makeTimeKeyFromTimeTuple(time_tuple)
            to_return[time_key] = time_dict
        return to_return

    def getDaysSaved(self):
        return self.days_saved

    def getByTimeDictsInOrder(self):
        return self.returnOrderedTimeDict(self.by_time)

    def calcTextCounts(self, username):
        self.removeFilters()
        text_counts = {}
        self.calcByTime("month")
        for time_key,time_dict in self.getByTimeDictsInOrder():
            counts = text_counts.setdefault(time_key, {})
            counts["all"] = time_dict["num_texts"]
        self.removeFilters()
        self.filterDataByUsers(from_users=[username])
        self.calcByTime("month")
        for time_key,time_dict in self.getByTimeDictsInOrder():
            counts = text_counts.setdefault(time_key, {})
            counts["from"] = time_dict["num_texts"]
        self.removeFilters()
        self.filterDataByUsers(to_users=[username])
        self.calcByTime("month")
        for time_key,time_dict in self.getByTimeDictsInOrder():
            counts = text_counts.setdefault(time_key, {})
            counts["to"] = time_dict["num_texts"]
        return text_counts

    def compareTimeTuples(self, tuple_a,tuple_b):
            len_a = len(tuple_a)
            len_b = len(tuple_b)
            if len_a != len_b: print "wtf"
            for i in range(0,len_a):
                a = int(tuple_a[len_a-i-1])
                b = int(tuple_b[len_b-i-1])
                if a < b:
                    return -1
                elif a > b:
                    return 1
            return 0

    def returnOrderedTimeDict(self, time_dict):
        time_keys = time_dict.keys()
        time_keys.sort(cmp=self.compareTimeTuples)
        to_return = []
        for time_key in time_keys:
            t_dict = time_dict[time_key]
            to_return.append((time_key,t_dict))
        return to_return


if __name__ == "__main__":
    td = TextData()
    s3_keys = td.getS3Keys()
    the_key = None
    for key in s3_keys:
        if "hendrik" in key.name:
            the_key = key
    td.loadFromS3Keys([the_key])
    username = random.choice(list(td.usernames)[0])
    text_counts = td.calcTextCounts(username)
    for time_key, counts in td.returnOrderedTimeDict(text_counts):
        print str(time_key) + " " + str(counts["all"]) + " " + str(counts["from"]) + " " + str(counts["to"])
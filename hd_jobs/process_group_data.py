from hd_jobs.common import *
from hd_jobs.calculate_word_freq import calcGroupFreqDicts

# JOBS FOR GROUPS
# =====================================================================================================================

# recalculate groups freqs and then update users abnormal.json files appropriately
def recalcGroupData():
    calcGroupFreqs()
    recalcMostAbnormal()

# for each group create freq.json from its raw.json
def calcGroupFreqs():
    print "** recalculating group freqs **"
    bucket = getHDISBucket()
    group_folders = getS3GroupFolders()
    for group_folder in group_folders:
        print "group freq: " + str(group_folder)
        group_key_name = group_folder + "raw.json"
        group_key, group_key_dict = getOrCreateS3Key(group_key_name)
        total_freq,month_freqs,day_freqs = calcGroupFreqDicts(group_key, "month")
        new_key_name = group_key.key.replace("raw.json","freq.json")
        new_key = Key(bucket)
        new_key.key = new_key_name
        to_write_dict = {
            "total_freq":total_freq,
            "month_freqs":month_freqs,
            "day_freqs":day_freqs
        }
        new_key.set_contents_from_string(json.dumps(to_write_dict))

# as freq.json is updated for groups, what words users use that are most abnormal may change, thus need 2 update
def recalcMostAbnormal():
    from hd_jobs.process_user_data import calcMostAbnormal
    users = HowDoISpeakUser.objects.filter(processed=True)
    for user in users:
        calcMostAbnormal(user.user_pin)

# returns the s3 keys of all group
def getS3GroupFolders():
    bucket = getHDISBucket()
    keys = bucket.list()
    group_folders = set([])
    for key in keys:
        name = key.name
        result = re.match("groups/(.+)/.*", name)
        if result:
            folder_name = "groups/" + result.group(1) + "/"
            group_folders.add(folder_name)
    return group_folders
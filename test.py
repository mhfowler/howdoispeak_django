from hd_jobs.add_user_to_groups import addUserToGroup, clearGroup
from hd_jobs.process_user_data import registerAllRawData, \
    calcByTime, getS3UserFolders, processAllUsers, \
    calcUserFreqs, calcMostAbnormal, calcCategoriesTotal, calcCategoriesByPerson, clearFileFromUsers, \
    calcSentimentByHour, calcSentimentByPerson
from hd_jobs.process_group_data import recalcGroupData
from hdis.models import HowDoISpeakUser
from hd_jobs.common import *

if __name__ == "__main__":
    # getS3UserFolders()
    # clearGroup("groups/all/")
    # clearFileFromUsers("categories.json")
    # clearFileFromUsers("categories_by_person.json")
    # clearFileFromUsers("sentiment_by_person.txt")
    # clearFileFromUsers("sentiment_by_hour.txt")
    # processAllUsers()
    # calcSentimentByHour(2738430634)
    calcSentimentByPerson(4163380919)
    # processAllUsers()
    # recalcGroupData()
    users = HowDoISpeakUser.objects.all()
    for user in users:
        # calcSentimentByHour(user.user_pin)
        calcSentimentByPerson(user.user_pin)
        # calcMostAbnormal(user.user_pin)
    #     calcUserFreqs(user.user_pin)
    # calcUserFreqs(4163380919)
    # recalcGroupData()
    # calcMostAbnormal(4163380919)
    # calcCategoriesByPerson(4163380919)
    # calcCategoriesTotal(4163380919)


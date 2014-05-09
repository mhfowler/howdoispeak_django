from hd_jobs.add_user_to_groups import addUserToGroup, clearGroup
from hd_jobs.process_user_data import registerAllRawData, \
    calcByTime, getS3UserFolders, processAllUsers, \
    calcUserFreqs, calcMostAbnormal, calcCategoriesTotal, calcCategoriesByPerson
from hd_jobs.process_group_data import recalcGroupData
from hdis.models import HowDoISpeakUser
from hd_jobs.common import *

if __name__ == "__main__":
    # getS3UserFolders()
    # processAllUsers()
    # users = HowDoISpeakUser.objects.all()
    # for user in users:
        # calcMostAbnormal(user.user_pin)
    #     calcUserFreqs(user.user_pin)
    # calcUserFreqs(4163380919)
    # recalcGroupData()
    # calcMostAbnormal(4163380919)
    calcCategoriesByPerson(4163380919)
    calcCategoriesTotal(4163380919)

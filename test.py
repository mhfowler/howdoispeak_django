from hd_jobs.add_user_to_groups import addUserToGroup, clearGroup
from hd_jobs.process_raw_data import registerAllRawData, recalcGroupFreqs, mainFun, recalcMostAbnormal, calcByTime
from hdis.models import HowDoISpeakUser

if __name__ == "__main__":
    # addUserToGroup("6996200796") # add max to group
    # enqueuAll()
    # recalcGroupFreqs()
    # mainFun()
    # clearGroup("groups/all/")
    # recalcGroupFreqs()
    # recalcMostAbnormal()
    users = HowDoISpeakUser.objects.all()
    for u in users:
        calcByTime(u.user_pin)

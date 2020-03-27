import os
import shutil
import json
from datetime import datetime, timedelta
from time import sleep

while True:
    path = '/tmp/onboarding/'
    for directory in list(os.listdir(path)):
        with open(path + directory + '/data.json') as json_file:

            data = json.load(json_file)
            if datetime.fromtimestamp(data.get('timestamp')) < (datetime.now() - timedelta(hours=2)):
                shutil.rmtree(path + directory)
    sleep(60*60)

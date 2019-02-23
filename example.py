"""


pre-reqs: Python 3.x, requests, and google-api-python-client libraries
Last modified: Feb 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import os
import sys
import logging
import argparse
import datetime
from datetime import datetime,timedelta
import json
import random
import assets.mediasite.controller as controller

if __name__ == "__main__":
    """
    args:
        --file: json configuration file
    """

    #gather our runpath for future use with various files
    run_path = os.path.dirname(os.path.realpath(__file__))

    #log file datetime
    current_datetime_string = '{dt.month}-{dt.day}-{dt.year}_{dt.hour}-{dt.minute}-{dt.second}'.format(dt = datetime.now())
    logfile_path = run_path+'/test_'+current_datetime_string+'.log'

    #logger for log file
    logging_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging_datefmt = '%m/%d/%Y - %I:%M:%S %p'
    logging.basicConfig(filename=logfile_path,
                        filemode='w',
                        format=logging_format,
                        datefmt=logging_datefmt,
                        level=logging.INFO
                        )

    #logger for console
    console = logging.StreamHandler()
    formatter = logging.Formatter(logging_format, datefmt=logging_datefmt)
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

    #open config file with configuration info
    config_file = open(run_path+"/config/config.json")
    config_data = json.load(config_file)

    #creating the mediasite controller
    mediasite = controller.controller(config_data)

    catalogs = mediasite.catalog.get_all_catalogs()

    for catalog in catalogs:
        if not catalog["LinkedFolderId"]:
            print(catalog["Name"])
    


   








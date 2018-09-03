"""
Mediasite controller for medaisite scheduler. Performs various Mediasite API
work using web_api client.

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import os
import sys
import logging
import json
import time
import assets.mediasite.model as model
import assets.mediasite.api_client as api_client
import assets.mediasite.modules.module as module
import assets.mediasite.modules.schedule as schedule
import assets.mediasite.modules.catalog as catalog
import assets.mediasite.modules.recorder as recorder
import assets.mediasite.modules.folder as folder
import assets.mediasite.modules.template as template
import assets.mediasite.modules.report as report
import assets.mediasite.modules.presentation as presentation

class controller():
    def __init__(self, config_data, *args, **kwargs):
        """
        params:
            model: complementary model for storing various mediasite data related to this controller
            run_path: root path where the application is being run from on the system
        """
        self.model = model.model()
        self.config_data = config_data
        self.api_client = self.create_api_client(config_data)
        self.module = module.module(self)
        self.schedule = schedule.schedule(self)
        self.catalog = catalog.catalog(self)
        self.recorder = recorder.recorder(self)
        self.folder = folder.folder(self)
        self.template = template.template(self)
        self.report = report.report(self)
        self.presentation = presentation.presentation(self)

    def create_api_client(self, config_data):
        """
        Loads configuration file data and creates new Mediasite api client using web_api.py

        params:
            config_data: dictionary containing information relevant to setting up mediasite api connection

        returns:
            Configured Mediasite web api client object
        """

        return api_client.client(config_data["base_url"],
                                        config_data["api_secret"],
                                        config_data["api_user"],
                                        config_data["api_pass"]
                                        )

    def connection_validated(self):
        """
        Validates Mediasite connection through web api through request for "home" information from Mediasite

        returns:
            True if connection is confirmed to work, false if not
        """

        #request mediasite home information - contains various site-level details
        result = self.api_client.request("get", "Home", "","")

        if self.experienced_request_errors(result):
            logging.error("Experienced errors while attempting to validate Mediasite connection")
            self.model.set_current_connection_valid(False)
            return False
        else:
            self.model.set_current_connection_valid(True)
            return True

    def experienced_request_errors(self, request_result):
        """
        Checks for errors experienced from web_api Python requests.

        params:
            request_result: returned content from web_api request peformed

        returns:
            true if errors were experienced, false if no errors experienced
        """

        if type(request_result) is str:
            logging.error(request_result)
            self.model.set_current_connection_valid(False)
            return True
        else:
            return False

    def wait_for_job_to_complete(self, job_link_url):
        """
        Function for checking on and waiting for completion or error status of jobs in
        Mediasite system using Mediasite API.

        arguments:
            job_link_url: unique link to Mediasite job which can be used for gathering status
        """
        while 1:
            #gather information on the job status
            job_result = self.api_client.request("get job", job_link_url, "", "").json()
            
            if self.experienced_request_errors(job_result):
                return job_result
            else:
                if "Status" in job_result.keys():
                    job_result_status = job_result["Status"]

                    #if successful we return
                    if job_result_status == "Successful":
                        logging.info("Job was successful")
                        return

                    #if the job fails or is canceled for some reason exit
                    elif job_result_status == "Disabled" or job_result_status == "Failed" or job_result_status == "Cancelled":
                        logging.error("Job did not complete successfully with a status of "+job_result_status)
                        logging.error("Job status information: "+job_result["StatusMessage"])
                        return
                    #if the job is queued or working we wait for the job to finish or fail
                    else:
                        logging.info("Waiting for job to complete. Job status: "+job_result_status)
                        time.sleep(5)
                else:
                    return job_result

        def process_scheduling_data_row(self, schedule_data):
            """
            Process scheduling data provided in pre-specified format.

            params:
                schedule_data: list which contain pertinent mediasite scheduling data

            returns:
                output indicating which rows of scheduling information were successfully scheduled
            """

            row_result = {}

            validation_result = self.schedule.validate_scheduling_data(schedule_data)

            #validate the scheduling data
            if "error" in validation_result.keys():
                row_result["error"] = validation_result["error"]
                return row_result

            #parse and create folders
            parent_folder_id = self.folder.parse_and_create_folders(schedule_data["folders"], schedule_data["folder_root_id"])
            
            #set the current schedule data parent folder id
            schedule_data["schedule_parent_folder_id"] = parent_folder_id

            #parse and create module
            if schedule_data["module_include"]:
                module_result = self.module.create_module(schedule_data["module_name"], schedule_data["module_id"])
                row_result["module_result"] = module_result

            #parse and create catalog
            if schedule_data["catalog_include"]:
                catalog_result = self.catalog.create_catalog(schedule_data["catalog_name"], schedule_data["catalog_description"], schedule_data["schedule_parent_folder_id"])
                row_result["catalog_result"] = catalog_result

            #enable catalog downloads
            if schedule_data["catalog_include"] and schedule_data["catalog_enable_download"]:
                self.catalog.enable_catalog_downloads(catalog_result["Id"])

            #disable catalog links
            if schedule_data["catalog_include"] and not schedule_data["catalog_allow_links"]:
                self.catalog.disable_catalog_allow_links(catalog_result["Id"])

            #link module to catalog
            if schedule_data["module_include"] and schedule_data["catalog_include"]:
                self.catalog.add_module_to_catalog(catalog_result["Id"], module_result["Id"])

            schedule_result = self.schedle.create_schedule(schedule_data)
            row_result["schedule_result"] = schedule_result

            if "odata.error" not in schedule_result:
                recurrence_result = self.schedule.create_recurrence(schedule_data, schedule_result)
                row_result["recurrence_result"] = recurrence_result

            return row_result

    def validate_scheduling_data(self, schedule_data):
        """
        Validate user entered data and notify them of any corrections using error dialogs

        returns:
            true if no errors were encountered, false if any errors were encountered
        """
        """
        if self.parse_and_check_for_recycled_folders(schedule_data["folders"], schedule_data["folder_root_id"]):
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - Submitted folders may already exist in recyle bin. Please empty recycle bin and try again."}
            logging.error(result["error"])
            return result
        """

        if schedule_data["catalog_include"] and schedule_data["catalog_name"] == "":
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - Submitted schedule data has no catalog name."}
            logging.error(result["error"])
            return result

        if self.schedule.schedule_data_has_0_occurrences(schedule_data):
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - Submitted schedule data does not contain at least one occurrence."}
            logging.error(result["error"])
            return result

        if schedule_data["module_include"] and schedule_data["module_id"] == "":
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - No module Id specified."}
            logging.error(result["error"])
            return result

        if schedule_data["module_include"] and self.module.module_moduleid_already_exists(schedule_data["module_id"]):
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - Submitted ModuleId already exists."}
            logging.error(result["error"])
            return result

        if schedule_data["schedule_template"] in self.model.get_templates():
            result = {"error":"Error: " + schedule_data["schedule_name"] + " - Submitted template name does not exist."}
            logging.error(result["error"])
            return result

        return {"Success":""}
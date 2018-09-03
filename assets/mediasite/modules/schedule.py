"""
Mediasite client class for schedule-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""


import logging
import time
import datetime
import pytz
import tzlocal
import datetime
from dateutil import rrule

class schedule():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def create_schedule(self, schedule_data):
        """
        Creates mediasite schedule using provided schedule data

        params:
            schedule_data: dictionary containing various necessary data for creating mediasite scheduling

        Expects schedule_data to contain the following keys:
        schedule_data = {
            "ms_folder_root_id":string,
            "ms_folders":string,
            "catalog_include":boolean,
            "catalog_name":string,
            "catalog_description":string,
            "catalog_enable_download":boolean,
            "module_include":boolean,
            "module_name":string,
            "module_id":string,
            "schedule_parent_folder_id":string,
            "schedule_template":string,
            "schedule_name":string,
            "schedule_naming_scheme":string,
            "schedule_recorder":string,
            "schedule_recurrence":string,
            "schedule_auto_delete":string,
            "schedule_start_datetime_utc_string":string,
            "schedule_end_datetime_utc_string":string,
            "schedule_start_datetime_utc":datetime,
            "schedule_end_datetime_utc":datetime,
            "schedule_start_datetime_local_string":string,
            "schedule_end_datetime_local_string":string,
            "schedule_start_datetime_local":datetime,
            "schedule_end_datetime_local":datetime,
            "schedule_duration":string,
            "schedule_recurrence_freq":string,
            "schedule_days_of_week":{
                "Sunday":boolean,
                "Monday":boolean,
                "Tuesday":boolean,
                "Wednesday":boolean,
                "Thursday":boolean,
                "Friday":boolean,
                "Saturday":boolean
                }
            }

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Creating schedule '"+schedule_data["schedule_name"])

        current_datetime_string = '{dt.month}-{dt.day}-{dt.year}_{dt.hour}-{dt.minute}-{dt.second}'.format(dt = datetime.datetime.now())
    
        schedule_naming_scheme = self.mediasite.model.translate_schedule_recurrence_naming(schedule_data["schedule_naming_scheme"])
        schedule_template_id = self.mediasite.model.translate_template_id(schedule_data["schedule_template"])
        schedule_recorder_id = self.mediasite.model.translate_recorder_id(schedule_data["schedule_recorder"])

        post_data = {"Name":schedule_data["schedule_name"],
                    "FolderId":schedule_data["schedule_parent_folder_id"],
                    "TitleType":schedule_naming_scheme,
                    "ScheduleTemplateId":schedule_template_id,
                    "IsUploadAutomatic":"True",
                    "RecorderId":schedule_recorder_id,
                    "RecorderName":schedule_data["schedule_recorder"],
                    "CreatePresentation":"True",
                    "LoadPresentation":"True",
                    "AutoStart":"True",
                    "AutoStop":"True",
                    "AdvanceCreationTime":7200,
                    "NotifyPresenter":"False",
                    "Description":"Scheduled by "+ os.getlogin() + " on " + current_datetime_string + " using Mediasite Scheduler",
                    "DeleteInactive":schedule_data["schedule_auto_delete"]
                    }

        result = self.mediasite.api_client.request("post", "Schedules", "", post_data).json()
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])
            else:
                self.mediasite.model.add_schedule(result)

            return result

    def translate_schedule_days_of_week(self, schedule_data):
        """
        Translates days of the week to schedule into Mediasite-friendly format as per API documentation

        params:
            schedule_data: dictionary containing various necessary data for creating mediasite scheduling

        returns:
            string which is ready to be sent to Mediasite for schedule recurrences
        """
        result_string = ""
        count = 0

        #for each day of week element, see if value is true, and if so append to a string containing all other days in order
        for key,val in schedule_data["schedule_days_of_week"].items():
            if val == True:
                if count > 0:
                    result_string += "|"

                result_string += key
                count += 1

        return result_string

    def to_dateutil_weekdays(self, recurrence_days_of_week):
        """
        Translates days of week from Mediasite-friendly convention to Dateutil-friendly format

        params:
            recurrence_days_of_week: Mediasite-friendly days of the week string

        returns:
            string which is ready to be sent to Dateutil for schedule dates recurrences
        """

        result_list = []

        if "Sunday" in recurrence_days_of_week:
            result_list.append(rrule.SU)
        if "Monday" in recurrence_days_of_week:
            result_list.append(rrule.MO)
        if "Tuesday" in recurrence_days_of_week:
            result_list.append(rrule.TU)
        if "Wednesday" in recurrence_days_of_week:
            result_list.append(rrule.WE)
        if "Thursday" in recurrence_days_of_week:
            result_list.append(rrule.TH)
        if "Friday" in recurrence_days_of_week:
            result_list.append(rrule.FR)            
        if "Saturday" in recurrence_days_of_week:
            result_list.append(rrule.SA)

        return result_list

    def convert_datetime_local_to_utc(self, datetime_local):
        """
        Translate local datetime to utc for use by internal Mediasite system

        params:
            datetime_local: local datetime object

        returns:
            converted utc datetime object
        """

        #find UTC times for datetimes due to Mediasite requirements
        UTC_OFFSET_TIMEDELTA = datetime.datetime.utcnow() - datetime.datetime.now()

        return datetime_local + UTC_OFFSET_TIMEDELTA

    def recurrence_datelist_generator(self, schedule_data):
        """
        Create a list of dates based on schedule data gathered for Mediasite recording scheduling

        params:
            schedule_data: dictionary containing various necessary data for creating mediasite scheduling

        returns:
            list of recurrence datetimes based on the schedule data
        """
        days_of_week = self.translate_schedule_days_of_week(schedule_data)

        #check that we have days of the week specified - dateutil returns all dates if none are specified (unwanted in this case)
        if days_of_week == "":
            return []

        rule = rrule.rrule(dtstart = schedule_data["schedule_start_datetime_local"], 
                            freq = rrule.DAILY,
                            byweekday = self.to_dateutil_weekdays(days_of_week)
                            )

        datelist = rule.between(schedule_data["schedule_start_datetime_local"],
                                schedule_data["schedule_end_datetime_local"],
                                inc = True
                                )

        return datelist

    def schedule_data_has_0_occurrences(self, schedule_data):
        """
        Determine whether the current schedule data contains 0 occurrences to avoid errors

        returns:
            true if there are 0 occurrences in the schedule data, false if there are more than 0 occurrences
        """
        datelist = self.recurrence_datelist_generator(schedule_data)

        if len(datelist) <= 0:
            logging.error("Submitted schedule data does not contain at least one occurrence.")
            return True
        else:
            return False

    def create_recurrence(self, schedule_data, schedule_result):
        """
        Creates Mediasite schedule recurrence. Specifically, this is the datetimes which a recording schedule
        will produce presentations with.

        params:
            schedule_data: dictionary containing various necessary data for creating mediasite scheduling
            schedule_result: data provided from Mediasite after a schedule is produced

        returns:
            resulting response from the mediasite web api request
        """
        logging.info("Creating schedule recurrence(s) for '"+schedule_data["schedule_name"])

        #convert duration minutes to milliseconds as required by Mediasite system
        recurrence_duration = int(schedule_data["schedule_duration"])*60*1000

        #translate various values gathered from the UI to Mediasite-friendly conventions
        recurrence_type = self.mediasite.model.translate_schedule_recurrence_pattern(schedule_data["schedule_recurrence"])

        #creates a recurrence using post_data created below
        def request_create_recurrence(post_data):
            result = self.mediasite.api_client.request("post", "Schedules('"+schedule_result["Id"]+"')/Recurrences", "", post_data).json()

            if self.mediasite.experienced_request_errors(result):
                return result
            else:
                if "odata.error" in result:
                    logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])
                else:
                    self.mediasite.model.add_recurrence(result)

        result = ""

        #for one-time recurrence creation
        if recurrence_type == "None":
            post_data = {"MediasiteId":schedule_result["Id"],
                "RecordDuration":recurrence_duration,
                "StartRecordDateTime":schedule_data["schedule_start_datetime_utc_string"],
                "EndRecordDateTime":schedule_data["schedule_end_datetime_utc_string"],
                "RecurrencePattern":recurrence_type,
                "RecurrenceFrequency":schedule_data["schedule_recurrence_freq"],
                "DaysOfTheWeek":self.translate_schedule_days_of_week(schedule_data)
                }

            result = request_create_recurrence(post_data)

        elif recurrence_type == "Weekly":
            #for weekly recurrence creation
            """
            NOTE: due to bugs in Mediasite system we defer to using one-time schedules for each day of the week
            specified within the provided time frame. This produces more accurate and stable results as of the time
            of writing this in Feb 2018.
            """

            #determine date range for use in creating single instances which are less error-prone
            datelist = self.recurrence_datelist_generator(schedule_data)

            #for each date in the list produced above, we create post data and request a one-time schedule recurrence
            for date in datelist:

                ms_friendly_datetime_start_utc = self.convert_datetime_local_to_utc(date)
                ms_friendly_datetime_start = ms_friendly_datetime_start_utc.strftime("%Y-%m-%dT%H:%M:%S")

                #find our current timezone
                local_tz = tzlocal.get_localzone()

                #check if current datetime is dst or not
                now = datetime.datetime.now()
                #is_now_dst = now.astimezone(local_tz).dst() != datetime.timedelta(0)
                is_now_dst = local_tz.localize(now).dst() != datetime.timedelta(0)

                #check if future datetime is dst or not
                #is_later_dst = date.astimezone(local_tz).dst() != datetime.timedelta(0)
                is_later_dst = local_tz.localize(date).dst() != datetime.timedelta(0)

                #compare between the current and future datetimes to find differences and adjust
                if is_now_dst != is_later_dst:

                    #convert future datetime to be an hour more or less bast on dst comparison above
                    if is_now_dst and not is_later_dst:
                        ms_friendly_datetime_start = (ms_friendly_datetime_start_utc + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
                    
                    elif not is_now_dst and is_later_dst:
                        ms_friendly_datetime_start = (ms_friendly_datetime_start_utc - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

                post_data = {"MediasiteId":schedule_result["Id"],
                            "RecordDuration":recurrence_duration,
                            "StartRecordDateTime":ms_friendly_datetime_start,
                            "RecurrencePattern":"None",
                            }
                
                request_create_recurrence(post_data)

            return result

        return result

    def gather_recurrences(self, schedule_id):
        """
        Gathers recurrences for specified Mediasite schedule by ID

        params:
            schedule_id: Mediasite schedule ID which you would like to find recurrences for.

        returns:
            resulting response from the mediasite web api request
        """
        result = self.mediasite.api_client.request("get", "Schedules('"+schedule_id+"')/Recurrences", "", "").json()
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def process_batch_scheduling_data(self, batch_scheduling_data):
        """
        Process batch scheduling data provided in pre-specified format.

        params:
            batch_scheduling_data: list of dictionaries which contain pertinent mediasite scheduling data

        returns:
            output indicating which rows of scheduling information were successfully scheduled
        """

        result_list = []

        #parse each row of scheduling data
        for row in batch_scheduling_data:

            #gather and organize schedule data
            schedule_data = self.gather_import_schedule_data(row)

            #perform mediasite-specific work using schedule_data for row
            row_result = self.process_scheduling_data_row(schedule_data)

            #append results to the overall list
            result_list.append(row_result)

        return result_list

    def fix_12_hour_time_padding(self, time_string):
        """
        Ensure 12 hour times have additional 0 in front of single digit numbers for later conversions

        params:
            time_string: 12 hour time string, for example "1:00 PM"

        returns:
            true if no errors were encountered, false if any errors were encountered
        """
        if len(time_string) == 7:
            time_string = "0" + time_string

        return time_string

    def gather_import_schedule_data(self, scheduling_data):
        """
        Parse, convert, and request mediasite schedule creation

        Note - default date time formats:
            Mediasite: 9999-12-31T23:59:59

        scheduling_data keys:
        -------------------
        Presentation Title
        Recorder
        Template
        Naming Scheme
        Delete Schedule After Occurrences
        Include Catalog
        Allow Catalog Links
        Enable Catalog Download
        Catalog Name
        Catalog Description
        Include Module
        Module Name
        Module ID
        Mediasite Folder
        Recurrence
        Start Date
        End Date
        Start Time
        End Time
        Recurrence Frequency
        Sun
        Mon
        Tue
        Wed
        Thu
        Fri
        Sat

        params:
            parent_folder_id: mediasite folder id which the schedule will be associated with
        returns:
            mediasite api output for schedule creation
        """

        #scheduling_data["Start Time"] = self.fix_12_hour_time_padding(scheduling_data["Start Time"])
        #scheduling_data["End Time"] = self.fix_12_hour_time_padding(scheduling_data["End Time"])

        local_start_datetime_string_intake = scheduling_data["Start Date"] + "T" + scheduling_data["Start Time"]
        local_end_datetime_string_intake = scheduling_data["End Date"] + "T" + scheduling_data["End Time"]

        #find duration in minutes from provided data
        local_start_time = datetime.datetime.strptime(scheduling_data["Start Time"], "%I:%M %p")
        local_end_time = datetime.datetime.strptime(scheduling_data["End Time"], "%I:%M %p")
        duration_in_minutes = int((local_end_time - local_start_time).seconds/60)

        #find UTC times for datetimes due to Mediasite requirements
        local_start_datetime = datetime.datetime.strptime(local_start_datetime_string_intake, "%m/%d/%yT%I:%M %p").replace(second=10)
        local_end_datetime = datetime.datetime.strptime(local_end_datetime_string_intake, "%m/%d/%yT%I:%M %p").replace(second=10)
        utc_start_datetime = self.convert_datetime_local_to_utc(local_start_datetime).replace(second=10)
        utc_end_datetime = self.convert_datetime_local_to_utc(local_end_datetime).replace(second=10)
        utc_start_datetime_string = utc_start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        utc_end_datetime_string = utc_end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        local_start_datetime_string = local_start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        local_end_datetime_string = local_end_datetime.strftime("%Y-%m-%dT%H:%M:%S")

        schedule_data_submit = {
            "folder_root_id":"",
            "folders":scheduling_data["Mediasite Folder"],
            "catalog_include":True if scheduling_data["Include Catalog"] == "TRUE" else False,
            "catalog_name":scheduling_data["Catalog Name"],
            "catalog_description":scheduling_data["Catalog Description"],
            "catalog_enable_download":True if scheduling_data["Enable Catalog Download"] == "TRUE" else False,
            "catalog_allow_links":True if scheduling_data["Allow Catalog Links"] == "TRUE" else False,
            "module_include":True if scheduling_data["Include Module"] == "TRUE" else False,
            "module_name":scheduling_data["Module Name"],
            "module_id":scheduling_data["Module ID"],
            "schedule_parent_folder_id":"",
            "schedule_template":scheduling_data["Template"],
            "schedule_name":scheduling_data["Presentation Title"],
            "schedule_naming_scheme":scheduling_data["Naming Scheme"],
            "schedule_recorder":scheduling_data["Recorder"],
            "schedule_recurrence":scheduling_data["Recurrence"],
            "schedule_auto_delete":"True" if scheduling_data["Delete Schedule After Occurrences"] == "TRUE" else "False",
            "schedule_start_datetime_utc_string":utc_start_datetime_string,
            "schedule_end_datetime_utc_string":utc_end_datetime_string,
            "schedule_start_datetime_utc":utc_start_datetime,
            "schedule_end_datetime_utc":utc_end_datetime,
            "schedule_start_datetime_local_string":local_start_datetime_string,
            "schedule_end_datetime_local_string":local_end_datetime_string,
            "schedule_start_datetime_local":local_start_datetime,
            "schedule_end_datetime_local":local_end_datetime,
            "schedule_duration":str(duration_in_minutes),
            "schedule_recurrence_freq":scheduling_data["Recurrence Frequency"],
            "schedule_days_of_week":{
                                    "Sunday":True if scheduling_data["Sun"] == "TRUE" else False,
                                    "Monday":True if scheduling_data["Mon"] == "TRUE" else False,
                                    "Tuesday":True if scheduling_data["Tue"] == "TRUE" else False,
                                    "Wednesday":True if scheduling_data["Wed"] == "TRUE" else False,
                                    "Thursday":True if scheduling_data["Thu"] == "TRUE" else False,
                                    "Friday":True if scheduling_data["Fri"] == "TRUE" else False,
                                    "Saturday":True if scheduling_data["Sat"] == "TRUE" else False
                                    }
            }

        return schedule_data_submit

    def delete_schedule(self, schedule_id):
        """
        Deletes mediasite schedule given schedule guid
        
        params:
            presentation_id: guid of a mediasite schedule

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Deleting Mediasite schedule: "+schedule_id)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("delete", "Schedules('"+schedule_id+"')", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def get_schedule(self, schedule_id):
        """
        Deletes mediasite schedule given schedule guid
        
        params:
            presentation_id: guid of a mediasite schedule

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Getting Mediasite schedule: "+schedule_id)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("get", "Schedules('"+schedule_id+"')", "","").json()
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result
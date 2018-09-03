"""
Mediasite client class for recorder-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging

class recorder():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def gather_recorders(self):
        """
        Gathers mediasite recorder name listing from mediasite system

        returns:
            list of mediasite recorder names from mediasite system
        """

        ms_recorders = []

        logging.info("Gathering Mediasite recorders")

        #request mediasite recorder information from mediasite
        result = self.mediasite.api_client.request("get", "Recorders", "$top=100", "")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:       
            #for each recorder in the result of the request append the name to the list
            for recorder in result.json()["value"]:
                ms_recorders.append({"name":recorder["Name"],"id":recorder["Id"]})

            #add the listing of recorder names to the model for later use
            self.mediasite.model.set_recorders(ms_recorders)

            return ms_recorders

    def gather_recorder_status(self, recorder_whitelist=[]):
        """
        Gathers mediasite recorder status listing from mediasite system

        note: can be the following:
            Unknown
            Idle
            Busy
            RecordStart
            Recording
            RecordEnd
            Pausing
            Paused
            Resuming
            OpeningSession
            ConfiguringDevices

        returns:
            list of mediasite recorder status from mediasite system
        """

        result_list = []

        for recorder in self.mediasite.model.get_recorders():
            if recorder["name"] in recorder_whitelist:
                continue

            logging.info("Finding recorder status information for recorder: " + recorder["name"])
            result = self.mediasite.api_client.request("get", "Recorders('"+recorder["id"]+"')/Status", "", "")
            result_json = result.json()
            result_json["Name"] = recorder["name"]
            result_list.append(result_json)

        return result_list

    def gather_recorder_scheduled_recordings(self, recorder_id):
        """
        Gathers scheduled recordings for recorder based on provided recorder guid

        params:
            recorder_id: guid of a mediasite recorder

        returns:
            list of scheduled recordings associated with the recorder
        """

        logging.info("Gathering schedules for recorder: "+recorder_id)

        #make the mediasite request using the post data found above to create the folder
        result = self.mediasite.api_client.request("get", "Recorders('"+recorder_id+"')/ScheduledRecordingTimes", "$top=100", "").json()

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

        

    
    def get_all_scheduled_recordings(self):
        """
        Gathers scheduled recordings for all recorders

        returns:
            dictionary organized by recorder with scheduled recordings
        """

        self.mediasite.recorder.gather_recorders()

        recorders = self.mediasite.model.get_recorders()

        #initialize our return dictionary
        recorder_recordings = []

        #loop for each recorder in recorders listing
        for recorder in recorders:

            #gather scheduled recordings by recorder
            scheduled_recordings = self.mediasite.recorder.gather_recorder_scheduled_recordings(recorder["id"])

            #initialize schedule id, name, and recorder_recordings list
            schedule_id = ""
            schedule_name = ""
            
            #loop for each recording in scheduled_recordings
            for recording in scheduled_recordings["value"]:
                
                #determine if we already have the schedule_id and name, if not, gathering it.
                if schedule_id != recording["ScheduleId"]:
                    schedule_id = recording["ScheduleId"]
                    schedule_result = self.mediasite.schedule.get_schedule(schedule_id)
                    schedule_name = schedule_result["Name"]

                #create dictionary containing the scheduled recording's information
                recording_dict = {"title":schedule_name,
                                    "location":recorder["name"],
                                    "cancelled":recording["IsExcluded"],
                                    "id":schedule_id,
                                    "start":recording["StartTime"] + "Z",
                                    "end":recording["EndTime"] + "Z",
                                    "duration":recording["DurationInMinutes"]
                                    }

                #add the scheduled recording information to list of other recordings for this recorder
                recorder_recordings.append(recording_dict)

        return recorder_recordings

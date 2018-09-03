"""
Mediasite client class for folder-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging
from urllib.parse import quote

class folder():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite
        self.gather_root_folder_id()

    def gather_folders(self, parent_id=""):
        """
        Gathers mediasite child folder name, ID, and parent ID listing from mediasite system
        based on provided parent mediasite folder ID

        params:
            parent_id: mediasite parent folder ID for use as a reference point in this function

        returns:
            list of dictionary items containing child mediasite folder names, ID's, and parent folder ID's
        """

        if parent_id == "":
            parent_id = self.mediasite.model.get_root_parent_folder_id()

        ms_folders = []

        logging.info("Gathering Mediasite folders")

        #request existing (non-recycled) mediasite folder information based on parent folder ID provided to function
        result = self.mediasite.api_client.request("get", "Folders", "$top=100&$filter=ParentFolderId eq '"+parent_id+"' and Recycled eq false","")

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #for each item in the result create a dictionary with name, ID, and parent ID elements for reference
            for folder in result.json()["value"]:
                ms_folders.append({"name":folder["Name"],
                                            "id":folder["Id"],
                                            "parent_id":folder["ParentFolderId"]
                                            })

            #add the listing of folder data to the model for later use
            self.mediasite.model.set_folders(ms_folders, parent_id)

            return ms_folders

    def gather_root_folder_id(self):
        """
        Gathers mediasite root folder ID for use with other functions.

        Note: finding the root folder ID is somewhat of a workaround as normal requests for the "Mediasite" root folder
        do not appear to yield any data. The "Mediasite Users" folder appears as a standard folder on most installations
        and therefore serves as a reference point to determine the root folder. This may need to change in the future based
        on Mediasite version default changes.

        returns:
            the parent ID of the mediasite "Mediasite Users" folder
        """

        logging.info("Gathering Mediasite root folder id")

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("get", "Folders", "$filter=Name eq 'Mediasite Users' and Recycled eq false","")

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #return the parent ID of the mediasite "Mediasite Users" folder
            self.mediasite.model.set_root_parent_folder_id(result.json()["value"][0]["ParentFolderId"])
            return result.json()["value"][0]["ParentFolderId"]

    def create_folder(self, folder_name, parent_id):
        """
        Creates mediasite folder based on provided name and parent folder ID

        params:
            folder_name: name desired for the new mediasite folder
            parent_id: mediasite parent folder ID for use as a reference point in this function

        returns:
            resulting response from the mediasite web api request for folder data
        """

        folder_search_result = self.find_folder_by_name_and_parent_id(folder_name, parent_id)

        if int(folder_search_result["odata.count"]) > 0:
            logging.info("Found existing folder '"+folder_name+"' under parent "+parent_id)
            return folder_search_result["value"][0]

        logging.info("Creating folder '"+folder_name+"' under parent "+parent_id)

        #prepare post data for use in creating the folder
        post_data = {"Name":folder_name,
                    "Description":"",
                    "ParentFolderId":parent_id
                    }

        #make the mediasite request using the post data found above to create the folder
        result = self.mediasite.api_client.request("post", "Folders", "", post_data).json()

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def find_folder_by_name_and_parent_id(self, folder_name, parent_id=""):
        """
        Finds mediasite folder based on provided name and parent folder ID

        params:
            folder_name: name desired for the new mediasite folder
            parent_id: mediasite parent folder ID for use as a reference point in this function

        returns:
            resulting response from the mediasite web api request to find the folder
        """

        logging.info("Searching for folder '"+folder_name+"' under parent "+parent_id)

        if parent_id == "":
            parent_id = self.mediasite.model.get_root_parent_folder_id()

        #make the mediasite request using the post data found above to create the folder
        result = self.mediasite.api_client.request("get", "Folders", "$filter=Name eq '"+folder_name+"' and ParentFolderId eq '"+parent_id+"' and Recycled eq false", "").json()

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def find_recycled_folder_by_name_and_parent_id(self, folder_name, parent_id):
        """
        Finds mediasite folder based on provided name and parent folder ID

        params:
            folder_name: name desired for the new mediasite folder
            parent_id: mediasite parent folder ID for use as a reference point in this function

        returns:
            resulting response from the mediasite web api request to find the folder
        """

        logging.info("Searching for recycled folder '"+folder_name+"' under parent "+parent_id)

        #make the mediasite request using the post data found above to create the folder
        result = self.mediasite.api_client.request("get", "Folders", "$filter=Name eq '"+folder_name+"' and ParentFolderId eq '"+parent_id+"'and Recycled eq true", "").json()

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def get_presentations_and_schedules_by_parent_folder_name(self, folder_name):
        """
        Gathers schedules and presentations found under one parent folder, searching each child folder underneath
        
        params:
            folder_name: name of the mediasite folder

        returns:
            details of schedules and presentations found within mediasite folder
        """

        folder = mediasite.folder.get_folder_by_name(folder_name)

        if int(folder.json()["odata.count"]) > 0:
            parent_id = folder.json()["value"][0]["Id"]

            child_folders = mediasite.folder.get_child_folders(parent_id)
            child_folders.append(folder.json()["value"][0])

            presentations = []
            schedules = []

            for folder in child_folders:
                presentations_result = mediasite.folder.get_folder_presentations(folder["Id"])
                [presentations.append(presentation) for presentation in presentations_result.json()["value"]]
                schedules_result = mediasite.folder.get_folder_schedules(folder["Id"])
                print(schedules_result.json())
                [schedules.append(schedule) for schedule in schedules_result.json()["value"]]

        return presentations, schedules

    def get_folder_schedules(self, parent_id):
        """
        Gathers schedules found under mediasite folder given folder's id
        
        params:
            parent_id: id of mediasite folder

        returns:
            details of schedules found within mediasite folder

        Note: this makes use of the "schedules" Mediasite API calls as no related "folders" call exists at this time.
        """

        logging.info("Finding Mediasite presentatations under parent: "+parent_id)

        result = self.mediasite.api_client.request("get", "Schedules", "$top=100&$filter=FolderId eq '"+parent_id+"'","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result

    def get_folder_presentations(self, parent_id):
        """
        Gathers presentations found under mediasite folder given folder's id
        
        params:
            parent_id: id of mediasite folder

        returns:
            details of presentations found within mediasite folder
        """

        logging.info("Finding Mediasite presentatations under parent: "+parent_id)

        result = self.mediasite.api_client.request("get", "Folders('"+parent_id+"')/Presentations", "$top=100","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:

            return result

    def get_folder_catalogs(self, parent_id):
        """
        Gathers presentations found under mediasite folder given folder's id
        
        params:
            parent_id: id of mediasite folder

        returns:
            details of presentations found within mediasite folder
        """

        logging.info("Finding Mediasite catalogs under parent: "+parent_id)

        result = self.mediasite.api_client.request("get", "Catalogs", "$top=600&$filter=LinkedFolderId eq '"+parent_id+"'","")
        result_json = result.json()
        result_list = []
        for catalog in result_json["value"]:
            if catalog["LinkedFolderId"] == parent_id:
                result_list.append(catalog)

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result_list

    def get_child_folders(self, parent_id, child_result=[]):
        """
        Gathers mediasite child folders given parent id of a folder
        
        params:
            parent_id: id of mediasite folder

        returns:
            list of child folder id's associated with the given parent folder id
        """

        logging.info("Finding child Mediasite folders under parent: "+parent_id)
  
        result = self.mediasite.api_client.request("get", "Folders", "$top=100&$filter=ParentFolderId eq '"+parent_id+"' and Recycled eq false","")
        
        if self.mediasite.experienced_request_errors(result) or int(result.json()["odata.count"]) <= 0:
            return result
        else:
            for folder in result.json()["value"]:
                child_result.append(folder)
                self.get_child_folders(folder["Id"], child_result)

            return child_result

    def get_folder_by_name(self, folder_name):
        """
        Gathers folder information given folder name within mediasite
        
        params:
            folder_name: name of folder which is to be found by name

        returns:
            the parent ID of the mediasite "Mediasite Users" folder
        """

        logging.info("Finding Mediasite folder information with name of: "+folder_name)

        result = self.mediasite.api_client.request("get", "Folders", "$filter=Name eq '"+folder_name+"' and Recycled eq false","").json()
        
        if self.mediasite.experienced_request_errors(result):
            return result

        else:
            return result

    def parse_and_create_folders(self, folders, parent_id=""):
        """
        Parse the provided path of folders in the GUI, delimeted by "/" and create each
        under the selected existing root folder within mediasite.

        params:
            folders: string containing multiple folders split by "/"
            parent_id: mediasite parent folder ID for use as a reference point in this function

        returns:
            final mediasite folder id (lowest level folder)
        """
        if parent_id == "":
            parent_id = self.mediasite.model.get_root_parent_folder_id()

        folders_list = folders.split("/")

        #loop through our folders list creating each folder using the parent of the last
        for folder in folders_list:
            if folder != "":
                result = self.create_folder(folder, parent_id)
                if "Id" in result:
                    parent_id = result["Id"]
                else:
                    break

        return parent_id

    def delete_folder(self, folder_id):
        """
        Deletes folder based on folder guid id provided as argument
        
        params:
            folder_id: guid of folder to delete

        returns:
            response from mediasite system
        """

        logging.info("Deleting mediasite folder with guid of: "+folder_id)

        result = self.mediasite.api_client.request("post", "Folders('"+folder_id+"')/DeleteFolder", "",{})
        
        if self.mediasite.experienced_request_errors(result):
            return result

        else:
            return result

    def delete_folder_by_path(self, folder_path):
        """
        Deletes parent folder including potentially many child folder or sub-elements
        
        params:
            folder_path: mediasite management portal folder path, for ex "/Current/Spring 2018/Test"

        returns:
            response from mediasite system
        """

        parent_id = ""

        #for each folder found in provided path, find it by name and parent folder guid

        for folder_name in folder_path.split("/")[1:]:
            result = self.mediasite.folder.find_folder_by_name_and_parent_id(folder_name, parent_id)
            if int(result["odata.count"]) > 0:
                for item in result["value"]:
                    if item["Name"] == folder_name:
                        parent_id = item["Id"]
            else:
                #if we don't find one of the folders in the provided path, return to stop this function from continuing
                logging.error("Unable to find folder in provided path: "+folder_name)
                return
        
        #remove "recorded" presentations and schedules as these can prevent folders from being deleted
        child_folders = self.mediasite.folder.get_child_folders(parent_id)
        child_folders.append({"Id":parent_id})

        #gather catalogs as these will be needed later
        self.mediasite.catalog.get_all_catalogs()
        catalogs = self.mediasite.model.get_catalogs()

        for folder in child_folders:
            folder_presentations = self.mediasite.folder.get_folder_presentations(folder["Id"])

            #presentation loop to remove presentations with a status of "Recorded" or "Record"
            folder_presentations_json = folder_presentations.json()
            if int(folder_presentations_json["odata.count"]) > 0:
                for presentation in folder_presentations_json["value"]:
                    print(presentation["Status"])
                    #if presentation["Status"] == "Recorded" or presentation["Status"] == "Record":
                    logging.info("Deleting presentation "+presentation["Title"]+" to ensure capability to delete parent folder(s).")
                    delete_result = self.mediasite.presentation.delete_presentation(presentation["Id"])
            
            #schedule loop to remove schedules
            folder_schedules = self.mediasite.folder.get_folder_schedules(folder["Id"])
            folder_schedules_json = folder_schedules.json()
            if int(folder_schedules_json["odata.count"]) > 0:
                for schedule in folder_schedules_json["value"]:
                    logging.info("Deleting schedule "+ schedule["Name"]+" to ensure capability to delete parent folder(s).")
                    delete_result = self.mediasite.schedule.delete_schedule(schedule["Id"])

            for catalog in catalogs:
                if catalog["LinkedFolderId"] == folder["Id"]:
                    logging.info("Deleting catalog "+catalog["Id"]+" to ensure capability to delete parent folder(s).")
                    self.mediasite.catalog.delete_catalog(catalog["Id"])

            result = self.mediasite.folder.delete_folder(folder["Id"])
            job_result = self.mediasite.wait_for_job_to_complete(result.json()["odata.id"])
        

        result = self.mediasite.folder.delete_folder(parent_id)

        job_result = self.mediasite.wait_for_job_to_complete(result.json()["odata.id"])

        #note: this appears to be the only way with these particular jobs to determine a successful run (despite actual message contents)
        if job_result:
            if job_result["odata.error"]["message"]["value"] == "The job completion state is missing.":
                logging.info("Successfully deleted folder(s) and related items. Note: folder and some items will remain in recycling bin until further action is taken.")


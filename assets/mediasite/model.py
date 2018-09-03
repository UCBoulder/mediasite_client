"""
Mediasite model for medaisite scheduler. Stores various data gathered
from Mediasite API using mediasite_web_api client.

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import os
import sys
import logging

class model():
    def __init__(self):
        self.current_connection_valid = False
        self.root_parent_folder_id = ""
        self.templates = {}
        self.recorders = {}
        self.schedules = {}
        self.recurrences = {}
        self.folders = {}
        self.catalogs = []

    def translate_recorder_id(self, recorder_name):
        """
        Finds Mediasite recorder ID using provided recorder name

        params:
            recorder_name: Mediasite recorder name which you would like to find the ID for.

        returns:
            resulting response from the mediasite web api request
        """
        for recorder in self.recorders:
            if recorder_name == recorder["name"]:
                return recorder["id"]

        return ""

    def translate_template_id(self, template_name):

        for template in self.templates:
            if template_name == template["Name"]:
                return template["Id"]

        return ""

    def translate_schedule_recurrence_naming(self, recurrence_label):
        translate_recurrence_dict = {
            "":"None",
            "Record Date":"ScheduleNameAndAirDateTime",
            "Incremental Number":"ScheduleNameAndNumber"
        }

        if recurrence_label not in translate_recurrence_dict:
            recurrence_label = ""

        return translate_recurrence_dict[recurrence_label]

    def translate_schedule_recurrence_pattern(self, recurrence_pattern):
        translate_recurrence_type_dict = {
            "Weekly":"Weekly",
            "One Time Only":"None"
        }

        return translate_recurrence_type_dict[recurrence_pattern]

    def add_recurrence(self, recurrence):
        self.recurrences[recurrence["Id"]] = recurrence

    def add_schedule(self, schedule):
        self.schedules[schedule["Id"]] = schedule

    def get_schedule(self, schedule):
        return self.schedules

    def set_templates(self, templates):
        self.templates = templates

    def get_templates(self):
        return self.templates

    def set_recorders(self, recorders):
        self.recorders = recorders

    def get_recorders(self):
        return self.recorders

    def set_folders(self, folders, parent_id="root"):
        self.folders[parent_id] = folders

    def get_folders(self):
        return self.folders

    def get_current_connection_valid(self):
        return self.current_connection_valid

    def set_current_connection_valid(self, state):
        self.current_connection_valid = state

    def get_root_parent_folder_id(self):
        return self.root_parent_folder_id

    def set_root_parent_folder_id(self, root_parent_folder_id):
        self.root_parent_folder_id = root_parent_folder_id

    def get_catalogs(self):
        return self.catalogs

    def set_catalogs(self, catalogs):
        self.catalogs = catalogs
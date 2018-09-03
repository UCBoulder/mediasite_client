"""
Mediasite client class for report-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging
import os
import json
import time
import datetime
import sys
import urllib.request
import requests
import pandas as pd
from xml.sax import parse
from assets.misc.ExcelHandler import ExcelHandler
from xml.etree.cElementTree import iterparse

class report():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def find_presentation_report_id_by_name(self, presentation_report_name):
        """
        find a presentation report id by name

        params:
            presentation_report_name: name of the presentation report

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Finding ID of presentation report")
        presentation_report_result = self.mediasite.api_client.request("get", "PresentationReports", "$top=1&$filter=Name eq '"+presentation_report_name+"'", "").json()
        presentation_report_id = presentation_report_result["value"][0]["Id"]

        return presentation_report_id

    def find_storage_report_id_by_name(self, storage_report_name):
        """
        find a content storage report id by name

        params:
            presentation_report_name: name of the presentation report

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Finding ID of storage report")
        storage_report_result = self.mediasite.api_client.request("get", "ContentStorageReports", "$top=1&$filter=Name eq '"+storage_report_name+"'", "").json()
        storage_report_id = storage_report_result["value"][0]["Id"]

        return storage_report_id

    def execute_presentation_report(self, presentation_report_id):
        """
        executes (initiates) mediasite presentation report by it's mediasite id

        params:
            presentation_report_id: id of the mediasite presentation report

        returns:
            resulting response from the mediasite web api request

        Note: waits for job to complete before returning
        """

        logging.info("Executing presentation report")
        presentation_report_execute_json = self.mediasite.api_client.request("post","PresentationReports('"+presentation_report_id+"')/Execute", "", {}).json()

        #wait for the report to be generated
        self.mediasite.wait_for_job_to_complete(presentation_report_execute_json["JobLink"])

        return presentation_report_execute_json

    def execute_storage_report(self, storage_report_id):
        """
        executes (initiates) mediasite presentation report by it's mediasite id

        params:
            presentation_report_id: id of the mediasite presentation report

        returns:
            resulting response from the mediasite web api request

        Note: waits for job to complete before returning
        """

        logging.info("Executing storage report")
        storage_report_execute_json = self.mediasite.api_client.request("post","ContentStorageReports('"+storage_report_id+"')/Execute", "", {}).json()

        #wait for the report to be generated
        self.mediasite.wait_for_job_to_complete(storage_report_execute_json["JobLink"])
        return storage_report_execute_json

    def download_presentation_report_from_id(self, presentation_report_id, presentation_report_result_id, download_type, download_filename):
        """
        Function for downloading Mediasite presentation reports using Mediasite API.

        params:
            presentation_report_id: Mediasite GUID for relevant report
            presentation_report_result_id: Mediasite GUID for relevant report result (data)
            download_type: type of file to request, for ex. "Excel" or "XML"
            download_filename: name of the resulting downloaded report data file

        Note: waits for the job to complete before returning 
        """

        #make request for report file to be generated
        presentation_report_execute_export_json = self.mediasite.api_client.request("post", "PresentationReports('"+presentation_report_id+"')/Export", "", {"ResultId":presentation_report_result_id,"FileFormat":download_type}).json()

        #wait for the job to finish
        self.mediasite.wait_for_job_to_complete(presentation_report_execute_export_json["JobLink"])
        logging.info("Attempting to download report from url: "+presentation_report_execute_export_json["DownloadLink"])

        #download the file as a stream
        with open(download_filename, 'wb') as handle:
            presentation_report_job_rsp = self.mediasite.api_client.request("get stream",presentation_report_execute_export_json["DownloadLink"],"","")
            for block in presentation_report_job_rsp.iter_content(1024):
                handle.write(block)

        logging.info("Successfully downloaded "+download_filename)

    def download_storage_report_from_id(self, storage_report_id, storage_report_result_id, download_type, download_filename):
        """
        Currently not functioning. This appears to be an unexposed portion of Mediasite's API

        Function for downloading Mediasite storage reports using Mediasite API.

        params:
            storage_report_id: Mediasite GUID for relevant report
            storage_report_result_id: Mediasite GUID for relevant report result (data)
            download_type: type of file to request, for ex. "Excel" or "XML"
            download_filename: name of the resulting downloaded report data file

        Note: Relies on Management portal link as the "Export" function for Content Storage Reports 
        appears to be an unexposed portion of the Mediasite API
        """
        
        #workaround using the management portal to download storage report
        
        with requests.Session() as s:
            if download_type == "Excel":
                report_route_link = "Manage/ContentStorageExport.aspx/ResultExcel?reportId=undefined&resultid="
            else:
                report_route_link = "Manage/ContentStorageExport.aspx/ResultXML?reportId=undefined&resultid="

            download_url = self.mediasite.config_data["base_url"].replace("Api/v1/","")+\
                "Manage/ContentStorageExport.aspx/ResultExcel?reportId=undefined&resultid="+\
                storage_report_result_id

            login_url = "https://cu-classcapture.colorado.edu/Mediasite/Login"
            user, password = self.mediasite.config_data["api_user"], self.mediasite.config_data["api_pass"]
            data = {"UserName":user,
                    "Password":password,
                    "RememberMe":"false"
                    }
            #log in        
            s.post(login_url, data=data)

            r = s.get(download_url, stream=True)
            with open(download_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        f.write(chunk)

        logging.info("Successfully downloaded "+download_filename)    

    def parse_presentation_summary_data_from_xml(self, filepath):
        """
        Function for parsing xml summary data from a downloaded presentation report

        params:
            filepath: filepath to the presentation report xml

        returns:
            dictionary containing data from the presentation report summary data
        """

        
        #dictionary containing tags from xml we're interested in gathering
        xml_mapping = {
            "PresentationsAvailable":"",
            "TotalTimeWatched":"", 
            "PresentationsWatched":"",
            "TotalViews":"",
            "TotalUsers":"",
            "PeakConnections":""
        }
        
        #parse through xml file using iterparse, break once the xml_mapping dictionary is filled in
        for event, elem in iterparse(filepath):
            if elem.tag in xml_mapping:
                xml_mapping[elem.tag] = elem.text
                elem.clear()
            
            if "" not in xml_mapping.values():
                break

        return xml_mapping

    def load_presentation_report_summary_sheet(self, filepath):
        """
        Function for parsing excel xml summary data from a downloaded presentation report

        params:
            filepath: filepath to the presentation report excel xml

        returns:
            pandas dataframe containing data from the presentation report summary
        """

        #build and use parser
        excelHandler = ExcelHandler()
        parse(filepath, excelHandler)

        #gather data from first sheet of excel xml report
        summary_df = pd.DataFrame(excelHandler.tables[0])

        #transpose (col names are row values for this sheet) and set column names using first row
        summary_df = summary_df.T
        summary_df.columns = summary_df.iloc[0]
        summary_df.drop(summary_df.index[0], inplace=True)

        #translate final two columns into values and rename the columns to relevant variable names
        summary_df.ix[1, summary_df.columns[len(summary_df.columns)-1]] = summary_df.columns[len(summary_df.columns)-1]
        summary_df.ix[1, summary_df.columns[len(summary_df.columns)-2]] = summary_df.columns[len(summary_df.columns)-2]
        summary_df.rename(columns={ summary_df.columns[len(summary_df.columns)-1]: "Timezone",
                            summary_df.columns[len(summary_df.columns)-2]: "Report Date"}, 
                    inplace=True)

        #cleanup
        summary_df.dropna(axis=1, inplace=True)
        summary_df.rename(columns = lambda x : str(x).replace(":",""), inplace=True)

        summary_df.reset_index(drop=True, inplace=True)

        return summary_df

    def load_presentation_report_presentation_sheet(self, filepath):
        """
        Function for parsing excel xml presentation data from a downloaded presentation report

        params:
            filepath: filepath to the presentation report excel xml

        returns:
            pandas dataframe containing data from the presentation report presentations
        """

        #build and use parser
        excelHandler = ExcelHandler()
        parse(filepath, excelHandler)

        #gather data from fourth sheet of excel xml report
        presentation_df = pd.DataFrame(excelHandler.tables[3][1:], columns=excelHandler.tables[3][0])
        presentation_df['Air Date'] =  pd.to_datetime(presentation_df['Air Date'], format='%Y-%m-%d %H:%M:%S')

        presentation_df.reset_index(drop=True, inplace=True)

        return presentation_df

    def parse_new_presentation_count(self, filepath):
        """
        Function for for determining the number of new presentations for a given presentation report

        params:
            filepath: filepath to the presentation report excel xml

        returns:
            number of new presentations found by the function
        """

        summary_df = self.load_presentation_report_summary_sheet(filepath)
        presentation_df = self.load_presentation_report_presentation_sheet(filepath)

        #parse the start date of report from the Range col in the summary date
        date_range_start = summary_df["Range"][0].split(": ")[1].split(" to ")[0]

        #filter presentation_df by Air Dates later than the start range, return shape rows
        return presentation_df[presentation_df["Air Date"] > date_range_start].shape[0]


    def gather_presentation_report_export(self, report_type, recurrence, report_prefix, export_destination, presentation_report_name):
        """
        Gathers export via exectution and download of the report

        params:
            report_type: type of report being gathered - excel or xml
            recurrence: recurrence timeframe, for titling of files
            report_prefix: prefix to indicate differences between types
            export_destination: filepath for the downloaded reports
            presentation_report_name: name of the mediasite presentation report

        returns:
            filename of the report which was generated
        """

        file_extension = ".excel.xml" if report_type == "excel" else ".xml"
        mediasite_request_type = "Excel" if report_type == "excel" else "XML"

        presentation_report_id = self.find_presentation_report_id_by_name(presentation_report_name)

        #gather report execute data
        presentation_report_execute_json = self.execute_presentation_report(presentation_report_id)

        #gather date strings for request
        current_date_file_string = time.strftime("%m-%d-%Y")

        #filenames and locations for the excel and xml files
        filename = export_destination.rstrip('/')+"/mediasite_report_"+\
            recurrence+"_"+report_prefix+'_'+current_date_file_string+file_extension

        #download excel (xml) version of data
        logging.info("Beginning Excel XML file generation for report")
        
        self.download_presentation_report_from_id(presentation_report_id, presentation_report_execute_json["ResultId"], mediasite_request_type, filename)

        return filename


    def gather_storage_report_export(self, report_type, recurrence, report_prefix, export_destination, storage_report_name):
        """
        Gathers export via exectution and download of the report

        params:
            report_type: type of report being gathered - excel or xml
            recurrence: recurrence timeframe, for titling of files
            report_prefix: prefix to indicate differences between types
            export_destination: filepath for the downloaded reports
            storage_report_name: name of the mediasite presentation report

        returns:
            filename of the report which was generated
        """

        file_extension = ".excel.xml" if report_type == "excel" else ".xml"
        mediasite_request_type = "Excel" if report_type == "excel" else "XML"

        storage_report_id = self.find_storage_report_id_by_name(storage_report_name)

        #gather report execute data
        storage_report_execute_json = self.execute_storage_report(storage_report_id)

        #gather date strings for request
        current_date_file_string = time.strftime("%m-%d-%Y")

        #filenames and locations for the excel and xml files
        filename = export_destination.rstrip('/')+"/mediasite_report_"+\
            recurrence+"_"+report_prefix+'_'+current_date_file_string+file_extension

        #download excel (xml) version of data
        logging.info("Beginning Excel XML file generation for report")
        
        self.download_storage_report_from_id(storage_report_id, storage_report_execute_json["ResultId"], mediasite_request_type, filename)

        return filename    

    def gather_all_presentation_report_exports(self, recurrence, report_prefix, export_destination, presentation_report_name):
        """
        Gathers all export via exectution and download of the report (xml and excel.xml)

        params:
            recurrence: recurrence timeframe, for titling of files
            report_prefix: prefix to indicate differences between types
            export_destination: filepath for the downloaded reports
            presentation_report_name: name of the mediasite presentation report

        returns:
            filenames of the reports which were generated, xml and excel.xml
        """

        xml_filename = self.gather_presentation_report_export("xml", recurrence, report_prefix, export_destination, presentation_report_name)
        excel_filename = self.gather_presentation_report_export("excel", recurrence, report_prefix, export_destination, presentation_report_name)

        return xml_filename, excel_filename

    def gather_presentaton_report_summary_data(self, recurrence, report_prefix, export_destination, presentation_report_name):
        """
        Gathers presentation reports to find summary data

        params:
            recurrence: the period of the report, for ex. "weekly", "monthly"
            report_prefix: the prefix to use for the report, for ex. "bba", "dls"
            export_destination: local directory location for downloaded report files
            presentation_report_name: presentation report name within Mediasite

        returns:
            mediasite_results: dict with various summary data extracted from the Mediasite API
        """

        xml_filename, excel_filename = self.gather_presentation_report_exports(recurrence, report_prefix, export_destination, presentation_report_name)

        #parse necessary data from xml file
        logging.info("Reading XML data from report")
        
        xml_mapping = self.parse_presentation_summary_data_from_xml(xml_filename)

         #initialize our final results dictionary
        mediasite_results = {"mediasite_results_total_time_watched":"",
            "mediasite_results_time_watched_hours":"",
            "mediasite_results_time_watched_miuntes":"",
            "mediasite_results_time_watched_seconds":"",
            "mediasite_results_number_presentations":"",
            "mediasite_results_watched_presentations":"",
            "mediasite_results_presentation_views":"",
            "mediasite_results_active_users":"",
            "mediasite_results_active_users_peak":"",
            "mediasite_results_excel_filepath":"",
            "mediasite_results_xml_filepath":"",
            "mediasite_results_email_content":""
            }

        #add xml data to results dictionary
        mediasite_results["mediasite_results_number_presentations"] = xml_mapping["PresentationsAvailable"]
        mediasite_results["mediasite_results_total_time_watched"] = xml_mapping["TotalTimeWatched"] 
        mediasite_results["mediasite_results_watched_presentations"] = xml_mapping["PresentationsWatched"]
        mediasite_results["mediasite_results_presentation_views"] = xml_mapping["TotalViews"]
        mediasite_results["mediasite_results_active_users"] = xml_mapping["TotalUsers"]
        mediasite_results["mediasite_results_active_users_peak"] = xml_mapping["PeakConnections"]
        
        #organize our time for display
        #NOTE: hours are in days by default in xml file (not the case in excel xml file)
        #ex: <TotalTimeWatched>05:44:37</TotalTimeWatched>
        total_mediasite_time_watched_split = mediasite_results["mediasite_results_total_time_watched"].split(":")
        mediasite_results["mediasite_results_time_watched_minutes"] = total_mediasite_time_watched_split[1]
        mediasite_results["mediasite_results_time_watched_seconds"] = total_mediasite_time_watched_split[2]

        #hours cleanup (see above comment)
        #checking for decimal in days format first for special calculation
        if "." in total_mediasite_time_watched_split[0]:
            total_mediasite_time_watched_hours_split = total_mediasite_time_watched_split[0].split(".")
            mediasite_results["mediasite_results_time_watched_hours"] = str((int(total_mediasite_time_watched_hours_split[0])*24)+int(total_mediasite_time_watched_hours_split[1]))
        else:
            mediasite_results["mediasite_results_time_watched_hours"] = str((int(total_mediasite_time_watched_split[0])*24))

        mediasite_results["mediasite_results_excel_filepath"] = excel_filename
        mediasite_results["mediasite_results_xml_filepath"] = xml_filename

        #create strings for the email
        logging.info("Finished gathering Mediasite data, generating email content")

        return mediasite_results

    def create_presentation_report_by_folder(self, report_name, folder_id):
        """
        Create a Mediasite presentation report to analyze presentations in given folder by id

        params:
            report_name: name of presentation report
            folder_id: Mediasite guid of the folder which will be associated with presentation report

        returns:
            result from mediasite api request to create presentation report
        """       

        logging.info("Creating presentation report "+report_name+" for folder "+folder_id)

        post_data = {"Name":report_name,
                    "FolderIdList":[folder_id],
                    "IncludeItemsWithZeroViews":True,
                    "IncludeSubFolders":True
                    }

        #make the mediasite request using the post data found above to create the folder
        result = self.mediasite.api_client.request("post", "PresentationReports", "", post_data).json()

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

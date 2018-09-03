"""
Mediasite client class for presentation-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging
from urllib.parse import quote

class presentation():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def get_presentations_by_name(self, name_search_query):
        """
        Gathers mediasite root folder ID for use with other functions.
        
        params:
            template_name: name of the template to be found within mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Searching for presentations containing the text: "+name_search_query)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("get", "Search", "search='"+name_search_query+"'&searchtype=Presentation","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def delete_presentation(self, presentation_id):
        """
        Deletes mediasite presentation given presentation guid
        
        params:
            presentation_id: guid of a mediasite presentation

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Deleting Mediasite presentation: "+presentation_id)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("delete", "Presentations('"+presentation_id+"')", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def remove_publish_to_go(self, presentation_id):
        """
        Gathers mediasite root folder ID for use with other functions.
        
        params:
            template_name: name of the template to be found within mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Removing publish to go from presentation: "+presentation_id)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("post", "Presentations('"+presentation_id+"')/RemovePublishToGo", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def remove_podcast(self, presentation_id):
        """
        Gathers mediasite root folder ID for use with other functions.
        
        params:
            template_name: name of the template to be found within mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Finding Mediasite template information with name of: "+template_name)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("post", "Presentations('"+presentation_id+"')/RemovePodcast", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def remove_video_podcast(self, presentation_id):
        """
        Gathers mediasite root folder ID for use with other functions.
        
        params:
            template_name: name of the template to be found within mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Finding Mediasite template information with name of: "+template_name)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("post", "Presentations('"+presentation_id+"')/RemoveVideoPodcast", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result
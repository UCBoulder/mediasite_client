"""
Mediasite client class for template-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging
from urllib.parse import quote

class template():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def gather_templates(self):
        """
        Gathers mediasite template name listing from mediasite system

        returns:
            list of mediasite template names from mediasite system
        """

        mediasite_templates = []

        logging.info("Gathering Mediasite templates")

        #request mediasite template information from mediasite
        result = self.mediasite.api_client.request("get", "Templates", "$top=200", "")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #for each template in the result of the request append the name to the list
            for template in result.json()["value"]:
                mediasite_templates.append(template)
            
            #add the listing of template names to the model for later use
            self.mediasite.model.set_templates(mediasite_templates)
            return mediasite_templates

    def find_template_by_name(self, template_name):
        """
        Gathers mediasite root folder ID for use with other functions.
        
        params:
            template_name: name of the template to be found within mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Finding Mediasite template information with name of: "+template_name)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("get", "Templates", "$filter=Name eq '"+quote(template_name)+"'","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result
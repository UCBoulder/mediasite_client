"""
Mediasite client class for module-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging

class module():
    def __init__(self, controller, *args, **kwargs):
    	self.controller = controller

    def create_module(self, module_name, module_id):
        """
        Creates mediasite module using provided module name and module id

        params:
            module_name: name which will appear for the module
            module_id: moduleid associated with module in mediasite

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Creating module '"+module_name+"' with module id "+module_id)
    
        post_data = {"Name":module_name,
                    "ModuleId":module_id
                    }

        result = self.controller.api_client.do_request("post", "Modules", "", post_data).json()

        if self.controller.experienced_request_errors(result):
            return result
        else:
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def module_moduleid_already_exists(self, module_id):
        """
        Determine whether the provided moduleid already exists

        params:
            module_id: moduleid associated with module in mediasite

        returns:
            true if it already exists, false if it does not
        """
        result = self.controller.api_client.do_request("get", "Modules", "$filter=ModuleId eq '"+module_id+"'", "").json()

        if self.controller.experienced_request_errors(result):
            return result
        else:
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            if int(result["odata.count"]) > 0:
                logging.error("Found more than one occurrence of ModuleId "+module_id)
                return True
            else:
                logging.info("Verified moduleId "+module_id+" does not already exist.")
                return False

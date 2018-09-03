"""
Mediasite client class for catalog-sepcific actions

Last modified: May 2018
By: Dave Bunten

License: MIT - see license.txt
"""

import logging

class catalog():
    def __init__(self, mediasite, *args, **kwargs):
        self.mediasite = mediasite

    def delete_catalog(self, catalog_id):
        """
        Deletes mediasite schedule given schedule guid
        
        params:
            presentation_id: guid of a mediasite schedule

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Deleting Mediasite catalog: "+catalog_id)

        #request mediasite folder information on the "Mediasite Users" folder
        result = self.mediasite.api_client.request("delete", "Catalogs('"+catalog_id+"')", "","")
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            #if there is an error, log it
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    def get_all_catalogs(self):
        """
        Gathers presentations found under mediasite folder given folder's id
        
        params:
            parent_id: id of mediasite folder

        returns:
            details of presentations found within mediasite folder
        """

        logging.info("Gathering all catalogs.")

        result = self.mediasite.api_client.request("get", "Catalogs", "$top=800","")
        result_json = result.json()
        self.mediasite.model.set_catalogs(result_json["value"])

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result_json

    def enable_catalog_downloads(self, catalog_id):
        """
        Enables mediasite catalog downloads using provided catalog ID

        Note: only returns a 204 http code on success

        params:
            catalog_id: mediasite catalog ID to enable downloads on

        returns:
            resulting response from the mediasite web api request to enable downloads on the folder
        """

        logging.info("Enabling catalog downloads for catalog: '"+catalog_id)

        #prepare patch data to be sent to mediasite
        patch_data = {"AllowPresentationDownload":"True"}

        #make the mediasite request using the catalog id and the patch data found above to enable downloads
        result = self.mediasite.api_client.request("patch", "Catalogs('"+catalog_id+"')/Settings", "", patch_data)
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result

    def disable_catalog_allow_links(self, catalog_id):
        """
        Disables mediasite catalog links using provided catalog ID

        Note: only returns a 204 http code on success

        params:
            catalog_id: mediasite catalog ID to disable links on

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Disabling catalog links for catalog: '"+catalog_id)

        #prepare patch data to be sent to mediasite
        patch_data = {"AllowCatalogLinks":"False"}

        #make the mediasite request using the catalog id and the patch data found above to enable downloads
        result = self.mediasite.api_client.request("patch", "Catalogs('"+catalog_id+"')/Settings", "", patch_data)
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result

    def add_module_to_catalog(self, catalog_id, module_guid):
        """
        Add mediasite module to catalog by catalog id and module guid

        params:
            catalog_id: mediasite catalog id which will have the module added
            module_guid: mediasite module GUID (not to be confused with a module ID)

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Associating catalog: "+catalog_id+" to module: "+module_guid)

        #prepare patch data to be sent to mediasite
        post_data = {"MediasiteId":catalog_id}

        #make the mediasite request using the catalog id and the patch data found above to enable downloads
        result = self.mediasite.api_client.request("post", "Modules('"+module_guid+"')/AddAssociation", "", post_data)

        if self.mediasite.experienced_request_errors(result):
            return result
        else:
            return result

    def create_catalog(self, catalog_name, description, parent_id):
        """
        Creates mediasite catalog using provided catalog name, description, and parent folder id

        params:
            catalog_name: name which will appear for the catalog
            description: description which will appear for the catalog (beneath name)
            folder_id: mediasite folder ID associated with the catalog

        returns:
            resulting response from the mediasite web api request
        """

        logging.info("Creating catalog '"+catalog_name+"' under parent folder "+parent_id)
    
        post_data = {"Name":catalog_name,
                    "Description":description,
                    "LinkedFolderId":parent_id
                    }

        result = self.mediasite.api_client.request("post", "Catalogs", "", post_data).json()
        
        if self.mediasite.experienced_request_errors(result):
            return result
        else:        
            if "odata.error" in result:
                logging.error(result["odata.error"]["code"]+": "+result["odata.error"]["message"]["value"])

            return result

    
"""
    This is the Home Server Services file.
    Here are specified the class representing each service on the server
    and also the CoAP resource that represents the endpoint (URI)
    where the Home Server Services can be viewed and/or updated.
"""
import json
import logging

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import status, error, check_on_body, AppError, AppHTTPError

import settings

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)

class Service(object):
    """
        This is the Service class.
        Each object of this class represents a Service that
        can be setted/used by the devices connected to this Home Server.
    """
    def __init__(self, service_id, name, core_service_ref=None):
        self.id = service_id
        self.name = name

        if core_service_ref == None:
            self.core_service_ref = core_service_ref
        else:
            try:
                aux = int(core_service_ref)
                self.core_service_ref = aux
            except:
                self.core_service_ref = None

    def get_info(self):
        """
            This method returns a dictionary with all the information
            correspondent to a given Service.
        """
        return {"id": self.id, "name": self.name, "core_service_ref":self.core_service_ref}


class HomeServerServices(Resource):
    """
        This is the Home Server Services CoAP resource.
        It represents the endpoint (URI) where all the home server
        services are stored and can be fetched and/or updated.
    """
    def __init__(self, server):

        super(HomeServerServices, self).__init__("HomeServerServices", server, visible=True,
                                             observable=True, allow_children=False)

        self.server = server
        self.root_uri = "/services"

        self.services = {}
        self.load_services_from_file()

        self.server.add_resource(self.root_uri, self)

        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "HomeServerServices"
        self.interface_type = "if1"

    def get_info(self):
        """
            This method returns a dictionary with all the services
            represented by this CoAP resource
        """
        return self.get_all_services()

    def get_json(self):
        """
            This method returns a JSON representation with all the
            services represented by this CoAP resource.
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with all the services represented by this CoAP resource.
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def load_services_from_file(self):
        """
            This is an auxiliary method that loads to the resource (memory) all
            the Services from their correspondent configuration
            file, pointed by 'settings.SERVICES_CONFIG_FILE'.
        """
        try:
            fp = open(str(settings.SERVICES_CONFIG_FILE), "r")

            data = json.load(fp)
            logger.info("Loading "+str(settings.SERVICES_CONFIG_FILE)+" file...")

            for ele in data["SERVICES"]:
                id = ele["id"]
                name = ele["name"]
                core_service_ref = ele["core_service_ref"]
                self.services[int(id)] = Service(id, name, core_service_ref)

            fp.close()
        except:
            logger.info("FILE: "+str(settings.SERVICES_CONFIG_FILE)+" not found")

    def save_services_to_file(self):
        """
            This is an auxiliary method that saves to the correspondent configuration
            file, pointed by 'settings.SERVICES_CONFIG_FILE', all
            the Services represented by this resource.
        """
        try:
            fp = open(str(settings.SERVICES_CONFIG_FILE), "w")

            data = self.get_all_services()

            logger.info("Saving "+str(settings.SERVICES_CONFIG_FILE)+" file...")
            json.dump(data, fp)
            fp.close()

            logger.info(str(settings.SERVICES_CONFIG_FILE)+" file changes saved.")
        except:
            logger.info("FILE: "+str(settings.SERVICES_CONFIG_FILE)+" not found")

    def validate_services(self, service_ids):
        """
            This method checks if a given Service is valid to be used
            on this Home Server
        """
        for s in service_ids:
            try:
                if not self.services[int(s)]:
                    return False
            except:
                return False
        return True

    def get_all_services(self):
        """
            This method returns a dictionary with all the services
            represented by this CoAP resource
        """
        data = {"SERVICES":[]}
        for s in self.services.itervalues():
            data["SERVICES"].append(s.get_info())
        return data

    def update_server_services(self, new_services):
        """
            This method adds new and/or updates the services represented
            by this CoAP resource.
            The only argument it has must be a list of services that must have
            all the services that we want on the home server.

            Ex: if the server already has service 1 and 2,
            and we want to add the service 3, the list to be given must have 3 service
            JSON objects, each one representing the service 1, 2 and 3 respectively.

            The same logic should be applied to the deletion of services (ex: if we have
            already service 1, 2 and 3, and we want to delete service 2, the list to
            provide must have the JSON object representations of services 1 and 3).

            The update of services must be done changing all the services that should be
            updated and give the full list of services, now with the updated ones, but
            applying the same logic as the examples before.
        """
        try:
            services = new_services["SERVICES"]
        except:
            raise AppError(defines.Codes.BAD_REQUEST,\
                        "Update Services Data bad formated")

        if isinstance(services, list):
            try:
                data = {}
                for n_serv in services:
                    check_on_body(n_serv, ["name", "id", "core_service_ref"])
                    data[int(n_serv["id"])] = Service(int(n_serv["id"]), str(n_serv["name"]),\
                                                        n_serv["core_service_ref"])

                self.services.clear()
                self.services = data
                self.save_services_to_file()
            except:
                raise AppError(defines.Codes.BAD_REQUEST,\
                            "List of services improperly formated")
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Request body should be a json element with a key SERVICES and a list of services as value")
    #
    ### COAP METHODS
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")
        self.payload = self.get_payload()
        return status(self, response, defines.Codes.CONTENT)

    def render_PUT_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")
          
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(self, response, defines.Codes.BAD_REQUEST,\
                                    "Body content not properly json formated")

            try:
                self.update_server_services(body)

                self.payload = self.get_payload()
                return status(self, response, defines.Codes.CHANGED)
            except AppError as e:
                return error(self, response, e.code, e.msg)

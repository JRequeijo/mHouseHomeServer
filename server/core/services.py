#!/usr/bin/env python
import json

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import status, error, check_on_body, AppError, AppHTTPError

import logging

logger = logging.getLogger(__name__)

import settings

class Service:
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
        return {"id": self.id, "name": self.name, "core_service_ref":self.core_service_ref}


class HomeServerServices(Resource):
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
        return self.get_all_services()

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def load_services_from_file(self):
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
        for s in service_ids:
            try:
                if not self.services[int(s)]:
                    return False
            except:
                return False
        return True

    def get_all_services(self):
        data = {"SERVICES":[]}
        for s in self.services.itervalues():
            data["SERVICES"].append(s.get_info())
        return data

    def update_server_services(self, new_services):
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
                            "Request body should be a json element with a key SERVICES\
                                and a list of services as value")

        self.save_services_to_file()
    #
    ### COAP METHODS
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(defines.Codes.BAD_REQUEST, "Body content not properly json formated")

            try:
                self.update_server_services(body)

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self)
            except AppError as e:
                return error(e.code, e.msg)
            except:
                return error(defines.Codes.BAD_REQUEST,\
                            "Request query must specify an id of the service to update")

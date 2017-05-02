#!/usr/bin/env python
import json

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import status, error


import logging

logger = logging.getLogger(__name__)

class HomeServerInfo(Resource):
    def __init__(self, server):

        super(HomeServerInfo, self).__init__("HomeServerInfo", server, visible=True,
                                             observable=True, allow_children=False)

        self.server = server
        self.root_uri = "/info"

        self.server.add_resource(self.root_uri, self)

        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "HomeServer"
        self.interface_type = "if1"

    def get_info(self):
        return {"server_id": self.server.id, "name": self.server.name,\
                 "address": self.server.address}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):

        if request.content_type is defines.Content_types.get("application/json"):
            if str(request.source[0]) == self.server.address:
                try:
                    body = json.loads(request.payload)
                except:
                    logger.error("Request payload not json")
                    return error(defines.Codes.BAD_REQUEST,\
                                    "Request content must be json formated")

                try:
                    self.server.name = body["name"]

                    self.payload = self.get_payload()
                    return status(defines.Codes.CHANGED, self)

                except KeyError as err:
                    return error(defines.Codes.BAD_REQUEST,\
                                "Field ("+str(err.message)+") not found on request json body")
            else:
                return error(defines.Codes.FORBIDDEN,\
                            "Only from the cloud the server info can be updated")
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                            "Content must be application/json")

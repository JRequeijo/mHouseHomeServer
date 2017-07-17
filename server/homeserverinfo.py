"""
    This is the Home Server Info File.
    Here is specified the CoAP resource that represents the endpoint (URI)
    where all the home server information is stored and can be updated.
"""
import json
import logging

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import status, error

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)

class HomeServerInfo(Resource):
    """
        This is the Home Server Info CoAP resource.
        It represents the endpoint (URI) where all the home server
        information is stored and can be fetched and/or updated.
    """
    def __init__(self, server):

        super(HomeServerInfo, self).__init__("HomeServerInfo", server, visible=True,
                                             observable=True, allow_children=False)

        self.server = server
        self.root_uri = "/info"

        self.server.add_resource(self.root_uri, self)

        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "HomeServerInfo"
        self.interface_type = "if1"

    def get_info(self):
        """
            This method returns a dictionary with all the informations
            represented by this CoAP resource.
        """
        return {"server_id": self.server.id, "name": self.server.name,\
                 "coap_address": self.server.coapaddress, "coap_port": self.server.coapport,\
                 "multicast": self.server.multicast, "proxy_address": self.server.proxyaddress,\
                 "proxy_port": self.server.proxyport}

    def get_json(self):
        """
            This method returns a JSON representation
            with all the informations represented by this CoAP resource.
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with all the informations represented by this CoAP resource.
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

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
            if str(request.source[0]) == self.server.address:
                try:
                    body = json.loads(request.payload)
                except:
                    logger.error("Request payload not json")
                    return error(self, response, defines.Codes.BAD_REQUEST,\
                                    "Request content must be json formated")

                try:
                    self.server.name = body["name"]

                    self.payload = self.get_payload()
                    return status(self, response, defines.Codes.CHANGED)

                except KeyError as err:
                    return error(self, response, defines.Codes.BAD_REQUEST,\
                                "Field ("+str(err.message)+") not found on request json body")
            else:
                return error(self, response, defines.Codes.FORBIDDEN,\
                            "The server info can only be updated from the Cloud")
        else:
            return error(self, response, defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                            "Content must be application/json")

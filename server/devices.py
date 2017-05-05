#!/usr/bin/env python

import json
import time

from coapthon import defines
from coapthon.resources.resource import Resource

import settings

from utils import *
from core.devicetypes import DEVICE_TYPES, validate_device_type
# from core.services import SERVICES, validate_services
from core.propertytypes import PROPERTY_TYPES
import core.valuetypes as valuetypes

import requests

import thread
import os.path
import logging

from cloudcomm import *

logger = logging.getLogger(__name__)

#
########################################################################################
### Device Resource
class Device(Resource):
    def __init__(self, devices_list, device_id, name="", address="", type_id=0, services=[]):

        # initialize CoAP Resource
        super(Device, self).__init__(name, devices_list.server, visible=True,\
                                        observable=True, allow_children=False)

        self.server = devices_list.server

        self.root_uri = devices_list.root_uri +"/"+ str(device_id)

        self.devices_list = devices_list

        #### Device Data ####
        self.id = device_id
        self.universal_id = None
        self.name = name

        if validate_IPv4(address):
            self.address = address
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid IP address ("+str(address)+")")

        if validate_device_type(type_id):
            self.device_type_id = type_id
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid device type ("+str(type_id)+")")

        if self.server.services.validate_services(services):
            self.services_aux = services
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid services provided")

        self.server.add_resource(self.root_uri, self)

        # type of the device
        self.device_type = DeviceTypeResource(self)

        # state of the device - to modify periodically
        self.state = DeviceState(self)

        # services of the device
        self.services = DeviceServicesResource(self)


        self.last_access = time.time()

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "Device"
        self.interface_type = "if1"

    def get_info(self):
        return {"local_id": self.id, "name": self.name, "address": self.address,\
                "device_type": self.device_type.type.id, "services": self.services.services,\
                "state":self.state.get_simplified_info(), "universal_id":self.universal_id}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def delete(self):

        self.device_type.delete()
        self.state.delete()
        self.services.delete()

        self.devices_list.remove_device(self.id)

        del self.server.root[self.root_uri]
        return True

    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if(request.content_type is defines.Content_types.get("application/json")):
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(defines.Codes.BAD_REQUEST, "Request content must be json formated")

            try:
                self.name = body["name"]

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self)

            except KeyError as err:
                return error(defines.Codes.BAD_REQUEST,\
                            "Field ("+str(err.message)+") not found on request json body")
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                            "Content must be application/json")

    def render_DELETE(self, request):
        self.devices_list.remove_device(self.id)

        self.device_type.delete()
        self.state.delete()
        self.services.delete()

        if not settings.WORKING_OFFLINE:
            thread.start_new_thread(unregist_device_from_cloud, (self.universal_id,))

        return True

## Devices List Resource
class DevicesList(Resource):
    def __init__(self, server, devices=[]):

        super(DevicesList, self).__init__("DevicesList", server, visible=True,\
                                            observable=True, allow_children=False)

        self.server = server

        self.root_uri = "/devices"

        self.server.add_resource(self.root_uri, self)
        self.construct_devices_list(devices)

        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "DevicesList"
        self.interface_type = "if1"

    def construct_devices_list(self, devices):

        res = {}
        for d in devices:
            id = d["device_id"]
            res[int(id)] = Device(self, id, d["name"], d["address"],\
                                        d["device_type"], d["services"])

        self.devices = res

    def get_info(self):
        return {"devices": self.get_devices_list()}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def add_device(self, device):

        existing_dev = self.check_existing_device(device["address"])
        if existing_dev is not None:
            raise AppError(defines.Codes.BAD_REQUEST, "Device with address ("+device["address"]\
                                                        +") already exists")
        else:
            device_id = self.server.id_gen.new_device_id()

        #alterar a criacao do Device pondo todos os campos
        res = Device(self, device_id, name=device["name"],\
                     address=device["address"], type_id=device["device_type"],\
                     services=device["services"])
        self.devices[device_id] = res

        return res

    def remove_device(self, device_id):
        #alterar este modo de remocao
        self.devices.pop(device_id)
        return True

    def get_devices_list(self):
        ret = []
        for ele in self.devices.values():
            d = ele.get_info()
            d.pop("state")
            d.pop("services")
            ret.append(d)
        return ret

    def delete(self):

        for d in self.devices.values():
            d.delete()

        del self.server.root[self.root_uri]
        return True

    def check_existing_device(self, device_address):
        if not validate_IPv4(device_address):
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid IP address ("+str(device_address)+")")

        for d in self.devices.values():
            if d.address == device_address:
                return d.id
        return None
    
    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_POST(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(defines.Codes.BAD_REQUEST, "Body content not properly json formated")
            try:
                check_on_body(body, ["name", "address", "device_type", "services"])

                dev = self.add_device(body)

                if not settings.WORKING_OFFLINE:
                    thread.start_new_thread(regist_device_on_cloud, (dev,))

                self.payload = self.get_payload()
                return status(defines.Codes.CREATED, self)

            except AppError as err:
                logger.error("ERROR: "+err.msg)
                return error(err.code, err.msg)
            except AppHTTPError as err:
                logger.error("ERROR: "+err.msg)
                return error(err.code, err.msg)
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                                    "Content must be application/json")

## Device State Resource
class DeviceState(Resource):
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceState, self).__init__("DeviceState", device.server, visible=True,\
                                            observable=True, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/state"

        device.server.add_resource(self.root_uri, self)

        # state of the device - to modify periodically
        self.state = DEVICE_TYPES[int(device.device_type_id)].default_state()

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "DeviceState"
        self.interface_type = "if1"

    def get_simplified_info(self):
        ret = {}
        for p in self.state:
            ret[p["name"]] = p["value"]

        return ret

    def get_info(self):
        return {"device_id": self.device.id, "state": self.state}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def change_state(self, new_state, origin):

        properties = self.device.device_type.type.properties

        keys = []
        for p in properties:
            keys.append(str(p.id))
            keys.append(str(p.name))

        for p in new_state.keys():
            if not str(p) in keys:
                raise AppError(defines.Codes.BAD_REQUEST,\
                                "Device does not have property ("+str(p)+")")

        for k in new_state.keys():
            if isinstance(k, basestring):
                try:
                    key = int(k)
                    for p in self.state:
                        if p["property_id"] == key:
                            prop = PROPERTY_TYPES[key]
                            if prop.validate(new_state[k]):
                                if self.device.address != str(origin) and\
                                    prop.accessmode not in ["WO", "RW"]:
                                    raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(key)+") can not be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                                if prop.valuetype_class == valuetypes.SCALAR:
                                    p["value"] = float(new_state[k])
                                else:
                                    p["value"] = str(new_state[k])
                            else:
                                raise AppError(defines.Codes.BAD_REQUEST,\
                                            "Invalid property new value ("+str(new_state[k])+")")
                except:
                    for p in self.state:
                        if p["name"] == str(k):
                            prop = PROPERTY_TYPES[int(p["property_id"])]
                            if prop.validate(new_state[k]):
                                if self.device.address != str(origin) and\
                                    prop.accessmode not in ["WO", "RW"]:
                                    raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(k)+") can not be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                                if prop.valuetype_class == valuetypes.SCALAR:
                                    p["value"] = float(new_state[k])
                                else:
                                    p["value"] = str(new_state[k])
                            else:
                                raise AppError(defines.Codes.BAD_REQUEST,\
                                                "Invalid property new value ("\
                                                            +str(new_state[k])+")")
            else:
                raise AppError(defines.Codes.INTERNAL_SERVER_ERROR,\
                            "Property id or name invalid format. Must be int or string.")
        return True
    def delete(self):
        del self.device.server.root[self.root_uri]
        return True

    # CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            origin = request.source[0]
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(defines.Codes.BAD_REQUEST,\
                            "Request payload not properly formated json")

            try:
                if isinstance(body, dict):
                    self.change_state(body, origin)
                else:
                    raise AppError(defines.Codes.BAD_REQUEST,\
                            "Content must be a json dictionary")
                print self.device.address
                print str(origin)

                if not settings.WORKING_OFFLINE:
                    if self.device.address == str(origin):
                        thread.start_new_thread(notify_cloud, (self,))

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self)
                # return self

            except AppError as err:
                return error(err.code, err.msg)
            except:
                print "FATAL UNKNOWN ERROR"
                return defines.Codes.INTERNAL_SERVER_ERROR
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                        "Request content must be application/json")

## Device Type Resource
class DeviceTypeResource(Resource):
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceTypeResource, self).__init__("DeviceType", device.server, visible=True,\
                                                    observable=False, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/type"

        device.server.add_resource(self.root_uri, self)

        self.type = DEVICE_TYPES[int(device.device_type_id)]

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "home_server"
        self.interface_type = "if1"

    def get_info(self):
        return {"device_id": self.device.id, "device_type": self.type.get_info()}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def delete(self):
        del self.device.server.root[self.root_uri]
        return True

    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self
## Device Services Resource
class DeviceServicesResource(Resource):
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceServicesResource, self).__init__("DeviceService", device.server, visible=True,\
                                            observable=False, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/services"

        device.server.add_resource(self.root_uri, self)

        self.services = device.services_aux
        del device.services_aux

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "DeviceServices"
        self.interface_type = "if1"


    def get_info(self):
        return {"device_id": self.device.id, "services": self.get_services()}

    def get_json(self):
        return json.dumps(self.get_info())

    def get_payload(self):
        return (defines.Content_types[self.res_content_type], json.dumps(self.get_info()))

    def get_services(self):
        aux = self.services
        for s in aux:
            if int(s) not in self.device.server.services.services.keys():
                self.services.remove(s)

        return self.services

    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_POST(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                return error(defines.Codes.BAD_REQUEST, "Request content must be json formated")

            try:
                if self.device.server.services.validate_services(body):
                    for n in body:
                        serv = int(n)
                        if serv not in self.services:
                            self.services.append(serv)
                else:
                    return error(defines.Codes.BAD_REQUEST,\
                                    "Services provided are not valid")

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self)
            except:
                return error(defines.Codes.BAD_REQUEST,\
                "Request content must specify a list of service ids in json format")
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                        "Request content format not application/json")

    def render_DELETE(self, request):
        try:
            query = request.uri_query
            aux = [query]
            d = dict(s.split("=") for s in aux)
            id = int(d["id"])
            try:
                self.services.remove(id)
            except:
                return error(defines.Codes.NOT_FOUND,\
                            "Service with id ("+str(id)+") is not attributed for this device")

            self.payload = self.get_payload()
            return status(defines.Codes.DELETED, self)
        except:
            return error(defines.Codes.BAD_REQUEST,\
            "Request query must specify an id of the service to remove")


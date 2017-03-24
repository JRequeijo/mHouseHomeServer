#!/usr/bin/env python

import json

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import *
from core.devicetypes import DEVICE_TYPES, validate_device_type
from core.services import SERVICES, validate_services
from core.propertytypes import PROPERTY_TYPES
import core.valuetypes as valuetypes
# from twisted.protocols.dict import define
# from server.infrastructure.device import valuetypes
# from server.communicator import Communicator


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
        self.name = name

        if validate_IPv4(address):
            self.address = address
        else:
            raise AppError(defines.Codes.INTERNAL_SERVER_ERROR,\
                            "Invalid IP address ("+str(address)+")")

        if validate_device_type(type_id):
            self.device_type_id = type_id

        if validate_services(services):
            self.services_ids = services

        self.server.add_resource(self.root_uri, self)

        # type of the device
        self.device_type = DeviceTypeResource(self)

        # state of the device - to modify periodically
        self.state = DeviceState(self)

        # services of the device
        self.services = DeviceServicesResource(self)
        
        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "Device"
        self.interface_type = "if1"

    def get_info(self):
        return {"device_id": self.id, "name": self.name, "address": self.address,\
                "device_type": self.device_type.type.id, "services": self.services_ids,\
                "state":self.state.get_simplified_info()}

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


    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_DELETE(self, request):
        self.devices_list.remove_device(self.id)

        self.device_type.delete()
        self.state.delete()
        self.services.delete()

        return True

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
            res[int(id)] = Device(self, id, d["name"], d["address"], d["type"], d["services"])

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
            self.devices[existing_dev].delete()
            device_id = existing_dev
        else:
            device_id = self.server.id_gen.new_device_id()

        #alterar a criacao do Device pondo todos os campos
        res = Device(self, device_id, name=device["name"],\
                     address=device["address"], type_id=device["type"], services=device["services"])
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
                # print "FOUND"
                return d.id
        return None

    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_POST(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                print "ERROR: Request payload not json"
                return error(defines.Codes.BAD_REQUEST, "Body content not properly json formated")
            try:
                check_on_body(body, ["name", "address", "type", "services"])

                self.add_device(body)

                self.payload = self.get_payload()
                return status(defines.Codes.CREATED, self.payload)

            except AppError as err:
                print "ERROR: "+err.msg
                return error(err.code, err.msg)
            except AppHTTPError as err:
                print "ERROR: "+err.msg
                return error(err.code, err.msg)
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                                    "Content must be application/json")


class DeviceState(Resource):
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceState, self).__init__("DeviceState", device.server, visible=True,\
                                            observable=False, allow_children=False)

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

    def change_state(self, new_state):

        properties = self.device.device_type.type.properties

        keys = []
        for p in properties:
            keys.append(str(p.id))
            keys.append(str(p.name))

        # print keys

        for p in new_state.keys():
            if not str(p) in keys:
                raise AppError(defines.Codes.BAD_REQUEST,\
                                "Device does not have property ("+str(p)+")")

        for k in new_state.keys():
            if isinstance(k, int):
                for p in self.state:
                    if p["property_id"] == int(k):
                        prop = PROPERTY_TYPES[int(k)]
                        if prop.validate(new_state[k]):
                            if prop.accessmode in ["WO", "RW"]:
                                if prop.valuetype_class == valuetypes.SCALAR:
                                    p["value"] = int(new_state[k])
                                else:
                                    p["value"] = str(new_state[k])

                                return True
                            else:
                                raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(k)+") can't be written (access mode: "+\
                                                                            str(prop.accessmode))
                        else:
                            raise AppError(defines.Codes.BAD_REQUEST,\
                                            "Invalid property new value ("+str(new_state[k])+")")

            elif isinstance(k, basestring):
                try:
                    key = int(k)
                except:
                    for p in self.state:
                        if p["name"] == str(k):
                            prop = PROPERTY_TYPES[int(p["property_id"])]
                            if prop.validate(new_state[k]):
                                if prop.accessmode in ["WO", "RW"]:
                                    if prop.valuetype_class == valuetypes.SCALAR:
                                        p["value"] = int(new_state[k])
                                    else:
                                        p["value"] = str(new_state[k])

                                    return True
                                else:
                                    raise AppError(defines.Codes.FORBIDDEN,\
                                            "Property ("+str(k)+") can't be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                            else:
                                raise AppError(defines.Codes.BAD_REQUEST,\
                                                "Invalid property new value ("\
                                                            +str(new_state[k])+")")

                for p in self.state:
                    if p["property_id"] == key:
                        prop = PROPERTY_TYPES[key]
                        if prop.validate(new_state[k]):
                            if prop.accessmode in ["WO", "RW"]:
                                if prop.valuetype_class == valuetypes.SCALAR:
                                    p["value"] = int(new_state[k])
                                else:
                                    p["value"] = str(new_state[k])

                                return True
                            else:
                                raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(key)+") can't be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                        else:
                            raise AppError(defines.Codes.BAD_REQUEST,\
                                        "Invalid property new value ("+str(new_state[k])+")")

            else:
                raise AppError(defines.Codes.INTERNAL_SERVER_ERROR,\
                            "Property id or name invalid format. Must be int or string.")

    def delete(self):
        del self.device.server.root[self.root_uri]
        return True

    # CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                print "ERROR: Request payload not json"
                return error(defines.Codes.BAD_REQUEST,\
                            "Request payload not properly formated json")

            try:
                if isinstance(body, dict):
                    self.change_state(body)
                else:
                    raise AppError(defines.Codes.BAD_REQUEST,\
                            "Content must be a json dictionary")

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self.payload)

            except AppError as err:
                return error(err.code, err.msg)
            except:
                print "FATAL UNKNOWN ERROR"
                return defines.Codes.INTERNAL_SERVER_ERROR
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                        "Request content must be application/json")

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

    def render_GET(self, request):
        self.payload = self.get_payload()
        return self
 
class DeviceServicesResource(Resource):
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceServicesResource, self).__init__("DeviceService", device.server, visible=True,\
                                            observable=False, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/services"

        device.server.add_resource(self.root_uri, self)

        self.services = {}

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
        return self.services

    def delete(self):
        del self.device.server.root[self.root_uri]
        return True

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
                if isinstance(body, list):
                    for ele in body:
                        id = ele["id"]
                        name = ele["name"]
                        self.services[int(id)] = name

                elif isinstance(body, dict):
                    id = ele["id"]
                    name = ele["name"]
                    self.services[int(id)] = name
                else:
                    return error(defines.Codes.BAD_REQUEST,\
                    "Request content must be json list of services or\
                             a json dictionary with only one service")

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self.payload)

            except:
                return error(defines.Codes.BAD_REQUEST,\
                            "Request content must specify a service id in json format")
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                        "Request content format not application/json")

    def render_DELETE(self, request):
        try:
            query = request.uri_query
            aux = [query]
            d = dict(s.split("=") for s in aux)
            id = d["id"]
            try:
                self.services.pop(id)
            except:
                return error(defines.Codes.NOT_FOUND,\
                            "Service with id ("+str(id)+") is not attributed for this device")

            self.payload = self.get_payload()
            return status(defines.Codes.DELETED, self.payload)
        except:
            return error(defines.Codes.BAD_REQUEST,\
            "Request query must specify an id of the service to remove from the device services")

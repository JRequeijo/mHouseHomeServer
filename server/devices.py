"""
    This is the Home Server Devices file.
    Here are specified CoAP resources representing the endpoints (URIs)
    where the Home Server list of devices can be viewed and/or updated,
    as well as the endpoints for each one of the devices connected to the
    Home Server and their accessible sub-endpoints/childrens (Device State, Type and
    Services).
"""
import json
import thread
import os.path
import logging

import requests
import time

from coapthon import defines
from coapthon.resources.resource import Resource

import settings
from utils import *

from cloudcomm import regist_device_on_cloud, unregist_device_from_cloud, notify_cloud

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)

#
########################################################################################
### Device Resource
class Device(Resource):
    """
        This is the Device CoAP resource.
        It represents each Device endpoint (URI) for the Home Server.
        It has all the Device informations and accessible sub-endpoints/childrens.
    """
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

        if self.server.configs.validate_device_type(type_id):
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
        """
            This method returns a dictionary with all the device informations
            represented by this CoAP resource
        """
        return {"local_id": self.id, "name": self.name, "address": self.address,\
                "device_type": self.device_type.type.id, "services": self.services.services,\
                "state":self.state.get_simplified_info(), "universal_id":self.universal_id}

    def get_json(self):
        """
            This method returns a JSON representation with all the
            device informations represented by this CoAP resource.
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with all the device informations represented by this CoAP resource.
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def delete(self):
        """
            This method deletes a Device, i.e. it deletes the device
            CoAP representation and all its sub-endpoints/childrens CoAP representations,
            'deleting' the full device from this server
        """
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
    """
        This is the Devices List CoAP resource.
        It represents the list of Devices endpoint (URI) for the Home Server.
        It has all the Devices present on this Home Server.
    """
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

    

    def get_info(self):
        """
            This method returns a dictionary with the list of devices
            present on this Home Server
        """
        return {"devices": self.get_devices_list()}

    def get_json(self):
        """
            This method returns a JSON representation with the list of devices
            present on this Home Server
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with  the list of devices present on this Home Server
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def construct_devices_list(self, devices):
        """
            This method builds a list of devices CoAP resource with the information
            (list) given on the argument devices. This list must be a JSON object list
            with each object representing a device
        """
        res = {}
        for d in devices:
            id = d["device_id"]
            res[int(id)] = Device(self, id, d["name"], d["address"],\
                                        d["device_type"], d["services"])

        self.devices = res
    def add_device(self, device):
        """
            This method adds a new device to the list of device represented by
            the CoAP resource. The device to add is given on the 'device' argument
            and it must be a dictionary representing the device (with the device
            informations)
        """
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
        """
            This method removes a device from the list of devices represented
            by the CoAP resource. The device to remove from the list is identified
            by its ID with the 'device_id' argument.
            CAUTION: this method may not delete the device CoAP representation from
            memory, it only removes the device from the list of devices. To delete the
            full device use the 'delete' method on the Device CoAP representation, which
            by itself calls this method to remove the device from the list of devices.
        """
        self.devices.pop(device_id)
        return True

    def get_devices_list(self):
        """
            This method returns the list of devices represented by this
            CoAP resource.
        """
        ret = []
        for ele in self.devices.values():
            d = ele.get_info()
            d.pop("state")
            d.pop("services")
            ret.append(d)
        return ret

    def delete(self):
        """
            This method deletes the list of devices CoAP representation, as well as
            all of its sub-endpoints/childrens (devices and their childrens) in a
            recursive way.
            It deletes all devices and the list endpoint from the server memory.
        """
        for d in self.devices.values():
            d.delete()

        del self.server.root[self.root_uri]
        return True

    def check_existing_device(self, device_address):
        """
            This method checks if a device with the IP address given on the
            first argument (device_address) is already present/registered
            on the Home Server.
        """
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
    """
        This is the Device State CoAP resource.
        It represents the state endpoint (URI) of a given Device.
    """
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceState, self).__init__("DeviceState", device.server, visible=True,\
                                            observable=True, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/state"

        device.server.add_resource(self.root_uri, self)

        # state of the device - to modify periodically
        self.state = self.device.server.configs.device_types[int(device.device_type_id)].default_state()

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "DeviceState"
        self.interface_type = "if1"

    

    def get_info(self):
        """
            This method returns a dictionary with the detailed state information
            correspondent to a given device
        """
        return {"device_id": self.device.id, "state": self.state}

    def get_json(self):
        """
            This method returns a JSON representation with the detailed
            state information correspondent to a given device
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with the detailed state information correspondent to a given device
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def get_simplified_info(self):
        """
            This method returns a dictionary with the simplified state information
            correspondent to a given device. This information is simplified because
            the dictionary is formated like {"property1_name":"property1_value",
            ..., "propertyN_name":"propertyN_value"}
        """
        ret = {}
        for p in self.state:
            ret[p["name"]] = p["value"]

        return ret
    def change_state(self, new_state, origin):
        """
            This method updates the state of a given device.
            It recieves the first argument (new_state), which should be a
            dictionary with a simplified representation of the new state, i.e.
            {"property1_name":"property1_value",..., "propertyN_name":"propertyN_value"},
            and where at least one of the Device's properties must be present.
            The second argument (origin) must be the IP address from where the update
            is being requested, in order to secure that only the device itself can update
            RO properties.
        """
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
                            prop = self.device.server.configs.property_types[key]
                            if prop.validate(new_state[k]):
                                if self.device.address != str(origin) and\
                                    prop.accessmode not in ["WO", "RW"]:
                                    raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(key)+") can not be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                                if prop.valuetype_class == "SCALAR":
                                    p["value"] = float(new_state[k])
                                else:
                                    p["value"] = str(new_state[k])
                            else:
                                raise AppError(defines.Codes.BAD_REQUEST,\
                                            "Invalid property new value ("+str(new_state[k])+")")
                except:
                    for p in self.state:
                        if p["name"] == str(k):
                            prop = self.device.server.configs.property_types[int(p["property_id"])]
                            if prop.validate(new_state[k]):
                                if self.device.address != str(origin) and\
                                    prop.accessmode not in ["WO", "RW"]:
                                    raise AppError(defines.Codes.FORBIDDEN,\
                                        "Property ("+str(k)+") can not be written (access mode: "\
                                                                        +str(prop.accessmode)+")")
                                if prop.valuetype_class == "SCALAR":
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
        """
            This method deletes the device state CoAP representation from the server.
        """
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
    """
        This is the Device Type CoAP resource.
        It represents the type endpoint (URI) of a given Device.
    """
    def __init__(self, device):

        # initialize CoAP Resource
        super(DeviceTypeResource, self).__init__("DeviceType", device.server, visible=True,\
                                                    observable=False, allow_children=False)

        #### Device Data ####
        self.device = device

        self.root_uri = device.root_uri+"/type"

        device.server.add_resource(self.root_uri, self)

        self.type = self.device.server.configs.device_types[int(device.device_type_id)]

        ### CoAP Resource Data ###
        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "home_server"
        self.interface_type = "if1"

    def get_info(self):
        """
            This method returns a dictionary with the device type information
            correspondent to a given device
        """
        return {"device_id": self.device.id, "device_type": self.type.get_info()}

    def get_json(self):
        """
            This method returns a JSON representation with the
            device type information correspondent to a given device
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with the device type information correspondent to a given device
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def delete(self):
        """
            This method deletes the device type CoAP representation from the server.
        """
        del self.device.server.root[self.root_uri]
        return True

    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self
## Device Services Resource
class DeviceServicesResource(Resource):
    """
        This is the Device Services CoAP resource.
        It represents the services endpoint (URI) of a given Device, i.e.
        the services that the device subscribed.
    """
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
        """
            This method returns a dictionary with the services information
            correspondent to a given device
        """
        return {"device_id": self.device.id, "services": self.get_services()}

    def get_json(self):
        """
            This method returns a JSON representation with the
            services information correspondent to a given device
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with the services information correspondent to a given device
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def get_services(self):
        """
            This method returns the list of services subscribed by the device.
            It auto-updates where some service is removed from the server and is
            no longer supported by it, so the devices cannot use it anymore.
        """
        aux = self.services
        for s in aux:
            if int(s) not in self.device.server.services.services.keys():
                self.services.remove(s)

        return self.services
    
    def delete(self):
        """
            This method deletes the services CoAP representation from the server.
        """
        del self.device.server.root[self.root_uri]
        return True

    ## CoAP Methods
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                body = json.loads(request.payload)
            except:
                return error(defines.Codes.BAD_REQUEST, "Request content must be json formated")

            try:
                if self.device.server.services.validate_services(body):
                    del self.services
                    self.services = []
                    for n in body:
                        self.services.append(int(n))
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


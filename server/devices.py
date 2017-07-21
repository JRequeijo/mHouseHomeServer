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
import copy
import sys

import requests
import time

from coapthon import defines
from coapthon.resources.resource import Resource

import settings
from utils import *
from proxy.communicator import Communicator

import cloudcommunicators.cloudcomm as cloudcomm

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
    def __init__(self, devices_list, device_id, name="", address="", port=0, type_id=0,\
                    services=[], timeout=settings.ENDPOINT_DEFAULT_TIMEOUT):

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
            self.port = port
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

        self.timeout = int(timeout)

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
                "port":self.port, "device_type": self.device_type.type.id,\
                "universal_id":self.universal_id, "timeout":self.timeout}

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
        logger.debug("Deleting device "+str(self.id))
        self.device_type.delete()
        self.state.delete()
        self.services.delete()

        self.devices_list.remove_device(self.id)

        del self.server.root[self.root_uri]
        return True

    def update_all_info(self, data):
        try:
            dev_type = data["device_type"]
            servs = data["services"]
            timeout = data["timeout"]
        except KeyError as err:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Field ("+err+") is missing")

        if self.server.configs.validate_device_type(dev_type):
            self.device_type_id = dev_type
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid device type ("+str(dev_type)+")")

        if self.server.services.validate_services(servs):
            self.services_aux = servs
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Invalid services provided")
        
        self.timeout = int(timeout)

        self.device_type.delete()
        self.state.delete()
        self.services.delete()

        # type of the device
        self.device_type = DeviceTypeResource(self)

        # state of the device - to modify periodically
        self.state = DeviceState(self)

        # services of the device
        self.services = DeviceServicesResource(self)

        self.last_access = time.time()

    ## CoAP Methods
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        if self.address == str(request.source[0]):
            self.last_access = time.time()

        self.payload = self.get_payload()
        return status(self, response, defines.Codes.CONTENT)

    def render_PUT_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        if(request.content_type is defines.Content_types.get("application/json")):
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(self, response, defines.Codes.BAD_REQUEST,\
                                    "Request content must be json formated")

            try:
                self.name = body["name"]

                if self.address == str(request.source[0]):
                    self.update_all_info(body)
                    cloudcomm.regist_device_on_cloud(self)

                self.payload = self.get_payload()
                return status(self, response, defines.Codes.CHANGED)

            except KeyError as err:
                return error(self, response, defines.Codes.BAD_REQUEST,\
                            "Field ("+str(err.message)+") not found on request json body")
        else:
            return error(self, response, defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                            "Content must be application/json")

    def render_DELETE_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")
          
        if request.source[0] == self.address:
            self.devices_list.remove_device(self.id)

            self.device_type.delete()
            self.state.delete()
            self.services.delete()

            if not settings.WORKING_OFFLINE:
                cloudcomm.unregister_device_from_cloud_platforms(self)

            return True, response
        else:
            return error(self, response, defines.Codes.FORBIDDEN, "You do not have permission to delete this device")

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
    def add_device(self, device, address, port):
        """
            This method adds a new device to the list of device represented by
            the CoAP resource. The device to add is given on the 'device' argument
            and it must be a dictionary representing the device (with the device
            informations)
        """
        existing_dev = self.check_existing_device(address)
        if existing_dev is not None:
            raise AppError(defines.Codes.BAD_REQUEST, "Device with address ("+address\
                                                        +") already exists with ID ("+\
                                                        str(existing_dev)+")")
        else:
            device_id = self.server.id_gen.new_device_id()

        #alterar a criacao do Device pondo todos os campos
        res = Device(self, device_id, name=device["name"],\
                     address=address, port=port, type_id=device["device_type"],\
                     services=device["services"], timeout=device["timeout"])
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
            ret.append(d)
        return ret

    def get_created_device(self, device):
        data = device.get_info()
        js = json.dumps(data)

        return (defines.Content_types[self.res_content_type], js)

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

        for d in self.devices.itervalues():
            if d.address == device_address:
                d.last_access = time.time()
                return d.id
        return None

    def monitoring_devices(self):
        """
            This method checks if every device is still active, i.e.
            it checks if a given device was accessed at least one time
            on the interval between the current time and the current time
            minus timeout.
            If one device was not accessed at least one time in that interval
            it is marked for deletion and then it is deleted.
        """
        while not self.server.stopped.isSet():
            try:
                now = time.time()
                del_marked = []
                for d in self.devices.itervalues():
                    if (now-d.timeout) > d.last_access:
                        comm = Communicator(d.address)
                        try:
                            comm.get("/", timeout=settings.DEVICES_MONITORING_TIMEOUT)
                            d.last_access = time.time()
                        except:
                            comm.stop()
                            logger.debug("Device ("+str(d.id)+") is down")
                            del_marked.append(d)
                            logger.debug("Device ("+str(d.id)+") marked for deletion")

                for d in del_marked:
                    d.delete()
                    logger.debug("Device ("+str(d.id)+") Deleted")
            except Exception as e:
                print e.message

        sys.exit(0)

    ## CoAP Methods
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        for d in self.devices.itervalues():
            if d.address == str(request.source[0]):
                d.last_access = time.time()

        self.payload = self.get_payload()
        return status(self, response, defines.Codes.CONTENT)

    def render_POST_advanced(self, request, response):
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
                check_on_body(body, ["name", "device_type", "services", "timeout"])

                address = str(request.source[0])
                port = int(request.source[1])
                dev = self.add_device(body, address, port)

                if not settings.WORKING_OFFLINE:
                    cloudcomm.register_device_on_cloud_platforms(dev)

                self.payload = self.get_created_device(dev)
                return status(self, response, defines.Codes.CREATED)

            except AppError as err:
                logger.error("ERROR: "+err.msg)
                return error(self, response, err.code, err.msg)
            except AppHTTPError as err:
                logger.error("ERROR: "+err.msg)
                return error(self, response, err.code, err.msg)
        else:
            return error(self, response, defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
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
        self.wanted_state = copy.deepcopy(self.state)

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
        return {"device_id": self.device.id,\
                "current_state": self.get_simplified_current_state(),\
                "wanted_state":self.get_simplified_wanted_state()}

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
        return {"current_state":self.get_simplified_current_state(),\
                "wanted_state":self.get_simplified_wanted_state()}

    def get_simplified_current_state(self):
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

    def get_simplified_wanted_state(self):
        """
            This method returns a dictionary with the simplified state information
            correspondent to a given device. This information is simplified because
            the dictionary is formated like {"property1_name":"property1_value",
            ..., "propertyN_name":"propertyN_value"}
        """
        ret = {}
        for p in self.wanted_state:
            ret[p["name"]] = p["value"]

        return ret
    def change_state(self, new_state):
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

    def change_wanted_state(self, new_state):
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
                    for p in self.wanted_state:
                        if p["property_id"] == key:
                            prop = self.device.server.configs.property_types[key]
                            if prop.validate(new_state[k]):
                                if prop.accessmode not in ["WO", "RW"]:
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
                    for p in self.wanted_state:
                        if p["name"] == str(k):
                            prop = self.device.server.configs.property_types[int(p["property_id"])]
                            if prop.validate(new_state[k]):
                                if prop.accessmode not in ["WO", "RW"]:
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
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        if self.device.address == str(request.source[0]):
            self.device.last_access = time.time()

        self.payload = self.get_payload()
        return status(self, response, defines.Codes.CONTENT)

    def render_PUT_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")
          
        if request.content_type is defines.Content_types.get("application/json"):
            origin = request.source
            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(self, response, defines.Codes.BAD_REQUEST,\
                            "Request payload not properly formated json")

            try:
                if isinstance(body, dict):
                    if self.device.address == str(origin[0]):
                        self.device.last_access = time.time()
                        self.change_state(body)
                        self.wanted_state = copy.deepcopy(self.state)
                    else:
                        self.change_wanted_state(body)
                else:
                    raise AppError(defines.Codes.BAD_REQUEST,\
                            "Content must be a json dictionary")

                if not settings.WORKING_OFFLINE:
                    if self.device.address == str(origin[0]):
                        cloudcomm.notify_cloud_platforms(self.device)

                self.payload = self.get_payload()
                return status(self, response, defines.Codes.CHANGED)

            except AppError as err:
                return error(self, response, err.code, err.msg)
            except:
                print "FATAL UNKNOWN ERROR"
                return defines.Codes.INTERNAL_SERVER_ERROR
        else:
            return error(self, response, defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
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
        return {"device_id": self.device.id, "device_type": self.type.get_info(True)}

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
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        if self.device.address == str(request.source[0]):
            self.device.last_access = time.time()

        self.payload = self.get_payload()
        return status(self, response, defines.Codes.CONTENT)
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
    def render_GET_advanced(self, request, response):
        if request.accept != defines.Content_types["application/json"] and request.accept != None:
            return error(self, response, defines.Codes.NOT_ACCEPTABLE,\
                                    "Could not satisfy the request Accept header")

        if self.device.address == str(request.source[0]):
            self.device.last_access = time.time()

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
                return error(self, response, defines.Codes.BAD_REQUEST,\
                                    "Request content must be json formated")

            try:
                if self.device.server.services.validate_services(body):
                    del self.services
                    self.services = []
                    for n in body:
                        self.services.append(int(n))
                else:
                    return error(self, response, defines.Codes.BAD_REQUEST,\
                                    "Services provided are not valid")

                if self.device.address == str(request.source[0]):
                    self.device.last_access = time.time()

                self.payload = self.get_payload()
                return status(self, response, defines.Codes.CHANGED)
            except:
                return error(self, response, defines.Codes.BAD_REQUEST,\
                "Request content must specify a list of service ids in json format")
        else:
            return error(self, response, defines.Codes.UNSUPPORTED_CONTENT_FORMAT,\
                        "Request content format not application/json")

    
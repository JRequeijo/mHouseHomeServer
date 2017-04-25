#!/usr/bin/env python

import json

from propertytypes import PROPERTY_TYPES
import settings
import logging


logger = logging.getLogger(__name__)

class DeviceType:
    def __init__(self, devicetype_id, name, properties=[]):
        self.id = devicetype_id
        self.name = name

        self.properties = []

        for p in properties:
            if int(p) in PROPERTY_TYPES.keys():
                self.properties.append(PROPERTY_TYPES[int(p)])
            else:
                raise Exception("Invalid Property")

    def get_info(self):
        return {"id": self.id, "name": self.name, "properties": self.get_properties()}

    def get_properties(self):
        prop = []
        for p in self.properties:
            prop.append(p.get_info())

        return prop

    def default_state(self):
        ret = []
        for p in self.properties:
            rep = {"property_id": p.id, "name": p.name, "value": p.default_value,\
                    "type": p.valuetype_class}
            ret.append(rep)

        return ret

DEVICE_TYPES = {0: DeviceType(0, "Empty Device", [])}

def validate_device_type(type_id):
    try:
        if DEVICE_TYPES[int(type_id)]:
            return True
        else:
            return False
    except:
        return False

# def add_deviceType(new_type):
#     DEVICE_TYPES[str(new_type.id)] = new_type

try:
    f = open(str(settings.DEVICE_TYPES_CONFIG_FILE), "r")

    file = json.load(f)
    logger.info("Loading "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" File...")
    for ele in file["DEVICE_TYPES"]:
        id = ele["id"]
        name = ele["name"]
        properties = ele["properties"]

        DEVICE_TYPES[int(id)] = DeviceType(id, name, properties)
    f.close()
except:
    logger.info("FILE: "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" not found")

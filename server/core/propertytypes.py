#!/usr/bin/env python

import json

import valuetypes
import settings
import logging.config
logger = logging.getLogger(__name__)

class PropertyType:
    def __init__(self, property_type_id, prop_type_name, accessmode,\
                    valuetype_class, valuetype_id):

        self.id = property_type_id
        self.name = prop_type_name

        if accessmode in ['RO', 'WO', 'RW']:
            self.accessmode = accessmode
        else:
            raise Exception("Invalid Access Mode")

        self.valuetype_class = valuetype_class
        self.valuetype_id = valuetype_id

        if valuetype_class == valuetypes.SCALAR:
            self.valuetype = valuetypes.SCALAR_VALUE_TYPES[str(valuetype_id)]
            self.default_value = self.valuetype.default_value
        elif valuetype_class == valuetypes.ENUM:
            self.valuetype = valuetypes.ENUM_VALUE_TYPES[str(valuetype_id)]
            self.default_value = self.valuetype.default_value
        elif valuetype_class == valuetypes.ARRAY:
            self.valuetype = valuetypes.ARRAY_VALUE_TYPES[str(valuetype_id)]
            self.default_value = self.valuetype.default_value

    def get_info(self):
        return {"property_id": self.id, "name": self.name,\
                "accessmode": self.accessmode, "valuetype": self.valuetype_class}

    def validate(self, value):
        return self.valuetype.validate(value)

PROPERTY_TYPES = {0: PropertyType(0, "Default_RO_Property", "RO", valuetypes.SCALAR, 0)}

def add_property(new_property):
    PROPERTY_TYPES[str(new_property.id)] = new_property

try:
    fp = open(str(settings.PROPERTY_TYPES_CONFIG_FILE), "r")

    data = json.load(fp)
    logger.info("Loading "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" file...")

    for ele in data["PROPERTY_TYPES"]:
        id = ele["id"]
        name = ele["name"]
        access_mode = ele["access_mode"]
        value_type = ele["value_type_class"]
        value_type_id = ele["value_type_id"]

        PROPERTY_TYPES[int(id)] = PropertyType(id, name, access_mode, value_type, value_type_id)

    fp.close()
except:
    logger.info("FILE: "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" not found")

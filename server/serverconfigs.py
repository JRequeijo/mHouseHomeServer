"""
    This is the Home Server Configurations file.
    Here are specified all classes representing each configuration
    and also the CoAP resource that represents the endpoint (URI)
    where the Home Server configurations can be viewed and/or updated.
"""
import json
import logging

from coapthon import defines
from coapthon.resources.resource import Resource

from utils import status, error, check_on_body, AppError, AppHTTPError
import settings

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)

#
## DEVICE TYPE
class DeviceType(object):
    """
        This is the Device Type Configuration class.
        Each object of this class represents a Device Type that
        can be connected/used in this Home Server.
    """
    def __init__(self, server_configs_res, devicetype_id, name, properties=[]):
        try:
            self.id = int(devicetype_id)
            self.name = str(name)

            if isinstance(properties, list):
                self.properties = []
                for p in properties:
                    try:
                        self.properties.append(server_configs_res.property_types[int(p)])
                    except (ValueError, TypeError):
                        raise Exception("Invalid Property ("+str(p)+")")
            else:
                raise Exception("Properties argument must be a list of property IDs")

        except (ValueError, TypeError):
            raise Exception("Invalid values on scalar value type arguments")

    def get_info(self):
        """
            This method returns a dictionary with all the information
            correspondent to a given Device Type.
        """
        return {"id": self.id, "name": self.name, "properties": self.get_properties()}

    def get_properties(self):
        """
            This method returns all properties that a given Device Type has.
        """
        prop = []
        for p in self.properties:
            prop.append(p.get_info())
        return prop

    def default_state(self):
        """
            This method returns the default properties state that a given
            Device Type has.
        """
        ret = []
        for p in self.properties:
            rep = {"property_id": p.id, "name": p.name, "value": p.default_value,\
                    "type": p.valuetype_class}
            ret.append(rep)

        return ret
#
### PROPERTY TYPE
class PropertyType(object):
    """
        This is the Property Type Configuration class.
        Each object of this class represents a Property Type that
        the devices connected/used in this Home Server can have.
    """
    def __init__(self, server_configs_res, property_type_id, prop_type_name, accessmode,\
                    valuetype_class, valuetype_id):
        try:
            self.id = int(property_type_id)
            self.name = str(prop_type_name)

            if str(accessmode) in ["RO", "WO", "RW"]:
                self.accessmode = str(accessmode)
            else:
                raise Exception("Invalid Access Mode")

            if str(valuetype_class) in ["SCALAR", "ENUM"]:
                self.valuetype_class = str(valuetype_class)
                self.valuetype_id = int(valuetype_id)
            else:
                raise Exception("Invalid Value Type Class")

            try:
                if self.valuetype_class == "SCALAR":
                    self.valuetype = server_configs_res.scalar_value_types[self.valuetype_id]
                    self.default_value = self.valuetype.default_value
                elif valuetype_class == "ENUM":
                    self.valuetype = server_configs_res.enum_value_types[self.valuetype_id]
                    self.default_value = self.valuetype.default_value
            except KeyError:
                raise Exception("Invalid Value Type ID")

        except (ValueError, TypeError):
            raise Exception("Invalid values on scalar value type arguments")

    def get_info(self):
        """
            This method returns a dictionary with all the information
            correspondent to a given Property Type.
        """
        return {"id": self.id, "name": self.name, "access_mode": self.accessmode,\
                "value_type_class": self.valuetype_class, "value_type_id":self.valuetype_id}

    def validate(self, value):
        """
            This method check if a given value is valid for a given
            Property Type
        """
        return self.valuetype.validate(value)
#
#### VALUE TYPES
# Scalar Value Type
class ScalarValueType(object):
    """
        This is the Scalar Value Type Configuration class.
        Each object of this class represents a Scalar Value Type that
        the properties of the devices connected/used in this Home Server
        can have.
    """
    def __init__(self, scalar_id, scalar_name, units,\
                    min_value, max_value, scalar_step, default_value):
        try:
            self.id = int(scalar_id)
            self.name = str(scalar_name)
            self.units = str(units)
            self.min_value = float(min_value)

            if float(max_value) < float(min_value):
                raise Exception("Invalid Max Value")
            else:
                self.max_value = float(max_value)

            if (float(scalar_step) < 0) or (float(scalar_step) > float(max_value)):
                raise Exception("Invalid Step Value")
            else:
                self.step = float(scalar_step)

            if (float(default_value) < float(min_value)) or\
                                (float(default_value) > float(max_value)):
                raise Exception("Invalid Default Value")
            else:
                self.default_value = float(default_value)
        except (ValueError, TypeError):
            raise Exception("Invalid values on scalar value type arguments")
    
    def get_info(self):
        """
            This method returns a dictionary with all the information
            correspondent to a given Scalar Value Type.
        """
        return {"id": self.id, "name": self.name, "max_value": self.max_value,\
                "min_value": self.min_value, "step":self.step, "units":self.units,\
                "default_value":self.default_value}

    def validate(self, value):
        """
            This method check if a given value is valid for
            a given type of Scalar Value. 
        """
        try:
            value = float(value)
            if (value >= self.min_value) and (value <= self.max_value):
                check = (value - self.min_value) / self.step
                if check.is_integer():
                    return True
        except:
            pass

        return False
#
# Enum Value Type
class EnumValueType(object):
    """
        This is the Enumerated Value Type Configuration class.
        Each object of this class represents a Enumerated Value Type that
        the properties of the devices connected/used in this Home Server
        can have.
    """
    def __init__(self, enum_id, enum_name, enum_values, default_value):

        try:
            self.id = int(enum_id)
            self.name = str(enum_name)
            self.choices = dict(enum_values)
            if str(default_value) not in enum_values.keys():
                raise Exception("Invalid Default Value")

            self.default_value = str(default_value)

        except (ValueError, TypeError):
            raise Exception("Invalid values on enum value type arguments")

    def get_info(self):
        """
            This method returns a dictionary with all the information
            correspondent to a given Enumerated Value Type.
        """
        return {"id": self.id, "name": self.name,\
                "choices": self.choices, "default_value": self.default_value}

    def validate(self, value):
        """
            This method check if a given value is valid for
            a given type of Enumerated Value. 
        """
        if value in self.choices.keys():
            return True
        else:
            return False
#
#
#
### CONFIGS ENDPOINT
class HomeServerConfigs(Resource):
    """
        This is the Home Server Configurations CoAP resource.
        It represents the endpoint (URI) where all the home server
        configurations are stored and can be fetched and/or updated.
    """
    def __init__(self, server):

        super(HomeServerConfigs, self).__init__("HomeServerConfigs", server, visible=True,\
                                             observable=True, allow_children=False)

        self.server = server
        self.root_uri = "/configs"

        self.scalar_value_types = {}
        self.enum_value_types = {}
        self.load_value_types_from_file()

        self.property_types = {}
        self.load_property_types_from_file()

        self.device_types = {}
        self.load_device_types_from_file()

        self.server.add_resource(self.root_uri, self)

        self.res_content_type = "application/json"
        self.payload = self.get_payload()

        self.resource_type = "HomeServerConfigurations"
        self.interface_type = "if1"

    def get_info(self):
        """
            This method returns a dictionary with all the configurations
            present on this CoAP resource
        """
        return self.get_all_configs()

    def get_json(self):
        """
            This method returns a JSON representation with all the
            configurations present on this CoAP resource.
        """
        return json.dumps(self.get_info())

    def get_payload(self):
        """
            This method returns a valid CoAPthon payload representation
            with all the configurations present on this CoAP resource.
        """
        return (defines.Content_types[self.res_content_type], self.get_json())

    def load_device_types_from_file(self):
        """
            This is an auxiliary method that loads to the resource (memory) all
            the Device Type Configurations from their correspondent configuration
            file, pointed by 'settings.DEVICE_TYPES_CONFIG_FILE'.
        """
        try:
            fp = open(str(settings.DEVICE_TYPES_CONFIG_FILE), "r")

            data = json.load(fp)
            logger.info("Loading "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" file...")

            try:
                for ele in data["DEVICE_TYPES"]:
                    id = int(ele["id"])
                    name = str(ele["name"])
                    if not isinstance(ele["properties"], list):
                        raise ValueError
                    else:
                        properties = ele["properties"]

                    self.device_types[int(id)] = DeviceType(self, id, name, properties)
            except KeyError as err:
                logger.error(str(err)+" not found on device type description")
            except ValueError:
                logger.error("Invalid values on device type description")

            fp.close()
        except:
            logger.info("FILE: "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" not found")
    
    def load_property_types_from_file(self):
        """
            This is an auxiliary method that loads to the resource (memory) all
            the Property Type Configurations from their correspondent configuration
            file, pointed by 'settings.PROPERTY_TYPES_CONFIG_FILE'.
        """
        try:
            fp = open(str(settings.PROPERTY_TYPES_CONFIG_FILE), "r")

            data = json.load(fp)
            logger.info("Loading "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" file...")

            try:
                for ele in data["PROPERTY_TYPES"]:
                    id = int(ele["id"])
                    name = str(ele["name"])
                    access_mode = str(ele["access_mode"])
                    value_type = str(ele["value_type_class"])
                    value_type_id = int(ele["value_type_id"])

                    self.property_types[int(id)] = PropertyType(self, id, name, access_mode,\
                                                                     value_type, value_type_id)
            except KeyError as err:
                logger.error(str(err)+" not found on property type description")
            except ValueError:
                logger.error("Invalid values on property type description")

            fp.close()
        except:
            logger.info("FILE: "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" not found")

    def load_value_types_from_file(self):
        """
            This is an auxiliary method that loads to the resource (memory) all
            the Value Types Configurations (Scalar and Enumerated Types) from
            their correspondent configuration file, pointed by
            'settings.DEVICE_TYPES_CONFIG_FILE'.
        """
        try:
            fp = open(str(settings.VALUE_TYPES_CONFIG_FILE), "r")

            data = json.load(fp)
            logger.info("Loading "+str(settings.VALUE_TYPES_CONFIG_FILE)+" file...")
            try:
                for ele in data["SCALAR_TYPES"]:
                    id = int(ele["id"])
                    name = str(ele["name"])
                    unit = str(ele["units"])
                    min_val = float(ele["min_value"])
                    max_val = float(ele["max_value"])
                    step = float(ele["step"])
                    deflt = float(ele["default_value"])

                    self.scalar_value_types[int(id)] = ScalarValueType(id, name, unit, min_val,\
                                                                        max_val, step, deflt)
            except KeyError as err:
                logger.error(str(err)+" not found on scalar type description")
            except ValueError:
                logger.error("Invalid values on scalar value type description")

            try:
                for ele in data["ENUM_TYPES"]:
                    id = int(ele["id"])
                    name = str(ele["name"])
                    if not isinstance(ele["choices"], dict):
                        raise ValueError
                    else:
                        enum = ele["choices"]

                    deflt = str(ele["default_value"])

                    self.enum_value_types[int(id)] = EnumValueType(id, name, enum, deflt)

            except KeyError as err:
                logger.error(str(err)+" not found on enum type description")
            except ValueError:
                logger.error("Invalid values on enum value type description")

            fp.close()
        except:
            logger.info("FILE: "+str(settings.VALUE_TYPES_CONFIG_FILE)+" not found")

    def save_device_types_to_file(self):
        """
            This is an auxiliary method that saves to the correspondent configuration
            file, pointed by 'settings.DEVICE_TYPES_CONFIG_FILE', all
            the Device Type Configurations present on this resource.
        """
        try:
            fp = open(str(settings.DEVICE_TYPES_CONFIG_FILE), "w")

            data = self.get_all_device_types()

            logger.info("Saving "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" file...")
            json.dump(data, fp)
            fp.close()

            logger.info(str(settings.DEVICE_TYPES_CONFIG_FILE)+" file changes saved.")
        except:
            logger.info("FILE: "+str(settings.DEVICE_TYPES_CONFIG_FILE)+" not found")
    
    def save_property_types_to_file(self):
        """
            This is an auxiliary method that saves to the correspondent configuration
            file, pointed by 'settings.PROPERTY_TYPES_CONFIG_FILE', all
            the Property Type Configurations present on this resource.
        """
        try:
            fp = open(str(settings.PROPERTY_TYPES_CONFIG_FILE), "w")

            data = self.get_all_property_types()

            logger.info("Saving "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" file...")
            json.dump(data, fp)
            fp.close()

            logger.info(str(settings.PROPERTY_TYPES_CONFIG_FILE)+" file changes saved.")
        except:
            logger.info("FILE: "+str(settings.PROPERTY_TYPES_CONFIG_FILE)+" not found")
    
    def save_value_types_to_file(self):
        """
            This is an auxiliary method that saves to the correspondent configuration
            file, pointed by 'settings.VALUE_TYPES_CONFIG_FILE', all
            the Value Types Configurations (Scalar and Enumerated Types) present on
            this resource.
        """
        try:
            fp = open(str(settings.VALUE_TYPES_CONFIG_FILE), "w")

            data = self.get_all_value_types()["VALUE_TYPES"]

            logger.info("Saving "+str(settings.VALUE_TYPES_CONFIG_FILE)+" file...")
            json.dump(data, fp)
            fp.close()

            logger.info(str(settings.VALUE_TYPES_CONFIG_FILE)+" file changes saved.")
        except:
            logger.info("FILE: "+str(settings.VALUE_TYPES_CONFIG_FILE)+" not found")

    def validate_device_type(self, type_id):
        """
            This method checks if a given Device Type is valid on this
            Home Server, taking into account all of its configurations
        """
        try:
            if self.device_types[int(type_id)]:
                return True
            else:
                return False
        except:
            return False

    def get_all_configs(self):
        """
            This method returns a dictionary with all the configurations
            present on this CoAP resource
        """
        data = {}
        data["DEVICE_TYPES"] = self.get_all_device_types()["DEVICE_TYPES"]
        data["PROPERTY_TYPES"] = self.get_all_property_types()["PROPERTY_TYPES"]
        data["VALUE_TYPES"] = self.get_all_value_types()["VALUE_TYPES"]
        return data

    def get_all_device_types(self):
        """
            This method returns a dictionary with all the Device Type
            configurations present on this CoAP resource
        """
        data = {"DEVICE_TYPES":[]}
        for dev in self.device_types.itervalues():
            data["DEVICE_TYPES"].append(dev.get_info())
        return data

    def get_all_property_types(self):
        """
            This method returns a dictionary with all the Property Type
            configurations present on this CoAP resource
        """
        data = {"PROPERTY_TYPES":[]}
        for prop in self.property_types.itervalues():
            data["PROPERTY_TYPES"].append(prop.get_info())
        return data

    def get_all_value_types(self):
        """
            This method returns a dictionary with all the Value Type
            configurations (Scalar and Enumerated Value Types) present
            on this CoAP resource
        """
        data = {"VALUE_TYPES":{}}
        data["VALUE_TYPES"]["SCALAR_TYPES"] = self.get_all_scalars()["SCALAR_TYPES"]
        data["VALUE_TYPES"]["ENUM_TYPES"] = self.get_all_enums()["ENUM_TYPES"]
        return data

    def get_all_scalars(self):
        """
            This method returns a dictionary with all the Scalar Value Type
            configurations present on this CoAP resource
        """
        data = {"SCALAR_TYPES":[]}
        for scalar in self.scalar_value_types.itervalues():
            data["SCALAR_TYPES"].append(scalar.get_info())
        return data

    def get_all_enums(self):
        """
            This method returns a dictionary with all the Enumerated Value Type
            configurations present on this CoAP resource
        """
        data = {"ENUM_TYPES":[]}
        for enum in self.enum_value_types.itervalues():
            data["ENUM_TYPES"].append(enum.get_info())
        return data

    def update_server_configs(self, new_configs, c_type):
        """
            This method adds new and/or updates the configurations present
            on this CoAP resource.
            The first argument (new_configs) must be a list of configurations that
            must have all the configurations that we want on the home server, for a
            specific type, which is specified by the second argument (c_type).
            c_type must be one of: DEVICE_TYPES, PROPERTY_TYPES, SCALAR_TYPES
            or ENUM_TYPES, specifiyng which type of configuration we are updating.

            Ex: if the server already has Device Type 1 and 2,
            and we want to add the Device Type 3, the list to be given must have 3
            Device Type JSON objects, each one representing the Device Type 1, 2 and
            3 respectively. (in this example c_type must be DEVICE_TYPES)

            The same logic should be applied to the deletion of configurations (ex:
            if we have already Property Type 1, 2 and 3, and we want to delete Property
            Type 2 the list to provide must have the JSON object representations of
            Property Type 1 and 3). (in this example c_type must be PROPERTY_TYPES)

            The update of configurations must be done changing all the configurations
            that should be updated and give the full list of configurations, now with
            the updated ones, but applying the same logic as the examples before (always
            specifying which type of configuration we are updating on c_type argument).
        """
        try:
            configs = new_configs[c_type]
        except:
            raise AppError(defines.Codes.BAD_REQUEST,\
                        "Update "+str(c_type)+" Data bad formated")

        if isinstance(configs, list):
            try:
                data = {}
                if c_type == "SCALAR_TYPES":
                    for ele in configs:
                        id = int(ele["id"])
                        name = str(ele["name"])
                        unit = str(ele["units"])
                        min_val = float(ele["min_value"])
                        max_val = float(ele["max_value"])
                        step = float(ele["step"])
                        deflt = float(ele["default_value"])

                        data[int(id)] = ScalarValueType(id, name, unit, min_val,\
                                                                max_val, step, deflt)

                    self.scalar_value_types.clear()
                    self.scalar_value_types = data
                    self.save_value_types_to_file()

                if c_type == "ENUM_TYPES":
                    for ele in configs:
                        id = int(ele["id"])
                        name = str(ele["name"])
                        if not isinstance(ele["choices"], dict):
                            raise ValueError
                        else:
                            enum = ele["choices"]

                        deflt = str(ele["default_value"])

                        data[int(id)] = EnumValueType(id, name, enum, deflt)

                    self.enum_value_types.clear()
                    self.enum_value_types = data
                    self.save_value_types_to_file()

                if c_type == "PROPERTY_TYPES":
                    for ele in configs:
                        id = int(ele["id"])
                        name = str(ele["name"])
                        access_mode = str(ele["access_mode"])
                        value_type = str(ele["value_type_class"])
                        value_type_id = int(ele["value_type_id"])

                        data[int(id)] = PropertyType(self, id, name, access_mode,\
                                                                        value_type, value_type_id)

                    self.property_types.clear()
                    self.property_types = data
                    self.save_property_types_to_file()

                if c_type == "DEVICE_TYPES":
                    for ele in configs:
                        id = int(ele["id"])
                        name = str(ele["name"])
                        if not isinstance(ele["properties"], list):
                            raise ValueError
                        else:
                            properties = ele["properties"]

                        data[int(id)] = DeviceType(self, id, name, properties)

                    self.device_types.clear()
                    self.device_types = data
                    self.save_device_types_to_file()
            except:
                raise AppError(defines.Codes.BAD_REQUEST,\
                            "List of "+str(c_type)+" improperly formated")
        else:
            raise AppError(defines.Codes.BAD_REQUEST,\
                            "Request body should be a json element with a key "+str(c_type)+" and a list of "+str(c_type)+" as value")
    #
    ### COAP METHODS
    def render_GET(self, request):
        self.payload = self.get_payload()
        return self

    def render_PUT(self, request):
        if request.content_type is defines.Content_types.get("application/json"):
            try:
                query = request.uri_query
                aux = [query]
                d = dict(s.split("=") for s in aux)
                c_type = d["type"]
            except:
                return error(defines.Codes.BAD_REQUEST,\
                        "Request query must specify a type of the config to update")

            try:
                body = json.loads(request.payload)
            except:
                logger.error("Request payload not json")
                return error(defines.Codes.BAD_REQUEST, "Body content not properly json formated")

            try:
                self.update_server_configs(body, c_type)

                self.payload = self.get_payload()
                return status(defines.Codes.CHANGED, self)
            except AppError as e:
                return error(e.code, e.msg)

import json
import settings
import logging.config
logger = logging.getLogger(__name__)

# class valuetypes:
SCALAR = "SCALAR"
ENUM = "ENUM"
ARRAY = "ARRAY"

# Scalar Value Type
class ScalarValueType:
    def __init__(self, scalar_id, name, units, min_value, max_value, step, default_value):
        self.id = scalar_id
        self.name = name
        self.units = units
        self.min_value = min_value

        if max_value < min_value:
            raise Exception("Invalid Max Value")
        else:
            self.max_value = max_value

        if (step < 0) or (step < min_value) or (step > max_value):
            raise Exception("Invalid Step Value")
        else:
            self.step = step

        if (default_value < min_value) or (default_value > max_value):
            raise Exception("Invalid Default Value")
        else:
            self.default_value = default_value

    def validate(self, value):
        try:
            value = float(value)
            if (value >= self.min_value) and (value <= self.max_value):
                check = (value - self.min_value) / self.step
                if check.is_integer():
                    return True
        except:
            pass

        return False

# Enum Value Type
class EnumValueType:
    def __init__(self, enum_id, name, enum, default_value):
        self.id = enum_id
        self.name = name
        self.enum = enum

        if default_value not in enum.keys():
            raise Exception("Invalid Default Value")

        self.default_value = default_value

    def validate(self, value):
        if value in self.enum.keys():
            return True
        else:
            return False

# Array Value Type
# class ArrayValueType:
#     def __init__(self, array_id, name, max_len, default_value):
#         self.id = array_id
#         self.name = name
#         self.max_len = max_len

#         if (default_value is not None) and (len(str(default_value)) > max_len):
#             raise Exception("Invalid Default Value")

#         self.default_value = default_value

#     def validate(self, value):
#         if len(value) < self.max_len:
#             return True
#         else:
#             return False

SCALAR_VALUE_TYPES = {'0': ScalarValueType(0, "Default_ScalarValueType", "empty", 0, 100, 1, 0)}

ENUM_VALUE_TYPES = {'0': EnumValueType(0, "Default_EnumValueType",\
                                        {"default_key":"default_value"}, "default_key")}

# ARRAY_VALUE_TYPES = {'0': ArrayValueType(0, "Default_ArrayValueType", 15, "Default_value")}

try:
    f = open(settings.VALUE_TYPES_CONFIG_FILE, "r")

    file = json.load(f)
    logger.info("Loading valuetypes.json file...")

    for ele in file["SCALAR_TYPES"]:
        id = ele["id"]
        name = ele["name"]
        unit = ele["units"]
        min_val = ele["min_value"]
        max_val = ele["max_value"]
        step = ele["step"]
        deflt = ele["default_value"]

        SCALAR_VALUE_TYPES[str(id)] = ScalarValueType(id, name, unit, min_val, max_val, step, deflt)

    for ele in file["ENUM_TYPES"]:
        id = ele["id"]
        name = ele["name"]
        enum = ele["choices"]
        deflt = ele["default_value"]

        ENUM_VALUE_TYPES[str(id)] = EnumValueType(id, name, enum, deflt)

    # for ele in file["ARRAY_TYPES"]:
    #     id = ele["id"]
    #     name = ele["name"]
    #     max_len = ele["max_len"]
    #     deflt = ele["default_value"]

    #     ARRAY_VALUE_TYPES[str(id)] = ArrayValueType(id, name, max_len, deflt)

    f.close()
except Exception as e:
    logger.info("FILE: " + e.message)


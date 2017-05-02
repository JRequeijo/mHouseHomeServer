import json
from coapthon import defines
import socket

class AppCoAPError(Exception):
    def __init__(self, code, msg=None):
        self.code = int(defines.CoAP_HTTP[defines.Codes.LIST[code].name])
        if msg is None:
            self.msg = defines.Codes.LIST[code].name
        else:
            self.msg = msg

    def __str__(self):
        return repr(self.code, self.msg)

class AppHTTPError(Exception):
    def __init__(self, code, msg=None):
        self.msg = None
        for key in defines.CoAP_HTTP:
            if int(defines.CoAP_HTTP[key]) == int(code):
                self.msg = key
        if self.msg is not None:
            for key in defines.Codes.LIST:
                if defines.Codes.LIST[key].name == self.msg:
                    self.code = (int(key), self.msg)

        self.msg = msg

    def __str__(self):
        return repr(self.code, self.msg)

class AppError(Exception):
    def __init__(self, code, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self):
        return repr(self.code, self.msg)

def error(error, info):     
    payload = json.dumps({"error_code": code_convert(error[0]),\
                            "status_line": error[1], "error_msg": info})

    return (error[0], (defines.Content_types["application/json"], payload))

def status(code, payload):
    return (code[0], payload)

def code_convert(code):
    ctype = int(format(code, "#010b")[2:5], 2)
    code = int(format(code, "#010b")[5:], 2)

    aux = str(ctype) + "." + str(code).zfill(2)
    return aux

def validate_IPv4(addr):
    if isinstance(addr, basestring):
        arr = addr.split('.')
        if len(arr) != 4:
            return False
        for num in arr:
            if not num.isdigit():
                return False
            i = int(num)
            if i < 0 or i > 255:
                return False
        return True
    else:
        return False

def get_my_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("coap.technology", 80))
    myip = sock.getsockname()[0]
    sock.close()
    return myip

def check_on_body(body, keys):
    if isinstance(body, dict):
        for k in keys:
            if not k in body.keys():
                raise AppError(defines.Codes.BAD_REQUEST,\
                                "Request json body does not contain field ("+k+")")
    else:
        for k in keys:
            if not k in body:
                raise AppError(defines.Codes.BAD_REQUEST,\
                                "Request json body does not contain field ("+k+")")

def CoAP2HTTP_code(code):
    phrase = defines.Codes.LIST[code].name
    num = defines.CoAP_HTTP[phrase]
    num = int(num)

    return (num, phrase)

def HTTP2CoAP_code(code):
    for phrase in defines.CoAP_HTTP.keys():
        if int(defines.CoAP_HTTP[phrase]) == int(code):
            for num in defines.Codes.LIST.keys():
                if defines.Codes.LIST[num].name == phrase:
                    return (num, phrase)
            
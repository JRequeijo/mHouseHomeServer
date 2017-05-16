"""
    This is the utilities file for the HomeServer.
    Here are help/utility functions that are used overall the HomeServer
"""
import json
import socket

from coapthon import defines

__author__ = "Jose Requeijo Dias"

class AppError(Exception):
    """
        This represents an Application Exception/Error.
        It always receive an Error Code and an optionaly customized message.
    """
    def __init__(self, code, msg=None):
        super(AppError, self).__init__()
        self.code = code
        self.msg = msg

    def __str__(self):
        return (self.code, self.msg)

class AppCoAPError(AppError):
    """
        This represents an Application CoAP Exception/Error.
        It always receive a CoAP Error Code which is tranformed into the correspondent
        HTTP Error Code, and an optionaly customized message.
        When the message is not customized, it assumes the default message for the given
        error code.
    """
    def __init__(self, code, msg=None):
        super(AppCoAPError, self).__init__(code, msg)
        (self.code, self.msg) = coap2http_code(int(code))
        if msg is not None:
            self.msg = msg

class AppHTTPError(AppError):
    """
        This represents an Application HTTP Exception/Error.
        It always receive a HTTP Error Code which is tranformed into the correspondent
        CoAP Error Code, and an optionaly customized message.
        When the message is not customized, it assumes the default message for the given
        error code.
    """
    def __init__(self, code, msg=None):
        super(AppHTTPError, self).__init__(code, msg)
        (self.code, self.msg) = http2coap_code(int(code))
        if msg is not None:
            self.msg = msg

def error(error_tup, info):
    """
        This function returns a RESTful JSON error representation.
        It always receive a tuple with an error code and a status line, and also
        some info about what happened to raise this error.
        It returns a tuple with the error code and a sub-tuple specifying that
        the content format is JSON and then the error JSON payload
    """
    payload = json.dumps({"error_code": code_convert(error_tup[0]),\
                            "status_line": error_tup[1], "error_msg": info})

    return (error_tup[0], (defines.Content_types["application/json"], payload))

def status(code, payload):
    """
        This function returns a RESTful JSON status representation.
        It always receive a tuple with a code and a status line, and also
        the payload to return
    """
    return (code[0], payload)

def code_convert(code):
    """
        This function converts CoAP Integer codes into its string
        representation form. Ex: HTTP Code 400 BAD REQUEST is the integer
        128 on CoAP and its string representation for CoAP is 4.00 . This
        function converts 128 to 4.00 in this case.
    """
    ctype = int(format(code, "#010b")[2:5], 2)
    code = int(format(code, "#010b")[5:], 2)

    aux = str(ctype) + "." + str(code).zfill(2)
    return aux

def validate_IPv4(addr):
    """
        This function checks if a given string is a valid IPv4 address.
    """
    if isinstance(addr, basestring):
        arr = addr.split(".")
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
    """
        This function get the local IPv4 address for the HomeServer
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("coap.technology", 80))
    myip = sock.getsockname()[0]
    sock.close()
    return myip

def check_on_body(body, keys):
    """
        This function checks if all the elements present on the list (keys)
        are also present on body. Body can be a list or a dictionary.
    """
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

def coap2http_code(code):
    """
        This function converts any CoAP code to its correspondent HTTP code
    """
    phrase = defines.Codes.LIST[code].name
    num = defines.CoAP_HTTP[phrase]
    num = int(num)

    return (num, phrase)

def http2coap_code(code):
    """
        This function converts any CoAP code to its correspondent HTTP code
    """
    for key, val in defines.CoAP_HTTP.iteritems():
        if int(val) == int(code):
            for key1, val1 in defines.Codes.LIST.iteritems():
                if val1.name == key:
                    return (key1, key)
            
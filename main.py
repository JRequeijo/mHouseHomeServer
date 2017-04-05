
from bottle import Bottle, run, request, response, abort, debug
import json
from coapthon import defines
from multiprocessing import Process
import os
import sys
import requests
import logging
import thread
from functools import wraps


from proxy.register import *
from proxy.communicator import Communicator
from server.homeserver import HomeServer
from utils import AppError
import settings

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)

logger = logging.getLogger('proxylog')

if not register():
    sys.exit()

debug(settings.DEBUG)

def log_to_logger(fn):
    '''
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    '''
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        logger.info('From: %s - %s %s %s' % (request.remote_addr,
                                        request.method,
                                        request.url,
                                        response.status))
        return actual_response
    return _log_to_logger


proxy = Bottle()
proxy.install(log_to_logger)
# backup = BackupSaver("housebackup.json", house)



comm = Communicator("192.168.1.67")

def save_server_confs(new_name):
    try:
        f = open("serverconf.json", "r")
        data = json.load(f)
        f.close()

        data["name"] = new_name
        f = open("serverconf.json", "w")
        json.dump(data, f)
        f.close()
    except Exception as err:
        logger.error(err.message)

# ################  PROXY ENDPOINTS  ##################

# ###### Server Root Endpoints########
@proxy.get('/')
@proxy.get('/info')
def get_info():
    try:
        resp = comm.get("/info", timeout=2)
    except AppError as err:
        abort(504, err.msg)

    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put('/info')
def actualize_info():
    if request.headers['content-type'] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                data["name"] = body["name"]

                resp = comm.put("/info", json.dumps(data), timeout=2)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                thread.start_new_thread(save_server_confs, (data["name"],))

                return send_response(resp.payload, resp.code)
            except KeyError as err:
                abort(400, "Field '"+err.message+"' missing on request json body")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")



# ###### Devices List Endpoints########
@proxy.get("/devices")
def get_all_devices():
    try: 
        resp = comm.get("/devices", timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.post("/devices")
def regist_device():
    if request.headers['content-type'] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                resp = comm.post("/devices", json.dumps(body), timeout=2)
            except AppError as err:
                abort(504, err.msg)
            resp = comm.get_response(resp)

            err_check = check_error_response(resp)
            if err_check is not None:
                abort(err_check[0], err_check[1])

            return send_response(resp.payload, resp.code)
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")



# ###### Single Device Endpoints########
@proxy.get("/devices/<device_id:int>")
def get_device(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id), timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.delete("/devices/<device_id:int>")
def unregist_device(device_id):
    try:
        resp = comm.delete("/devices/"+str(device_id), timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put('/devices/<device_id:int>')
def actualize_device_info(device_id):
    if request.headers['content-type'] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                data["name"] = body["name"]

                resp = comm.put("/devices/"+str(device_id), json.dumps(data), timeout=2)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                return send_response(resp.payload, resp.code)
            except KeyError as err:
                abort(400, "Field '"+err.message+"' missing on request json body")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")

# ###### States Endpoints########
@proxy.get("/devices/<device_id:int>/state")
def get_device_state(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/state", timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put("/devices/<device_id:int>/state")
def change_device_state(device_id):
    if request.headers['content-type'] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                resp = comm.put("/devices/"+str(device_id)+"/state", json.dumps(body), timeout=2)
            except AppError as err:
                abort(504, err.msg)
            resp = comm.get_response(resp)

            err_check = check_error_response(resp)
            if err_check is not None:
                abort(err_check[0], err_check[1])

            return send_response(resp.payload, resp.code)
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")


# ###### Types Endpoints########
@proxy.get("/devices/<device_id:int>/type")
def get_device_type(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/type", timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)
    
    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])
    
    return send_response(resp.payload, resp.code)


# ###### Services Endpoints########
@proxy.get("/devices/<device_id:int>/services")
def get_device_services(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/services", timeout=2)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)
    
    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])
    
    return send_response(resp.payload, resp.code)


# @proxy.post("/devices/<device_id:int>/services")
# def add_service_to_device(device_id):
#     if request.headers['content-type'] == "application/json":
#         try:
#             body = request.json
#         except:
#             abort(400, "Request body not properly json formated")
            
#         if body is not None:
#             try:
#                 data = {}
#                 data["id"] = body["id"]
#                 data["name"] = body["name"]
        
#                 resp = comm.post("/devices/"+str(device_id)+"/services", json.dumps(data))
#                 resp = comm.get_response(resp)
                
#                 err_check = check_error_response(resp)
#                 if err_check is not None:
#                     abort(err_check[0], err_check[1])
                
#                 return send_response(resp.payload, resp.code)
            
#             except KeyError as err:
#                 abort(400, "Field '"+err.message+"' missing on request json body")
#         else:
#             abort(400, "Request body formated in json is missing")
#     else:
#         abort(415, "Request body content format not json")


# @proxy.delete("/devices/<device_id:int>/services")
# def delete_service_from(device_id):
#     resp = comm.delete("/devices/"+str(device_id)+"/services")
#     resp = comm.get_response(resp)
    
#     err_check = check_error_response(resp)
#     if err_check is not None:
#         abort(err_check[0], err_check[1])
    
#     return send_response(resp.payload, resp.code)


            

# ######## Helper Functions #######

# #change to use authentication framework
# def authorize(request):
#     if (request.environ.get('REMOTE_ADDR') == get_my_ip()) and (request.headers['user-agent'] == "app-communicator"):
#         return True
#     else:
#         return False

def send_response(data, code=None):
    if code is not None:
        response.status = utils.CoAP2HTTP_code(code)[0]
    response.set_header("Content-Type", "application/json")
    return data

def check_error_response(response):
    if response.code >= defines.Codes.ERROR_LOWER_BOUND:
        code, phrase = utils.CoAP2HTTP_code(response.code)

        if response.payload is not None:
            d = json.loads(response.payload)
            return (code, d["error_msg"])
        else:
            return (code, phrase)
    else:
        return None


######### Handle Errors #############
@proxy.error(400)
@proxy.error(404)
@proxy.error(403)
@proxy.error(405)
@proxy.error(415)
@proxy.error(500)
@proxy.error(504)
def errorHandler(error):
    return send_response(json.dumps({"error_code": error.status_code, "error_msg": error.body}))


def initialize_home_server(server_confs_file_name):
    try:
        f = open(server_confs_file_name, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
        server.start()
    except:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()


####### Initialize Home Server ########
home_server_proc = Process(target=initialize_home_server, args=(settings.SERVER_CONFIG_FILE,))


home_server_proc.start()
run(proxy, host=settings.PROXY_ADDR, port=settings.PROXY_PORT, quiet=settings.QUIET)


home_server_proc.join()


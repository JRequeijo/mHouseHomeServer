
from bottle import Bottle, run, request, response, abort, debug
import json
from coapthon import defines
from multiprocessing import Process
import os
import sys
import requests

from register import *
from communicator import Communicator

# from proxy.server import Server
# from utils import AppCoAPError, AppError, get_my_ip, CoAP2HTTP_code
# from gateway.proxy.idgenerator import IDGenerator
# from gateway.proxy.config import start_house_config
# from gateway.proxy.backupsaver import BackupSaver
# from server.communicator import Communicator


if not register("serverconf.json"):
    sys.exit()

print "\n"
debug(True)

proxy = Bottle()

# backup = BackupSaver("housebackup.json", house)



comm = Communicator("192.168.1.67")

# ################  PROXY ENDPOINTS  ##################

# ###### Server Root Endpoints########
@proxy.get('/')
@proxy.get('/info')
def get_info():
    resp = comm.get("/info")
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

# @proxy.put('/info')
# def actualize_info():
#     if request.headers['content-type'] == "application/json":
#         try:
#             body = request.json
#         except:
#             abort(400, "Request body not properly json formated")
              
#         if body is not None:
#             try:
#                 data = {}
#                 data["name"] = body["name"]
          
#                 resp = comm.put("/info", json.dumps(data))
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



# ###### Devices List Endpoints########
@proxy.get("/devices")
def get_all_devices():
    resp = comm.get("/devices")
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
            resp = comm.post("/devices", json.dumps(body))
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
    resp = comm.get("/devices/"+str(device_id))
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.delete("/devices/<device_id:int>")
def unregist_device(device_id):
    resp = comm.delete("/devices/"+str(device_id))
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)


# ###### States Endpoints########
@proxy.get("/devices/<device_id:int>/state")
def get_device_state(device_id):
    resp = comm.get("/devices/"+str(device_id)+"/state")
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
            resp = comm.put("/devices/"+str(device_id)+"/state", json.dumps(body))
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
    resp = comm.get("/devices/"+str(device_id)+"/type")
    resp = comm.get_response(resp)
    
    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])
    
    return send_response(resp.payload, resp.code)


# ###### Services Endpoints########
@proxy.get("/devices/<device_id:int>/services")
def get_device_services(device_id):
    resp = comm.get("/devices/"+str(device_id)+"/services")
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
@proxy.error(405)
@proxy.error(415)
@proxy.error(500)
def errorHandler(error):
    return send_response(json.dumps({"error_code": error.status_code, "error_msg": error.body}))




# # def init_reverse_communicator():
# #     print "Reverse Communicator Initialized on process "+str(os.getpid())
# #     serv = ReverseCommunicator()
# #     serv.start()


# ####### Initialize Gateway ########
# #rev_comm_proc = Process(target=init_reverse_communicator)


# #rev_comm_proc.start()
run(proxy, host=utils.get_my_ip(), port=8080)


# #rev_comm_proc.join()

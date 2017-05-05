# #!/usr/bin/env python

# import json
# import settings
# import logging.config
# logger = logging.getLogger(__name__)

# class Service:    
#     def __init__(self, service_id, name, core_service_ref=None):
#         self.id = service_id
#         self.name = name

#         if core_service_ref == None:
#             self.core_service_ref = core_service_ref
#         else:
#             try:
#                 aux = int(core_service_ref)
#                 self.core_service_ref = aux
#             except:
#                 self.core_service_ref = None

#     def get_info(self):
#         return {"id": self.id, "name": self.name, "core_service_ref":self.core_service_ref}

# # SERVICES = {0: Service(0, "Undefined Service")}

# def validate_services(service_ids):
#     for s in service_ids:
#         try:
#             if not SERVICES[int(s)]:
#                 return False
#         except:
#             return False

#     return True

# def get_all_services():
#     data = {"SERVICES":[]}
#     for s in SERVICES.itervalues():
#         data["SERVICES"].append(s.get_info())
#     return data

# def add_service(service_id, service_name, core_service_ref):
#     SERVICES[int(service_id)] = Service(service_id, service_name, core_service_ref)

#     # try:
#     #     fp = open(str(settings.SERVICES_CONFIG_FILE), "w")

#     #     data = get_all_services()

#     #     json.dump(data, fp)

#     #     fp.close()
#     # except:
#     #     logger.info("FILE: "+str(settings.SERVICES_CONFIG_FILE)+" not found")

# def load_services_from_file():
#     try:
#         fp = open(str(settings.SERVICES_CONFIG_FILE), "r")

#         data = json.load(fp)
#         logger.info("Loading "+str(settings.SERVICES_CONFIG_FILE)+" file...")

#         data = {}
#         for ele in data["SERVICES"]:
#             id = ele["id"]
#             name = ele["name"]
#             core_service_ref = ele["core_service_ref"]
#             data[int(id)] = Service(id, name, core_service_ref)

#         fp.close()

#         return data
#     except:
#         logger.info("FILE: "+str(settings.SERVICES_CONFIG_FILE)+" not found")

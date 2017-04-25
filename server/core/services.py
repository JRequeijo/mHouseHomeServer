#!/usr/bin/env python

import json
import settings
import logging.config
logger = logging.getLogger(__name__)

class Service:    
    def __init__(self, service_id, name):
        self.id = service_id
        self.name = name

    def get_info(self):
        return {"id": self.id, "name": self.name}

SERVICES = {0: Service(0, "Undefined Service")}

def validate_services(service_ids):
    for s in service_ids:
        try:
            if not SERVICES[int(s)]:
                return False
        except:
            return False

    return True

# def add_service(new_service):
#         SERVICES[str(new_service.id)] = new_service

try:
    fp = open(str(settings.SERVICES_CONFIG_FILE), "r")

    data = json.load(fp)
    logger.info("Loading "+str(settings.SERVICES_CONFIG_FILE)+" file...")

    for ele in data["SERVICES"]:
        id = ele["id"]
        name = ele["name"]

        SERVICES[int(id)] = Service(id, name)

    fp.close()
except:
    logger.info("FILE: "+str(settings.SERVICES_CONFIG_FILE)+" not found")

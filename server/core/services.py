#!/usr/bin/env python

import json

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
    f = open("services.json", "r")

    file = json.load(f)
    print "Loading services.json file..."

    for ele in file["SERVICES"]:
        id = ele["id"]
        name = ele["name"]

        SERVICES[int(id)] = Service(id, name)

    f.close()
except:
    print "FILE: 'services.json' not found"

import json
import sys

class IDGenerator:
    def __init__(self, server):
        self.server = server

    def current_device_id(self):
        keys = self.server.devices.devices.keys()
        return max(keys) if keys else 0

    def new_device_id(self):
        return self.current_device_id()+1
        
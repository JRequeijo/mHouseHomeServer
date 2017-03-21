import json
import sys

class IDGenerator:
    def __init__(self, server):
        self.server = server

    def current_device_id(self):
        return max(self.server.devices.keys())

    def new_device_id(self):
        return self.current_device_id()+1
"""
    This is the id generator file.
    Here is specified the class that generates all the devices local ids
    for the HomeServer.
"""

__author__ = "Jose Requeijo Dias"

class IDGenerator(object):
    """
        This is the id generator class.
        It generates all the devices local device ids for the HomeServer.
    """
    def __init__(self, server):
        self.server = server

    def current_device_id(self):
        """
            This method calculates and returns the current device id.
        """
        keys = self.server.devices.devices.keys()
        return max(keys) if keys else 0

    def new_device_id(self):
        """
            This method gives a new device id, i.e. it gives the current
            device id plus 1. The current device id is automatically updated
            when the device with a new id is created.
        """
        return self.current_device_id()+1
        
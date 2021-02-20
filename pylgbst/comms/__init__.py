"""
This package holds communication aspects
"""
import binascii
#import json
#import logging
#import socket
#import traceback
#from abc import abstractmethod
from binascii import unhexlify
#from threading import Thread

from pylgbst.messages import MsgHubAction
from pylgbst.utilities import str2hex

#log = logging.getLogger('comms')

MOVE_HUB_HW_UUID_SERV = '00001623-1212-efde-1623-785feabcd123'
MOVE_HUB_HW_UUID_CHAR = '00001624-1212-efde-1623-785feabcd123'
ENABLE_NOTIFICATIONS_HANDLE = 0x000f
ENABLE_NOTIFICATIONS_VALUE = b'\x01\x00'

MOVE_HUB_HARDWARE_HANDLE = 0x0E


class Connection(object):
    def connect(self, hub_mac=None):
        pass

    #@abstractmethod
    def is_alive(self):
        pass

    def disconnect(self):
        pass

    #@abstractmethod
    def write(self, handle, data):
        pass

    #@abstractmethod
    def set_notify_handler(self, handler):
        pass

    def enable_notifications(self):
        pass

    def _is_device_matched(self, address, dev_name, hub_mac, find_name):
        assert hub_mac or find_name, 'You have to provide either hub_mac or hub_name in connection options'
        print("Checking device: %s, MAC: %s", dev_name, address)
        matched = False
        if address != "00:00:00:00:00:00":
            if hub_mac:
                if hub_mac.lower() == address.lower():
                    matched = True
            elif dev_name == find_name:
                matched = True

            if matched:
                print("Found %s at %s", dev_name, address)

        return matched

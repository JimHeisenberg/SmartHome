import sys
import os
import json
import socket
import time
import datetime
import hashlib
import requests
import threading
import ConnectionManagerLocal
import RPi.GPIO as GPIO

class Light(ConnectionManagerLocal.DeviceHandle):
    def __init__(self, connectionSocket: socket.socket, IPAddress,
                 deviceManager=None, deviceID=None, deviceIsOn=None, deviceName=None, deviceType=None):
        super().__init__(connectionSocket, IPAddress, deviceManager, deviceID,
                         deviceIsOn, deviceName, deviceType)
        self.initLight()

    def doChangeStatus(self, turnDeviceOn=None):
        if turnDeviceOn is None:
            return None
        self.DeviceIsOn = turnDeviceOn
        try:
            self.initLight()
            if turnDeviceOn:
                GPIO.output([3, 5, 7], 1)
                # os.system("uhubctl -l 1 -a 1")
            else:
                GPIO.output([3, 5, 7], 0)
                # os.system("uhubctl -l 1 -a 0")
        except Exception as e:
            print(e)
        return True

    def initLight(self):
        if not hasattr(self, "light"):
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup([3, 5, 7], GPIO.OUT)
            except Exception as e:
                print(e)
            self.light = True
        return None

    def __del__(self):
        super().__del__()
        try:
            GPIO.cleanup()
        except Exception as e:
            print(e)
        return None


if __name__ == "__main__":
    l = Light(socket.socket(), None)
    l.doChangeStatus(True)
    time.sleep(10)
    l.doChangeStatus(False)

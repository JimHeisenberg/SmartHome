from ConnectionManagerLocal import ConnectionManagerLocal
from alarm import Alarm
from assistant import Assistant, VoiceRecognizer
from light import Light


# global variable
BACKEND_IP = "124.223.65.144"
BACKEND_PORT = 54321
BACKEND_URL = "http://"+BACKEND_IP+":12345"
# end of global variable


if __name__ == "__main__":
    cm = ConnectionManagerLocal(BACKEND_URL)
    with cm as deviceManager:
        s1 = deviceManager._createLocalSocket(BACKEND_IP, 54321)
        light = Light(s1, None, deviceManager, 1, True)
        light.send({"DeviceID": 1, "DeviceIsOn": True})
        light.tryChangeStatus(True)
        deviceManager.addDeviceHandle(light)

        s3 = deviceManager._createLocalSocket(BACKEND_IP, 54321)
        alarm = Alarm(s3, None, deviceManager, 3, True)
        alarm.send({"DeviceID": 3, "DeviceIsOn": True})
        deviceManager.addDeviceHandle(alarm)

        s5 = deviceManager._createLocalSocket(BACKEND_IP, 54321)
        assistant = Assistant(s5, None, deviceManager, 5, True)
        assistant.send({"DeviceID": 5, "DeviceIsOn": True})
        deviceManager.addDeviceHandle(assistant)
    cm.start()

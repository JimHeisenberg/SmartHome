import sys
import os
import json
import socket
import time
import datetime
import hashlib
import requests
import threading
import base64
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models
import ConnectionManagerLocal


class Assistant(ConnectionManagerLocal.DeviceHandle):
    def __init__(self, connectionSocket: socket.socket, IPAddress,
                 deviceManager=None, deviceID=None, deviceIsOn=None, deviceName=None, deviceType=None):
        super().__init__(connectionSocket, IPAddress, deviceManager, deviceID,
                         deviceIsOn, deviceName, deviceType)
        self.initVoiceRecognize()

    def doChangeStatus(self, turnDeviceOn=None):
        if turnDeviceOn is None:
            return None
        self.DeviceIsOn = turnDeviceOn
        if turnDeviceOn:
            os.system("uhubctl -l 2 -a 1")
        else:
            os.system("uhubctl -l 2 -a 0")
        return True

    def initVoiceRecognize(self):
        if hasattr(self, "voiceRecognizer"):
            return None
        self.voiceRecognizer = VoiceRecognizer(self)
        self.voiceRecognizer.start()
        # arecord -l
        # arecord -D plughw:1 -r 8000 -c 1 -d 1 audio1.wav
        # base64.b64encode(d)


class VoiceRecognizer(threading.Thread):
    def __init__(self, assistant, configPath="./test/config.json"):
        super().__init__()
        try:
            with open(configPath, "r", encoding="UTF-8") as f:
                conf = json.load(f)
                secretId = conf.get("SecretId")
                secretKey = conf.get("SecretKey")
            cred = credential.Credential(secretId, secretKey)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "asr.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = asr_client.AsrClient(cred, "", clientProfile)
            self.lock = threading.Lock()
            self.conf = conf
            self.client = client
            self.assistant: Assistant = assistant
        except TencentCloudSDKException as err:
            print(err)

    def doRecord(self, device="plughw:1", t=5, filePath="./test/") -> str:
        try:
            timeNowStr = datetime.datetime.now().isoformat()
            timeNowStr = timeNowStr.split('.')[0].replace(":", "-")
            fileName = f"{filePath}audio-{timeNowStr}.wav"
            os.system(f"arecord -D {device} -r 8000 -c 1" +
                      f" -d {t} {fileName}")
            with open(fileName, "rb") as f:
                data = f.read()
                data = base64.b64encode(data)
                data = data.decode()
            return data
        except Exception as e:
            print(e)
            return None

    def doRecognize(self, data, query_interval=1) -> str:
        if data is None:
            return None
        try:
            client = self.client
            # recognize
            req = models.CreateRecTaskRequest()
            params = {
                "EngineModelType": "8k_zh",
                "ChannelNum": 1,
                "ResTextFormat": 0,
                "SourceType": 1,
                "Data": data
            }
            req.from_json_string(json.dumps(params))
            resp = client.CreateRecTask(req)
            print(resp.to_json_string())
            respInfo = json.loads(resp.to_json_string())
            taskId = respInfo.get("Data").get("TaskId")
            # RequestId = respInfo.get("RequestId")
            respStatus = 0
            while (respStatus != 2):
                time.sleep(query_interval)
                req = models.DescribeTaskStatusRequest()
                params = {
                    "TaskId": taskId
                }
                req.from_json_string(json.dumps(params))
                resp = client.DescribeTaskStatus(req)
                print(resp.to_json_string())
                respInfo = json.loads(resp.to_json_string())
                respStatus = respInfo.get("Data").get("Status")
            respInfo = json.loads(resp.to_json_string())
            result = respInfo.get("Data").get("Result")
            if (self.conf.get("onIns") in result):
                return True
            if (self.conf.get("offIns") in result):
                return False
        except TencentCloudSDKException as err:
            print(err)
        return None

    def doAction(self, status, deviceID=None):
        if status is None:
            return
        if deviceID is None:
            deviceID = self.conf.get("insDevID")
        deviceHandle = self.assistant.deviceManager.getDeviceHandle(deviceID)
        deviceHandle.tryChangeStatus(status)
        return None

    def doTask(self):
        data = self.doRecord(t=3)
        status = self.doRecognize(data)
        self.doAction(status)

    def run(self):
        import _thread
        while True:
            _thread.start_new_thread(self.doTask)
            time.sleep(3.5)


if __name__ == "__main__":
    a = Assistant(socket.socket(), None)
    a.doChangeStatus(True)
    time.sleep(10)
    a.doChangeStatus(False)

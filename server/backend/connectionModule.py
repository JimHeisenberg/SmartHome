import sys
import os
import json
import socket
import time
import datetime
import hashlib
import requests
import threading
from flask import Flask, current_app, render_template, request, abort
from itsdangerous import BadData, TimedJSONWebSignatureSerializer as Serializer
import backend.sqlModule as sqlModule


# global variable
HOST = "127.0.0.1"
if "GCC" in sys.version:
    HOST = "127.0.0.1"
CONNECTION_PORT = 54321
BACKEND_PORT = 12345
FRONTEND_PORT = 12345
SERVER_PORT = 12345
# file
HEARTBEAT_INTERVAL = 20  # seconds
LOG = True
# end of global variable


class DeviceHandle:
    def __init__(self, connectionSocket: socket.socket, IPAddress,
                 deviceManager=None,
                 deviceID=None, deviceIsOn=None,
                 deviceName=None, deviceType=None,
                 socketBufferSize=8124,
                 heartbeatInterval=HEARTBEAT_INTERVAL):
        self.deviceManager: DeviceManager = deviceManager
        self.socket = connectionSocket
        self.socketBufferSize = socketBufferSize
        self.IPAddress = IPAddress
        self.DeviceID = deviceID
        self.DeviceIsOn = deviceIsOn
        self.DeviceName = deviceName
        self.DeviceType = deviceType
        self.lastReceiveTime = time.time()
        self.heartbeatInterval = heartbeatInterval
        self.heartbeatSentAfterInterval = False
        self.socket.setblocking(False)

    def __del__(self):
        self.socket.close()

    def _initDeviceInfo(self, dataRecv: dict):
        self.DeviceID = dataRecv.get("DeviceID")
        self.DeviceIsOn = dataRecv.get("DeviceIsOn")
        if self.DeviceID is not None:
            try:
                mysql = self.deviceManager.mysql
                devInfo = mysql.select(
                    ["DeviceName", "DeviceType", ],
                    "DeviceTable", f"DeviceID='{self.DeviceID}'")
                if devInfo == ():
                    raise Exception(
                        f"DeviceID:{self.DeviceID} not exist in db")
                (deviceName, deviceType) = devInfo[0]
                self.DeviceName = deviceName
                self.DeviceType = deviceType
                self._initInstructionInfo(self.DeviceID)
                mysql.update({"DeviceID": self.DeviceID,
                              "DeviceIsOn": self.DeviceIsOn,
                              "DeviceIsOnline": True},
                             "DeviceTable", f"DeviceID='{self.DeviceID}'")
            except Exception as e:
                self.remove()
                print(e)
        return None

    def _initInstructionInfo(self, deviceID: int):
        self.deviceManager.instructionManager._initInstructionInfo(deviceID)
        return None

    def receive(self) -> list:  # -> list of dict
        result = list()
        dataReceived = bytes()
        try:
            # sys.byteorder = 'little'
            dataReceived += self.socket.recv(self.socketBufferSize)
            if len(dataReceived) == 0:
                # raise Exception("socket broken")
                return []
            while dataReceived[-1] != 59:  # ascii ';' == 59 and b';'[0] = 59
                dataReceived += self.socket.recv(self.socketBufferSize)
            dataReceived = dataReceived.decode()
            if LOG:
                print(f"DeviceID:{self.DeviceID}  " +
                      f"dataReceived: {dataReceived}")
            for data in dataReceived.split(';')[:-1]:
                result.append(json.loads(data))
        except BlockingIOError:
            pass
        except Exception as e:
            print(e, flush=True)
            self.remove()
        if len(result) > 0:
            self.lastReceiveTime = time.time()
        return result

    def send(self, data: dict):
        dataSend = json.dumps(data) + ';'
        if LOG:
            print(f"DeviceID:{self.DeviceID}  " +
                  f"dataSend: {dataSend}")
        success = None
        try:
            # sys.byteorder = 'little'
            self.socket.sendall(dataSend.encode())
            success = True
        except Exception as e:
            print(e, flush=True)
            success = False
        return success

    def tryChangeStatus(self, turnDeviceOn=None):
        timeNowStr = datetime.datetime.now().isoformat().split('.')[0]
        success = self.send({
            "heartbeatTime": timeNowStr,
            "turnDeviceOn": turnDeviceOn,
        })
        return success

    def onStatusChange(self, deviceIsOn: bool):
        self.DeviceIsOn = deviceIsOn
        self.deviceManager.instructionManager.onStatusChange(
            self.DeviceID, deviceIsOn)
        try:
            mysql = self.deviceManager.mysql
            mysql.update({"DeviceIsOn": deviceIsOn}, "DeviceTable",
                         f"DeviceID='{self.DeviceID}'")
        except Exception as e:
            print(e)
        return None

    def handle(self):
        """
        send format: {
            "heartbeatTime": "2022-04-30T12:34:56",
            "turnDeviceOn": True,
            "sync": False, # force device update instruction itself
        }
        recv format: {
            "heartbeatTime": "2022-04-30T12:34:56",
            "DeviceID": 1,
            "DeviceIsOn": True,
        }
        """
        dataReceivedList = self.receive()
        for data in dataReceivedList:
            # init Device Info
            if self.DeviceID is None:
                self._initDeviceInfo(data)
            # onStatusChange
            actualDeviceIsOn = data.get("DeviceIsOn")
            if (actualDeviceIsOn is not None) and (self.DeviceIsOn != actualDeviceIsOn):
                self.onStatusChange(actualDeviceIsOn)
            if data.get("heartbeatTime") is not None:
                self._heartbeat(doRespond=True)
        self._heartbeat()
        return None

    def remove(self):
        self.socket.close()
        self.deviceManager.removeDeviceHandle(deviceID=None, deviceHandle=self)
        try:
            mysql = self.deviceManager.mysql
            mysql.update({"DeviceID": self.DeviceID, "DeviceIsOnline": False},
                         "DeviceTable", f"DeviceID='{self.DeviceID}'")
        except Exception as e:
            print(e)
        print(f"device removed: DeviceID={self.DeviceID}")
        return None

    def doForceSync(self, sync=False):
        # force device update instruction itself
        timeNowStr = datetime.datetime.now().isoformat().split('.')[0]
        self.send({
            "heartbeatTime": timeNowStr,
            "sync": sync,
        })
        return None

    def _heartbeat(self, doRespond=False):
        timeDiff = time.time() - self.lastReceiveTime
        doHeartbeat = False
        if timeDiff > 2 * self.heartbeatInterval:
            if self.heartbeatSentAfterInterval:
                print(f"DeviceID={self.DeviceID} disconnected: overtime",
                      flush=True)
                self.remove()
            else:
                doHeartbeat = True
        elif timeDiff > self.heartbeatInterval:
            if self.heartbeatSentAfterInterval:
                pass
            else:
                doHeartbeat = True
        else:
            self.heartbeatSentAfterInterval = False
        if doHeartbeat:
            timeNowStr = datetime.datetime.now().isoformat().split('.')[0]
            self.send({"heartbeatTime": timeNowStr})
            self.heartbeatSentAfterInterval = True
        if doRespond:
            self.send({"heartbeatRespond": True})
        return None

    def getLastReceiveTimeISOFormat(self, cut=True):
        timeString = datetime.datetime.fromtimestamp(
            self.lastReceiveTime).isoformat()
        if (cut):
            timeString = timeString.split('.')[0]
        return timeString


class DeviceManager:
    def __init__(self, mysql: sqlModule.MYSQL, host=HOST, port=CONNECTION_PORT, maxDeviceNumber=99, ):
        self.deviceHandleList = list()
        self.socket = self._createServerSocket(host, port, maxDeviceNumber)
        self.instructionManager = InstructionManager(self)
        self.mysql: sqlModule.MYSQL = mysql

    def __del__(self):
        self.socket.close()

    def _createServerSocket(self, host, port, maxDeviceNumber) -> socket.socket:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((host, port))
        serverSocket.listen(maxDeviceNumber)
        serverSocket.setblocking(False)
        return serverSocket

    def getDeviceStatus(self, deviceID: int, deviceName=None):
        deviceStatus = None
        deviceHandle = self.getDeviceHandle(deviceID, deviceName)
        if deviceHandle is not None:
            deviceStatus = deviceHandle.DeviceIsOn
        return deviceStatus

    def tryChangeStatus(self, deviceID: int, deviceIsOn: bool) -> bool:
        deviceHandle = self.getDeviceHandle(deviceID)
        success = False
        if deviceHandle is not None:
            success = deviceHandle.tryChangeStatus(deviceIsOn)
        return success

    def addDeviceHandle(self, deviceHandle: DeviceHandle) -> bool:
        success = False
        if self.getDeviceHandle(deviceHandle.DeviceID) is None:
            self.deviceHandleList.append(deviceHandle)
            success = True
        return success

    def getDeviceHandle(self, deviceID: int, deviceName=None) -> DeviceHandle:
        deviceHandle = None
        for devHandle in self.deviceHandleList:
            if deviceName is not None:
                if deviceName == devHandle.DeviceName:
                    deviceHandle = devHandle
                    break
            else:
                if deviceID == devHandle.DeviceID:
                    deviceHandle = devHandle
                    break
        return deviceHandle

    def popDeviceHandle(self, deviceID: int, deviceName=None) -> DeviceHandle:
        deviceHandle = self.getDeviceHandle(deviceID, deviceName)
        if deviceHandle is not None:
            self.deviceHandleList.remove(deviceHandle)
        return deviceHandle

    def removeDeviceHandle(self, deviceID: int, deviceName=None, deviceHandle=None):
        if deviceHandle is None:
            deviceHandle = self.getDeviceHandle(deviceID, deviceName)
        if deviceHandle is not None:
            self.deviceHandleList.remove(deviceHandle)
        return None

    def handleAll(self):
        try:
            # receive data
            (connectionSocket, IPaddr) = self.socket.accept()
            print(f"new connection from {IPaddr}", flush=True)
            # connectionSocket.setblocking(False)
            deviceHandle = DeviceHandle(connectionSocket, IPaddr, self)
            self.addDeviceHandle(deviceHandle)
        except BlockingIOError:
            # ignore when no new connectionSocket
            pass
        current_list = self.deviceHandleList.copy()
        for devHandle in current_list:
            devHandle.handle()
        return None


class ConditionHandle:
    def __init__(self, condition: dict, instructionHandle=None):
        self.instructionHandle: InstructionHandle = instructionHandle
        self.condition = condition
        self.type = condition.get("type")
        self.conditionA = None if condition.get(
            "conditionA") is None else ConditionHandle(condition.get("conditionA"), instructionHandle)
        self.conditionB = None if condition.get(
            "conditionB") is None else ConditionHandle(condition.get("conditionB"), instructionHandle)
        self.DeviceID = condition.get("DeviceID")
        self.DeviceIsOn = condition.get("DeviceIsOn")
        self.time = None
        self.timeStr = condition.get("time")
        self.timeOperator = condition.get('timeOperator')
        self.repeat = condition.get('repeat')
        if self.timeStr is not None:
            if len(self.timeStr) == 16:
                self.time = datetime.datetime.strptime(
                    self.timeStr, "%Y-%m-%dT%H:%M")
            elif len(self.timeStr) == 19:
                self.time = datetime.datetime.strptime(
                    self.timeStr, "%Y-%m-%dT%H:%M:%S")
            else:
                self.time = datetime.datetime.strptime(
                    self.timeStr.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        if self.instructionHandle is not None and self.DeviceID is not None:
            self.instructionHandle.conditionDeviceIDSet.add(self.DeviceID)
        if self.instructionHandle is not None and self.time is not None:
            self.instructionHandle.conditionTimeSet.add(self.time)

    def handle(self, t=None) -> bool:
        result = False
        if self.type == "if":
            deviceManager = self.instructionHandle.instructionManager.deviceManager
            if deviceManager.getDeviceStatus(self.DeviceID) == self.DeviceIsOn:
                result = True
        elif self.type == "when":
            timeNow = datetime.datetime.fromtimestamp(
                int(time.time())) if t is None else t
            timeSet = self.time
            if self.repeat:
                timeNow = timeNow.time()
                timeSet = timeSet.time()
            if self.timeOperator == '=':
                result = timeNow == timeSet
            elif self.timeOperator == '<':
                result = timeNow < timeSet
            elif self.timeOperator == '>':
                result = timeNow >= timeSet
            else:
                pass
        elif self.type == "and":
            result = self.conditionA.handle() and self.conditionB.handle()
        elif self.type == "or":
            result = self.conditionA.handle() or self.conditionB.handle()
        else:
            pass
        return result

    def judge(self, t=None) -> bool:
        return self.handle(t)

    def toString(self) -> str:
        return json.dumps(self.condition)


class ActionHandle:
    def __init__(self, action: dict, instructionHandle=None):
        self.instructionHandle: InstructionHandle = instructionHandle
        self.action = action
        self.DeviceID = action.get("DeviceID")
        self.DeviceIsOn = action.get("DeviceIsOn")
        self.instructionHandle.actionDeviceID = self.DeviceID

    def handle(self):
        deviceManager = self.instructionHandle.instructionManager.deviceManager
        success = deviceManager.tryChangeStatus(self.DeviceID, self.DeviceIsOn)
        return success

    def do(self) -> bool:
        return self.handle()

    def toString(self):
        return json.dumps(self.action)


class InstructionHandle:
    def __init__(self, instruction: dict, instructionManager=None, instructionID=None, instructionIsOn=None,
                 instructionName=None, instructionMeta=None, ):
        self.instruction = instruction
        self.instructionManager: InstructionManager = instructionManager
        self.InstructionID = self.instruction.get("InstructionID")
        self.InstructionName = self.instruction.get("InstructionName")
        self.InstructionMeta = self.instruction.get("InstructionMeta")
        self.InstructionIsOn = self.instruction.get("InstructionIsOn")
        self.conditionHandle: ConditionHandle = None
        self.actionHandle: ActionHandle = None
        self.conditionDeviceIDSet = set()
        self.conditionTimeSet = set()
        self.actionDeviceID = None
        if self.InstructionMeta is not None:
            if self.InstructionMeta.get("condition") is not None:
                self.conditionHandle = ConditionHandle(
                    self.InstructionMeta.get("condition"), self)
            if self.InstructionMeta.get("action") is not None:
                self.actionHandle = ActionHandle(
                    self.InstructionMeta.get("action"), self)
        self.checkSync()

    def handle(self) -> bool:
        if self.InstructionIsOn:
            if self.conditionHandle.judge():
                return self.actionHandle.do()
        else:
            return None

    def handleTime(self, t=None) -> bool:
        if self.InstructionIsOn and len(self.conditionTimeSet) > 0:
            if self.conditionHandle.judge(t):
                return self.actionHandle.do()
        else:
            return None

    def remove(self):
        self.instructionManager.removeInstructionHandle(
            instructionID=None, instructionHandle=self)
        print(f"instruction removed: {self.instruction}")
        return None

    def tryChangeStatus(self, turnInstructionOn):
        if self.instructionIsOn != turnInstructionOn:
            self.onStatusChange(turnInstructionOn)
        return None

    def onStatusChange(self, instructionIsOn):
        self.instructionIsOn = instructionIsOn
        try:
            if instructionIsOn is not None:
                mysql = self.instructionManager.deviceManager.mysql
                mysql.update({"InstructionIsOn": instructionIsOn}, "InstructionTable",
                             f"InstructionID='{self.InstructionID}'")
        except Exception as e:
            print(e)
        return None

    def checkSync(self):
        if len(self.conditionDeviceIDSet) <= 1:
            if (len(self.conditionDeviceIDSet) == 0) or (self.actionDeviceID in self.conditionDeviceIDSet):
                deviceHandle = self.instructionManager.deviceManager.getDeviceHandle(
                    self.actionDeviceID)
                if deviceHandle is not None:
                    deviceHandle.doForceSync(True)

    def toString(self):
        return json.dumps(self.instruction)


class InstructionManager:
    def __init__(self, deviceManager: DeviceManager) -> None:
        self.deviceManager: DeviceManager = deviceManager
        self.instructionHandleList = list()

    def handleAll(self):
        current_list = self.instructionHandleList.copy()
        for insHandle in current_list:
            insHandle.handle()

    def handleTime(self, t=None):
        current_list = self.instructionHandleList.copy()
        for insHandle in current_list:
            insHandle.handleTime(t)

    def _initInstructionInfo(self, DeviceID):
        instructionsInfo = list()
        try:
            instructionsInfo = self.deviceManager.mysql.select((
                "InstructionTable.InstructionID",
                "InstructionTable.InstructionIsOn",
                "InstructionTable.InstructionName",
                "InstructionTable.InstructionMeta",),
                "InstructionTable INNER JOIN DeviceInstructionLinkTable ON InstructionTable.InstructionID = DeviceInstructionLinkTable.InstructionID",
                f"DeviceInstructionLinkTable.DeviceID='{DeviceID}'")
        except Exception as e:
            print(e, flush=True)
        for insInfo in instructionsInfo:
            instructions = {
                "InstructionID": insInfo[0],
                "InstructionIsOn": insInfo[1],
                "InstructionName": insInfo[2],
                "InstructionMeta": json.loads(insInfo[3]),
            }
            insHandle = InstructionHandle(instructions, self)
            self.addInstructionHandle(insHandle)
        return None

    def getInstructionStatus(self, instructionID, instructionName=None):
        status = None
        instructionHandle = self.getInstructionHandle(
            instructionID, instructionName)
        if (instructionHandle) is not None:
            status = instructionHandle.InstructionIsOn
        return status

    def onStatusChange(self, deviceID, deviceIsOn):
        for insHandle in self.instructionHandleList:
            if deviceID in insHandle.conditionDeviceIDSet:
                insHandle.handle()
        return None

    def addInstructionHandleFromDB(self, instructionID):
        mysql = self.deviceManager.mysql
        try:
            if mysql is not None:
                insInfo = mysql.select(("InstructionID",
                                        "InstructionIsOn",
                                        "InstructionName",
                                        "InstructionMeta",),
                                       "InstructionTable",
                                       f"InstructionID='{instructionID}'")
                if insInfo == ():
                    raise Exception(
                        f"InstructionID:{self.instructionID} not exist in db")
                insInfo = insInfo[0]
                instructions = {
                    "InstructionID": insInfo[0],
                    "InstructionIsOn": insInfo[1],
                    "InstructionName": insInfo[2],
                    "InstructionMeta": json.loads(insInfo[3]),
                }
                insHandle = InstructionHandle(instructions, self)
                self.addInstructionHandle(insHandle)
        except Exception as e:
            print(e, flush=True)
        return None

    def addInstructionHandle(self, instructionHandle):
        if (self.getInstructionHandle(instructionHandle.InstructionID)) is None:
            self.instructionHandleList.append(instructionHandle)
        return None

    def getInstructionHandle(self, instructionID, instructionName=None) -> InstructionHandle:
        instructionHandle = None
        for insHandle in self.instructionHandleList:
            if instructionName is not None:
                if instructionName == insHandle.InstructionName:
                    instructionHandle = insHandle
                    break
            else:
                if instructionID == insHandle.InstructionID:
                    instructionHandle = insHandle
                    break
        return instructionHandle

    def popInstructionHandle(self, instructionID, instructionName=None) -> InstructionHandle:
        instructionHandle = self.getInstructionHandle(
            instructionID, instructionName)
        if instructionHandle is not None:
            self.instructionHandleList.remove(instructionHandle)
        return instructionHandle

    def removeInstructionHandle(self, instructionID, instructionName=None, instructionHandle=None):
        if instructionHandle is None:
            instructionHandle = self.getInstructionHandle(
                instructionID, instructionName)
        if instructionHandle is not None:
            self.instructionHandleList.remove(instructionHandle)
        return None


class ConnectionManager(threading.Thread):
    """
    example:
    connectionManager = ConnectionManager(mysql)
    then you can:
    connectionManager.start()
    or you can:
    with connectionManager as deviceManager:
        do your things
    """

    def __init__(self, mysql: sqlModule.MYSQL = None):
        super().__init__()
        self.lock = threading.Lock()
        self.mysql = None
        self.deviceManager: DeviceManager = None
        self.time: int = int(time.time())
        if mysql is not None:
            self.mysql = mysql
            self.deviceManager = DeviceManager(mysql)

    def __enter__(self) -> DeviceManager:
        self.lock.acquire()
        return self.deviceManager

    def __exit__(self, type, value, trace):
        self.lock.release()

    def _initDeviceManager(self, mysql: sqlModule.MYSQL):
        self.mysql = mysql
        self.deviceManager = DeviceManager(mysql)

    def run(self):
        while True:
            # use time.sleep(0.01) for debug (pass lock to backend)
            time.sleep(0.01)
            with self as deviceManager:
                deviceManager.handleAll()
                timeNow = int(time.time())
                if timeNow > self.time:
                    self.time = timeNow
                    timeNow = datetime.datetime.fromtimestamp(timeNow)
                    deviceManager.instructionManager.handleTime(timeNow)


if __name__ == "__main__":
    mysql = sqlModule.MYSQL(database="SmartHomeDB", user="jim",
                            password="jimmysql", host="127.0.0.1")
    cm = ConnectionManager(mysql)
    cm.start()
    with cm as deviceManager:
        deviceManager
        pass

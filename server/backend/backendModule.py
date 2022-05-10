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
import backend.connectionModule as connectionModule

# global variable
TOEKN_EXPIRE_TIME = 3600 * 12  # 12h
mysql = sqlModule.MYSQL(database="SmartHomeDB", user="jim",
                        password="jimmysql", host="127.0.0.1")
# if use flask debug, you can NOT use connectionManager
connectionManager = connectionModule.ConnectionManager(mysql)
# with connectionManager as deviceManager:
#       do things
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'SmartHomeProject'
# end of global variable


def generatePassword(UserPasswordString, saltLength=512):
    """
    generate password
    parameter:
        UserPasswordString: str
        saltLength: int
    return:
        tuple(UserPassword, UserSalt): tuple(bytes, bytes)
    """
    # def bytesXOR(bytesA, bytesB):
    #     intA = int.from_bytes(bytesA, sys.byteorder)
    #     intB = int.from_bytes(bytesB, sys.byteorder)
    #     intC = intA ^ intB
    #     bytesC = intC.to_bytes(max(len(bytesA), len(bytesB)), sys.byteorder)
    #     return bytesC
    def getSHA512bytes(data):
        if type(data) is str:
            data = data.encode()
        return hashlib.sha512(data).digest()

    UserSalt = os.urandom(int(saltLength/8))
    UserPassword = getSHA512bytes(
        getSHA512bytes(UserPasswordString) + UserSalt)
    return (UserPassword, UserSalt)


def verifyPassword(UserPasswordString, UserSalt, UserPassword):
    """
    verify password
    parameter:
        UserPasswordString: str
        UserSalt: bytes
        UserPassword: bytes
    return:
        IsSame: bool
    """
    def getSHA512bytes(data):
        if type(data) is str:
            data = data.encode()
        return hashlib.sha512(data).digest()

    TruePassword = getSHA512bytes(
        getSHA512bytes(UserPasswordString) + UserSalt)
    IsSame = TruePassword == UserPassword
    return IsSame


def createToken(tokenDict, expireTime=3600):
    """
    create token
    parameter:
        tokenDict: a dict
        expireTime: int
    return:
        token: str, ascii encoding
    """
    if type(tokenDict["UserPassword"]) is bytes:
        tokenDict["UserPassword"] = tokenDict["UserPassword"].hex()
    s = Serializer(current_app.config["SECRET_KEY"], expires_in=expireTime)
    token = s.dumps(tokenDict).decode("ascii")
    return token


def verifyToken(token):
    """
    verify and decode token
    parameter:
        token: str, ascii encoding
    return:
        tokenDict: a dict
    """
    s = Serializer(current_app.config["SECRET_KEY"])
    tokenDict = s.loads(token)
    UserID = tokenDict["UserID"]
    UserPassword = bytes.fromhex(tokenDict["UserPassword"])
    TruePassword = mysql.select(
        "UserPassword", "UserTable", f"UserID='{UserID}'")[0][0]
    if UserPassword != TruePassword:
        raise Exception("Invalid token")
    return tokenDict


def checkDataKeys(data, keys):
    """
    check data to makesure data.keys() are in keys
    parameter:
        data: a dict
        keys: list of str
    return:
        data or raise Exception
    """
    if type(data) is dict:
        data_keys = data.keys()
    else:
        data_keys = [data]
    for key in data_keys:
        if key not in keys:
            raise Exception(f"key not in {keys}")
    return data


def checkPermission(UserID, PermissionType, DeviceID=None, InstructionID=None):
    """
    check User has Permission on Device/InstructionID or not
    parameter:
        UserID: int
        DeviceID: int
        InstructionID: int
        PermissionType: str, "CanView", "CanControl", "CanManage"
    return:
        bool: User has Permission on Device/InstructionID or not
    """
    checkDataKeys(PermissionType, ["CanView", "CanControl", "CanManage"])
    if DeviceID != None:
        PermissionInfo = mysql.select(["CanView", "CanControl", "CanManage"],
                                      "UserDevicePermissionTable",
                                      f"UserID='{UserID}' AND DeviceID='{DeviceID}'")
    # convert InstructionID to DeviceID
    elif InstructionID != None:
        PermissionInfo = mysql.select(["MAX(CanView)", "MAX(CanControl)", "MAX(CanManage)"],
                                      "UserDevicePermissionTable INNER JOIN DeviceInstructionLinkTable ON UserDevicePermissionTable.DeviceID = DeviceInstructionLinkTable.DeviceID"
                                      f"UserID='{UserID}' AND InstructionID='{InstructionID}' GROUP BY UserDevicePermissionTable.DeviceID")
    else:  # DeviceID=None, InstructionID=None
        return True
    if PermissionInfo == ():
        return False
    if PermissionType == "CanView":
        return PermissionInfo[0][0] > 0
    if PermissionType == "CanControl":
        return PermissionInfo[0][1] > 0
    if PermissionType == "CanManage":
        return PermissionInfo[0][2] > 0
    return False


# @app.route("/_register", methods=["POST"])
def _register():
    """
    post jsonData to backend
    jsonData = {"UserName":str,"UserPassword":str}
    return a json data
    if success return {"Token":token}
    else abort http 500
    """
    try:
        jsonData = request.get_json(force=True)
        jsonData = checkDataKeys(jsonData, ["UserName", "UserPassword"])
        UserName = jsonData["UserName"].lower()
        UserPasswordString = jsonData["UserPassword"]
        exist = mysql.select(("UserID"), "UserTable",
                             f"UserName='{UserName}'")
        if exist == () or exist == (()):  # Account not exists
            (UserPassword, UserSalt) = generatePassword(UserPasswordString)
            User = {"UserName": UserName,
                    "UserPassword": UserPassword,
                    "UserSalt": UserSalt}
            mysql.insert(User, "UserTable")
            UserID = mysql.select("UserID", "UserTable",
                                  f"UserName='{UserName}'")[0][0]
        else:
            raise Exception("Account already exists")

        tokenDict = {"UserID": UserID,
                     "UserName": UserName, "UserPassword": UserPassword}
        token = createToken(tokenDict)
        return {"Token": token}

    except Exception as e:
        print(e)
        abort(401)


# @app.route("/_login", methods=["POST"])
def _login():
    """
    post jsonData to backend
    jsonData = {"UserName":str,"UserPassword":str}
    return a json data
    if success return {"Token":token}
    else abort http 500
    """
    try:
        jsonData = request.get_json(force=True)
        jsonData = checkDataKeys(jsonData, ["UserName", "UserPassword"])
        UserName = jsonData["UserName"].lower()
        UserPasswordString = jsonData["UserPassword"]
        UserID, UserPassword, UserSalt = mysql.select(("UserID", "UserPassword", "UserSalt"), "UserTable",
                                                      f"UserName='{UserName}'")[0]
        if not verifyPassword(UserPasswordString, UserSalt, UserPassword):
            raise Exception("Wrong password")
        tokenDict = {"UserID": UserID,
                     "UserName": UserName, "UserPassword": UserPassword}
        token = createToken(tokenDict, TOEKN_EXPIRE_TIME)
        return {"Token": token}

    except Exception as e:
        print(e)
        abort(401)


# @app.route("/_permission", methods=["POST"])
def _permission():
    """
    post json to backend
    jsonData = {"Action":str, "Token":token, "DeviceID", "Data":json}
    "Action" can be "select", "insert", "delete" or "update"
    "Data" = list "Permission"
    "Permission" = {"PermissionID":int, "CanView":bool, "CanControl":bool, "CanManage":bool}
    if success return {"Data":json}
    elif token expired abort http 401
    else abort http 500
    """
    def select(DeviceID):
        PermissionInfo = mysql.select(("UserTable.UserID",
                                       "UserTable.UserName",
                                       "UserDevicePermissionTable.PermissionID",
                                       "UserDevicePermissionTable.CanView",
                                       "UserDevicePermissionTable.CanControl",
                                       "UserDevicePermissionTable.CanManage",
                                       "UserDevicePermissionTable.PermissionrMeta",),
                                      " UserTable INNER JOIN UserDevicePermissionTable ON UserTable.UserID = UserDevicePermissionTable.UserID",
                                      f"UserDevicePermissionTable.DeviceID='{DeviceID}'")
        Data = []
        for per in PermissionInfo:
            Permission = {"UserID":             per[0],
                          "UserName":           per[1],
                          "PermissionID":       per[2],
                          "CanView":            per[3],
                          "CanControl":         per[4],
                          "CanManage":          per[5],
                          "PermissionrMeta":    per[6],
                          }
            Data.append(Permission)
        return Data

    try:
        jsonData = request.get_json(force=True)
        checkDataKeys(jsonData, ["Action", "Token", "DeviceID", "Data"])
        checkDataKeys(jsonData["Action"],
                      ["select", "insert", "delete", "update"])
        Action = jsonData["Action"]
        Token = jsonData["Token"]
        DeviceID = jsonData["DeviceID"]
        Data = jsonData.get("Data")
        UserID = verifyToken(Token)["UserID"]

        if Action == "select":
            Data = select(DeviceID)

        elif Action == "insert":
            for Permission in Data:
                DevicePassword = Permission.pop("DevicePassword")
                TruePassword = mysql.select("DevicePassword", "DeviceTable",
                                            f"DeviceID='{DeviceID}'")[0][0]
                if DevicePassword.encode() != TruePassword:
                    raise Exception("wrong password")
                Permission["UserID"] = UserID
                mysql.insert(Permission, "UserDevicePermissionTable")
            Data = select(DeviceID)

        elif Action == "delete":
            for Permission in Data:
                PermissionID = Permission["PermissionID"]
                mysql.delete("UserDevicePermissionTable",
                             f"PermissionID='{PermissionID}'")
            Data = select(DeviceID)

        elif Action == "update":
            if not checkPermission(UserID, "CanManage", DeviceID=DeviceID):
                raise Exception("User can NOT Manage the Device")
            for Permission in Data:
                PermissionID = Permission["PermissionID"]
                if not Permission.get("CanManage"):
                    Permission["CanManage"] = False
                else:
                    Permission["CanControl"] = True
                if not Permission.get("CanControl"):
                    Permission["CanControl"] = False
                else:
                    Permission["CanView"] = True
                if not Permission.get("CanView"):
                    # Permission["CanView"] = False
                    mysql.delete("UserDevicePermissionTable",
                                 f"PermissionID='{PermissionID}'")
                else:
                    # Permission["CanView"] = True
                    mysql.update(Permission, "UserDevicePermissionTable",
                                 f"PermissionID='{PermissionID}'")
            Data = select(DeviceID)

        return {"Data": Data}

    except BadData:
        abort(401)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/_device", methods=["POST"])
def _device():
    """
    post json to backend
    jsonData = {"Action":str, "Token":token, "Data":json}
    "Action" can be "select" or "update"
    "Data" = list "Device"
    "Device" = {"DeviceID":int, "DeviceName":str}
    if success return {"Data":json}
    elif token expired abort http 401
    else abort http 500
    """
    def select(UserID):
        DevicesInfo = mysql.select(("DeviceTable.DeviceID",
                                    "DeviceTable.DeviceName",
                                   "DeviceTable.DeviceType",
                                    "DeviceTable.DeviceMeta",
                                    "DeviceTable.DeviceDescription",
                                    "DeviceTable.DeviceIsOn",
                                    "DeviceTable.DeviceIsOnline",
                                    "UserDevicePermissionTable.PermissionID",
                                    "UserDevicePermissionTable.CanView",
                                    "UserDevicePermissionTable.CanControl",
                                    "UserDevicePermissionTable.CanManage",
                                    "UserDevicePermissionTable.PermissionrMeta",),
                                   " DeviceTable INNER JOIN UserDevicePermissionTable ON DeviceTable.DeviceID = UserDevicePermissionTable.DeviceID",
                                   f"UserDevicePermissionTable.UserID='{UserID}'")
        Data = []
        for dev in DevicesInfo:
            Device = {"DeviceID":           dev[0],
                      "DeviceName":         dev[1],
                      "DeviceType":         dev[2],
                      "DeviceMeta":         dev[3],
                      "DeviceDescription":  dev[4],
                      "DeviceIsOn":         dev[5],
                      "DeviceIsOnline":     dev[6],
                      "PermissionID":       dev[7],
                      "CanView":            dev[8],
                      "CanControl":         dev[9],
                      "CanManage":          dev[10],
                      "PermissionrMeta":    dev[11],
                      }
            Data.append(Device)
        return Data

    try:
        jsonData = request.get_json(force=True)
        checkDataKeys(jsonData, ["Action", "Token", "Data"])
        checkDataKeys(jsonData["Action"], ["select", "update"])
        Action = jsonData["Action"]
        Token = jsonData["Token"]
        Data = jsonData.get("Data")
        UserID = verifyToken(Token)["UserID"]

        if Action == "select":
            Data = select(UserID)

        elif Action == "update":
            for Device in Data:
                DeviceID = Device["DeviceID"]
                if not checkPermission(UserID, "CanManage", DeviceID=DeviceID):
                    raise Exception("User can NOT Manage the Device")
                # manage connection -> device on/off
                if (Device.get("DeviceIsOn") is not None):
                    DeviceIsOn = Device.pop("DeviceIsOn")
                    with connectionManager as deviceManager:
                        deviceManager.getDeviceHandle(
                            DeviceID).tryChangeStatus(DeviceIsOn)
                mysql.update(Device, "DeviceTable",
                             f"DeviceID='{DeviceID}'")
            Data = select(UserID)

        return {"Data": Data}

    except BadData:
        abort(401)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/_instruction", methods=["POST"])
def _instruction():
    """
    post json to backend
    jsonData = {"Action":str, "Token":token, "DeviceID":int, "Data":json}
    "Action" can be "select", "insert", "delete" or "update"
    "Data" = list "Instruction"
    "Instruction" = {"InstructionID":int, "InstructionName":str, "InstructionMeta":str,
                     "InstructionDescription":str, "InstructionIsOn":bool}
    if success return {"Data":json}
    elif token expired abort http 401
    else abort http 500
    """
    def select(UserID, DeviceID=None):
        condition = f"UserDevicePermissionTable.UserID='{UserID}'"
        if DeviceID is not None:
            condition = f"UserDevicePermissionTable.DeviceID='{DeviceID}'"
        condition += f" GROUP BY InstructionTable.InstructionID"  # , UserTable.UserID"
        condition += f" ORDER BY InstructionTable.InstructionID"  # , UserTable.UserID"
        InstructionsInfo = mysql.select(
            ("InstructionTable.InstructionID",
             "ANY_VALUE(InstructionTable.InstructionName)",
             "ANY_VALUE(InstructionTable.InstructionMeta)",
             "ANY_VALUE(InstructionTable.InstructionDescription)",
             "ANY_VALUE(InstructionTable.InstructionIsOn)",
             "MAX(UserDevicePermissionTable.CanView)",
             "MAX(UserDevicePermissionTable.CanControl)",
             "MAX(UserDevicePermissionTable.CanManage)",
             # "UserTable.UserID",
             # "ANY_VALUE(UserTable.UserName)",
             ),
            " InstructionTable INNER JOIN DeviceInstructionLinkTable ON InstructionTable.InstructionID = DeviceInstructionLinkTable.InstructionID" +
            " INNER JOIN DeviceTable ON DeviceInstructionLinkTable.DeviceID = DeviceTable.DeviceID" +
            " INNER JOIN UserDevicePermissionTable ON DeviceTable.DeviceID = UserDevicePermissionTable.DeviceID" +
            " INNER JOIN UserTable ON UserDevicePermissionTable.UserID = UserTable.UserID",
            condition=condition)
        Data = []
        for ins in InstructionsInfo:
            Instruction = {
                "InstructionID":            ins[0],
                "InstructionName":          ins[1],
                "InstructionMeta":          ins[2],
                "InstructionDescription":   ins[3],
                "InstructionIsOn":          ins[4],
                # "UserID":                   ins[8],
                # "UserName":                 ins[9],
            }
            if DeviceID is None:
                Instruction.update({
                    "CanView":              ins[5],
                    "CanControl":           ins[6],
                    "CanManage":            ins[7],
                })
            Data.append(Instruction)
        return Data

    def insert_link(ins):
        def insert_link_condition(con):
            if con["type"] in ("and", "or"):
                insert_link_condition(con["conditionA"])
                insert_link_condition(con["conditionB"])
            elif con["type"] == "if":
                link_con = {
                    "DeviceID": con["DeviceID"],
                    "InstructionID": ins["InstructionID"],
                    "LinkCondition": True,
                    "LinkAction": False,
                }
                mysql.insert(link_con, "DeviceInstructionLinkTable")
            else:  # con["type"] == "when":
                pass
            return None

        # init
        ins["InstructionID"] = mysql.select(
            "InstructionID", "InstructionTable",
            f"InstructionName='{ins['InstructionName']}'")[0][0]
        # insert_link_action
        insert_link_condition(ins["InstructionMeta"]["condition"])
        # insert_link_action
        action = ins["InstructionMeta"]["action"]
        db_link_act_info = mysql.select(
            "LinkCondition", "DeviceInstructionLinkTable",
            f"InstructionID='{ins['InstructionID']}' AND DeviceID='{action['DeviceID']}'"
        )
        linkCondition = True if (db_link_act_info == ((1,),)) else False
        link_act = {
            "DeviceID": action["DeviceID"],
            "InstructionID": ins["InstructionID"],
            "LinkCondition": linkCondition,
            "LinkAction": True,
        }
        if linkCondition:
            mysql.update(link_act, "DeviceInstructionLinkTable",
                         f"InstructionID='{ins['InstructionID']}' AND DeviceID='{action['DeviceID']}'")
        else:
            mysql.insert(link_act, "DeviceInstructionLinkTable")
        return None

    try:
        jsonData = request.get_json(force=True)
        jsonData = checkDataKeys(jsonData,
                                 ["Action", "Token",  "DeviceID", "Data"])
        Action = jsonData["Action"]
        Token = jsonData["Token"]
        DeviceID = jsonData.get("DeviceID")
        Data = jsonData.get("Data")
        UserID = verifyToken(Token)["UserID"]
        # also manage link
        if Action == "select":
            if not checkPermission(UserID, "CanView", DeviceID=DeviceID):
                raise Exception("Permission Denied!")
            Data = select(UserID, DeviceID)
        elif Action == "insert":
            for ins in Data:
                # mysql.insert ins
                mysql.insert(ins, "InstructionTable")
                # mysql.insert(link, "DeviceInstructionLinkTable")
                insert_link(ins)
                with connectionManager as deviceManager:
                    deviceManager.instructionManager.addInstructionHandleFromDB(
                        ins["InstructionID"])
            Data = select(UserID, DeviceID)
        elif Action == "delete":
            for ins in Data:
                with connectionManager as deviceManager:
                    insHandle = deviceManager.instructionManager.getInstructionHandle(
                        ins["InstructionID"])
                    if insHandle is not None:
                        insHandle.remove()
                mysql.delete("DeviceInstructionLinkTable",
                             f"InstructionID={ins['InstructionID']}")
                mysql.delete("InstructionTable",
                             f"InstructionID={ins['InstructionID']}")
            Data = select(UserID, DeviceID)
        elif Action == "update":
            for ins in Data:
                # mysql.delete ins
                with connectionManager as deviceManager:
                    insHandle = deviceManager.instructionManager.getInstructionHandle(
                        ins["InstructionID"])
                    if insHandle is not None:
                        insHandle.remove()
                mysql.delete("DeviceInstructionLinkTable",
                             f"InstructionID={ins['InstructionID']}")
                mysql.delete("InstructionTable",
                             f"InstructionID={ins['InstructionID']}")
                # mysql.insert ins
                mysql.insert(ins, "InstructionTable")
                # mysql.insert(link, "DeviceInstructionLinkTable")
                insert_link(ins)
                with connectionManager as deviceManager:
                    deviceManager.instructionManager.addInstructionHandleFromDB(
                        ins["InstructionID"])
            Data = select(UserID, DeviceID)

        return {"Data": Data}

    except BadData:
        abort(401)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/_account", methods=["POST"])
def _account():
    """
    post json to backend
    jsonData = {"Action":str, "Token":token, "Data":json}
    "Action" can be "select", "changePassword"
    "Data" = {"UserPassword":str}
    if success return {"Token":token, "UserData":json}
    elif token expired abort http 401
    else abort http 500
    """

    try:
        jsonData = request.get_json(force=True)
        if type(jsonData) is str:  # debug request.get_json
            jsonData = json.loads(jsonData)
        jsonData = checkDataKeys(jsonData, ["Action", "Token", "Data"])
        Action = jsonData["Action"]
        Token = jsonData["Token"]
        Data = jsonData.get("Data")
        tokenDict = verifyToken(Token)
        UserID = tokenDict["UserID"]
        checkDataKeys(Data, ["UserPassword", None])

        # if Action == "select":
        UserInfo = mysql.select(("UserName", "UserMeta"),
                                " UserTable", f"UserID='{UserID}'")
        UserData = {"UserID": UserID,
                    "UserName": UserInfo[0][0],
                    "UserMeta": UserInfo[0][1]}

        if Action == "changePassword":
            UserPasswordString = Data["UserPassword"]
            (UserPassword, UserSalt) = generatePassword(UserPasswordString)
            User = {"UserPassword": UserPassword, "UserSalt": UserSalt}
            mysql.update(User, "UserTable", f"UserID='{UserID}'")
            tokenDict["UserPassword"] = UserPassword

        token = createToken(tokenDict)
        return {"Token": token, "UserData": UserData}

    except BadData:
        abort(401)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/_trigger", methods=["POST"])
def _trigger():
    # refreshing
    with connectionManager as deviceManager:
        deviceManager.instructionManager.handleAll()
    # end refreshing

    try:
        jsonData = request.get_json(force=True)
        jsonData = checkDataKeys(jsonData,
                                 ["Action", "Token",  "DeviceID", "Data"])
        Action = jsonData.get("Action")
        Token = jsonData.get("Token")
        DeviceID = jsonData.get("DeviceID")
        Data = jsonData.get("Data")
        if Token != "SmartDevice":
            return
        if Action == "select":
            Data = list()
            instructionsInfo = mysql.select((
                "InstructionTable.InstructionID",
                "ANY_VALUE(InstructionName)",
                "ANY_VALUE(InstructionMeta)",
                "ANY_VALUE(InstructionIsOn)",),
                "InstructionTable INNER JOIN DeviceInstructionLinkTable ON " +
                "InstructionTable.InstructionID = DeviceInstructionLinkTable.InstructionID",
                f"TRUE GROUP BY InstructionTable.InstructionID HAVING COUNT(LinkID) = 1 AND MAX(DeviceID)='{DeviceID}' "
            )
            for insInfo in instructionsInfo:
                ins = {
                    "InstructionID":  insInfo[0],
                    "InstructionName": insInfo[1],
                    "InstructionMeta": json.loads(insInfo[2]),
                    "InstructionIsOn": insInfo[3],
                }
                Data.append(ins)
            return {"Data": Data}
        return None
    except BadData:
        abort(401)
    except Exception as e:
        print(e)
        abort(500)

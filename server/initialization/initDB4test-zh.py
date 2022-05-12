import sys
import os
sys.path.append(os.getcwd()+"/server/")
if True:
    import backend.sqlModule as sqlModule
    import backend.backendModule as backendModule


mysql = sqlModule.MYSQL(database="SmartHomeDB", user="jim",
                        password="jimmysql", host="127.0.0.1")


# User
User1 = {"UserName": "jim", "UserPassword": "123", }
(UserPassword, UserSalt) = backendModule.generatePassword(
    User1["UserPassword"])
User1["UserPassword"] = UserPassword
User1["UserSalt"] = UserSalt
mysql.insert(User1, "UserTable")
User1["UserID"] = mysql.select("UserID", "UserTable", "UserName='jim'")[0][0]

User2 = {"UserName": "tom", "UserPassword": "123", }
(UserPassword, UserSalt) = backendModule.generatePassword(
    User2["UserPassword"])
User2["UserPassword"] = UserPassword
User2["UserSalt"] = UserSalt
mysql.insert(User2, "UserTable")
User2["UserID"] = mysql.select("UserID", "UserTable", "UserName='tom'")[0][0]

# device
Device1 = {
    "DeviceName": "智能灯01",
    "DevicePassword": "智能灯01",
    "DeviceType": "智能灯",
    "DeviceIsOn": True,
    "DeviceIsOnline": True,
}
mysql.insert(Device1, "DeviceTable")
Device1["DeviceID"] = mysql.select(
    "DeviceID", "DeviceTable", "DeviceName='智能灯01'")[0][0]

Device2 = {
    "DeviceName": "智能灯02",
    "DevicePassword": "智能灯02",
    "DeviceType": "智能灯",
    "DeviceIsOn": True,
    "DeviceIsOnline": True,
}
mysql.insert(Device2, "DeviceTable")
Device2["DeviceID"] = mysql.select(
    "DeviceID", "DeviceTable", "DeviceName='智能灯02'")[0][0]

Device3 = {
    "DeviceName": "智能闹钟01",
    "DevicePassword": "智能闹钟01",
    "DeviceType": "智能闹钟",
    "DeviceIsOn": True,
    "DeviceIsOnline": True,
}
mysql.insert(Device3, "DeviceTable")
Device3["DeviceID"] = mysql.select(
    "DeviceID", "DeviceTable", "DeviceName='智能闹钟01'")[0][0]

Device4 = {
    "DeviceName": "智能闹钟02",
    "DevicePassword": "智能闹钟02",
    "DeviceType": "智能闹钟",
    "DeviceIsOn": True,
    "DeviceIsOnline": True,
}
mysql.insert(Device4, "DeviceTable")
Device4["DeviceID"] = mysql.select(
    "DeviceID", "DeviceTable", "DeviceName='智能闹钟02'")[0][0]

Device5 = {
    "DeviceName": "智能助手01",
    "DevicePassword": "智能助手01",
    "DeviceType": "智能助手",
    "DeviceIsOn": True,
    "DeviceIsOnline": True,
}
mysql.insert(Device5, "DeviceTable")
Device5["DeviceID"] = mysql.select(
    "DeviceID", "DeviceTable", "DeviceName='智能助手01'")[0][0]
# UserDevicePermissionTable
Permission1 = {
    "UserID": User1["UserID"],
    "DeviceID": Device1["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": True,
}
mysql.insert(Permission1, "UserDevicePermissionTable")
Permission1["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User1['UserID']} AND DeviceID={Device1['DeviceID']}")[0][0]

Permission2 = {
    "UserID": User1["UserID"],
    "DeviceID": Device2["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": False,
}
mysql.insert(Permission2, "UserDevicePermissionTable")
Permission2["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User1['UserID']} AND DeviceID={Device2['DeviceID']}")[0][0]

Permission3 = {
    "UserID": User1["UserID"],
    "DeviceID": Device3["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": True,
}
mysql.insert(Permission3, "UserDevicePermissionTable")
Permission3["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User1['UserID']} AND DeviceID={Device3['DeviceID']}")[0][0]

Permission4 = {
    "UserID": User1["UserID"],
    "DeviceID": Device4["DeviceID"],
    "CanView": True,
    "CanControl": False,
    "CanManage": False,
}
mysql.insert(Permission4, "UserDevicePermissionTable")
Permission4["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User1['UserID']} AND DeviceID={Device4['DeviceID']}")[0][0]

Permission5 = {
    "UserID": User2["UserID"],
    "DeviceID": Device2["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": True,
}
mysql.insert(Permission5, "UserDevicePermissionTable")
Permission5["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User2['UserID']} AND DeviceID={Device2['DeviceID']}")[0][0]

Permission6 = {
    "UserID": User2["UserID"],
    "DeviceID": Device4["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": True,
}
mysql.insert(Permission6, "UserDevicePermissionTable")
Permission6["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User2['UserID']} AND DeviceID={Device4['DeviceID']}")[0][0]

Permission7 = {
    "UserID": User1["UserID"],
    "DeviceID": Device5["DeviceID"],
    "CanView": True,
    "CanControl": True,
    "CanManage": True,
}
mysql.insert(Permission7, "UserDevicePermissionTable")
Permission7["PermissionID"] = mysql.select(
    "PermissionID", "UserDevicePermissionTable",
    f"UserID={User1['UserID']} AND DeviceID={Device5['DeviceID']}")[0][0]
# InstructionTable
Instruction1Meta = {
    "condition": {
        "type": "if",
        "DeviceID": Device1["DeviceID"],
        "DeviceIsOn": True,
    },
    "action": {
        "DeviceID": Device2["DeviceID"],
        "DeviceIsOn": False,
    },
}
Instruction1 = {
    "InstructionName": "指令01",
    "InstructionMeta": Instruction1Meta,
    "InstructionIsOn": True,
}
mysql.insert(Instruction1, "InstructionTable")
Instruction1["InstructionID"] = mysql.select(
    "InstructionID", "InstructionTable",
    "InstructionName='指令01'")[0][0]

Instruction2Meta = {
    "condition": {
        "type": "when",
        "time": "2022-04-25T18:00:00",
        "timeOperator": "=",  # triggerd = true/false?
        "repeat": False,
    },
    "action": {
        "DeviceID": Device1["DeviceID"],
        "DeviceIsOn": False,
    },
}
Instruction2 = {
    "InstructionName": "指令02",
    "InstructionMeta": Instruction2Meta,
    "InstructionIsOn": True,
}
mysql.insert(Instruction2, "InstructionTable")
Instruction2["InstructionID"] = mysql.select(
    "InstructionID", "InstructionTable",
    "InstructionName='指令02'")[0][0]

Instruction3Meta = {
    "condition": {
        "type": "if",
        "DeviceID": Device1["DeviceID"],
        "DeviceIsOn": False,
    },
    "action": {
        "DeviceID": Device3["DeviceID"],
        "DeviceIsOn": True,
    },
}
Instruction3 = {
    "InstructionName": "指令03",
    "InstructionMeta": Instruction3Meta,
    "InstructionIsOn": True,
}
mysql.insert(Instruction3, "InstructionTable")
Instruction3["InstructionID"] = mysql.select(
    "InstructionID", "InstructionTable",
    "InstructionName='指令03'")[0][0]

Instruction4Meta = {
    "condition": {
        "type": "or",
        "conditionA": {
            "type": "and",
            "conditionA": {
                "type": "if",
                "DeviceID": Device1["DeviceID"],
                "DeviceIsOn": True,
            },
            "conditionB": {
                "type": "if",
                "DeviceID": Device3["DeviceID"],
                "DeviceIsOn": False,
            },
        },
        "conditionB": {
            "type": "if",
            "DeviceID": Device2["DeviceID"],
            "DeviceIsOn": True,
        },
    },
    "action": {
        "DeviceID": Device4["DeviceID"],
        "DeviceIsOn": False,
    },
}
Instruction4 = {
    "InstructionName": "指令04",
    "InstructionMeta": Instruction4Meta,
    "InstructionIsOn": True,
}
mysql.insert(Instruction4, "InstructionTable")
Instruction4["InstructionID"] = mysql.select(
    "InstructionID", "InstructionTable",
    "InstructionName='指令04'")[0][0]
# DeviceInstructionLinkTable
Link1 = {
    "DeviceID": Device1["DeviceID"],
    "InstructionID": Instruction1["InstructionID"],
    "LinkCondition": True,
    "LinkAction": False,
}
mysql.insert(Link1, "DeviceInstructionLinkTable")
Link1["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device1['DeviceID']} AND InstructionID={Instruction1['InstructionID']}")[0][0]

Link2 = {
    "DeviceID": Device2["DeviceID"],
    "InstructionID": Instruction1["InstructionID"],
    "LinkCondition": False,
    "LinkAction": True,
}
mysql.insert(Link2, "DeviceInstructionLinkTable")
Link2["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device2['DeviceID']} AND InstructionID={Instruction1['InstructionID']}")[0][0]

Link3 = {
    "DeviceID": Device1["DeviceID"],
    "InstructionID": Instruction2["InstructionID"],
    "LinkCondition": False,
    "LinkAction": True,
}
mysql.insert(Link3, "DeviceInstructionLinkTable")
Link3["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device1['DeviceID']} AND InstructionID={Instruction2['InstructionID']}")[0][0]

Link4 = {
    "DeviceID": Device1["DeviceID"],
    "InstructionID": Instruction3["InstructionID"],
    "LinkCondition": True,
    "LinkAction": False,
}
mysql.insert(Link4, "DeviceInstructionLinkTable")
Link4["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device1['DeviceID']} AND InstructionID={Instruction3['InstructionID']}")[0][0]

Link5 = {
    "DeviceID": Device3["DeviceID"],
    "InstructionID": Instruction3["InstructionID"],
    "LinkCondition": False,
    "LinkAction": True,
}
mysql.insert(Link5, "DeviceInstructionLinkTable")
Link5["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device3['DeviceID']} AND InstructionID={Instruction3['InstructionID']}")[0][0]

Link6 = {
    "DeviceID": Device1["DeviceID"],
    "InstructionID": Instruction4["InstructionID"],
    "LinkCondition": True,
    "LinkAction": False,
}
mysql.insert(Link6, "DeviceInstructionLinkTable")
Link6["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device1['DeviceID']} AND InstructionID={Instruction4['InstructionID']}")[0][0]

Link7 = {
    "DeviceID": Device2["DeviceID"],
    "InstructionID": Instruction4["InstructionID"],
    "LinkCondition": True,
    "LinkAction": False,
}
mysql.insert(Link7, "DeviceInstructionLinkTable")
Link7["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device2['DeviceID']} AND InstructionID={Instruction4['InstructionID']}")[0][0]

Link8 = {
    "DeviceID": Device3["DeviceID"],
    "InstructionID": Instruction4["InstructionID"],
    "LinkCondition": True,
    "LinkAction": False,
}
mysql.insert(Link8, "DeviceInstructionLinkTable")
Link8["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device3['DeviceID']} AND InstructionID={Instruction4['InstructionID']}")[0][0]

Link9 = {
    "DeviceID": Device4["DeviceID"],
    "InstructionID": Instruction4["InstructionID"],
    "LinkCondition": False,
    "LinkAction": True,
}
mysql.insert(Link9, "DeviceInstructionLinkTable")
Link9["LinkID"] = mysql.select(
    "LinkID", "DeviceInstructionLinkTable",
    f"DeviceID={Device4['DeviceID']} AND InstructionID={Instruction4['InstructionID']}")[0][0]

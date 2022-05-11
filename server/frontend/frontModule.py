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


# global variable
HOST = "127.0.0.1"
if "GCC" in sys.version:
    HOST = "10.0.16.17"
BACKEND_IP = HOST
BACKEND_PORT = 54321
BACKEND_URL = "http://"+BACKEND_IP+":12345"
# end of global variable


# @app.route("/", methods=["GET"])
def index():
    return render_template('index.html')


# @app.route("/login", methods=["GET"])
def login():
    return render_template('login.html')


# @app.route("/register", methods=["GET"])
def register():
    return render_template('register.html')


# @app.route("/overview", methods=["GET"])
def overview():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        Token = request.args["Token"]
        # devices
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_device", json=dataSent)
        dataReceived = result.json()
        devices = dataReceived["Data"]
        # instructions
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_instruction", json=dataSent)
        dataReceived = result.json()
        instructions = dataReceived["Data"]
        for instruction in instructions:
            instruction["InstructionMeta"] = json.loads(
                instruction["InstructionMeta"])
        # render html
        return render_template('overview.html', devices=devices, instructions=instructions)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/device", methods=["GET"])
def device():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        Token = request.args["Token"]
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_device", json=dataSent)
        dataReceived = result.json()
        devices = dataReceived["Data"]
        return render_template('device.html', devices=devices)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/device_detail", methods=["GET"])
def device_detail():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        Token = request.args["Token"]
        if "add" in request.args.keys():
            return render_template('device_detail.html', add=True, edit=True)
        edit = False
        if "edit" in request.args.keys():
            edit = True
        if "DeviceID" not in request.args.keys():
            return "DeviceID missing"
        DeviceID = int(request.args["DeviceID"])
        # dev info
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_device", json=dataSent)
        dataReceived = result.json()
        devices = dataReceived["Data"]
        device = None
        for dev in devices:
            if dev["DeviceID"] == DeviceID:
                device = dev
                break
        # permission info
        dataSent = {
            "Action": "select",
            "Token": Token,
            "DeviceID": DeviceID,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_permission", json=dataSent)
        dataReceived = result.json()
        permissions = dataReceived["Data"]
        # instruction info
        dataSent = {
            "Action": "select",
            "Token": Token,
            "DeviceID": DeviceID,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_instruction", json=dataSent)
        dataReceived = result.json()
        instructions = dataReceived["Data"]
        for instruction in instructions:
            instruction["InstructionMeta"] = json.loads(
                instruction["InstructionMeta"])
        return render_template('device_detail.html', device=device, permissions=permissions, instructions=instructions, edit=edit, add=False)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/instruction", methods=["GET"])
def instruction():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        Token = request.args["Token"]
        # instruction info
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_instruction", json=dataSent)
        dataReceived = result.json()
        instructions = dataReceived["Data"]
        for instruction in instructions:
            instruction["InstructionMeta"] = json.loads(
                instruction["InstructionMeta"])
        return render_template('instruction.html', instructions=instructions)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/instruction_detail", methods=["GET"])
def instruction_detail():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        Token = request.args["Token"]
        if "add" in request.args.keys():
            return render_template('instruction_detail.html', add=True, edit=True)
        edit = False
        if "edit" in request.args.keys():
            edit = True
        if "InstructionID" not in request.args.keys():
            return "InstructionID missing"
        InstructionID = int(request.args["InstructionID"])
        # instructions info
        dataSent = {
            "Action": "select",
            "Token": Token,
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_instruction", json=dataSent)
        dataReceived = result.json()
        instructions = dataReceived["Data"]
        # filter instructions
        instruction = None
        for ins in instructions:
            if ins["InstructionID"] == InstructionID:
                instruction = ins
                break
        instruction["InstructionMeta"] = json.loads(
            instruction["InstructionMeta"])
        return render_template('instruction_detail.html', instruction=instruction, edit=edit, add=False)
    except Exception as e:
        print(e)
        abort(500)


# @app.route("/account", methods=["GET"])
def account():
    try:
        if "Token" not in request.args.keys():
            return "Token missing"
        dataSent = {
            "Action": "select",
            "Token": request.args["Token"],
            "Data": None
        }
        result = requests.post(BACKEND_URL + "/_account", json=dataSent)
        dataReceived = result.json()
        UserData = dataReceived["UserData"]
        return render_template('account.html', UserData=UserData)
    except Exception as e:
        print(e)
        abort(500)


# helper functions
# @app.context_processor
def addShowInstructionMeta():
    def showCondition(condition, edit=False):
        conditionType = condition.get("type")
        if edit:
            if conditionType in ("and", "or"):
                list_group_item_1 = showCondition(
                    condition.get("conditionA"), edit)
                list_group_item_2 = f"""
                    <select onchange="conditionChange(this)">
                        <option >if</option>
                        <option >when</option>
                        <option {"selected" if conditionType == "and" else ""}>and</option>
                        <option {"selected" if conditionType == "or" else ""}>or</option>
                    </select>
                """
                conditionType.upper()
                list_group_item_3 = showCondition(
                    condition.get("conditionB"), edit)
            elif conditionType == "if":
                list_group_item_1 = """
                    <select onchange="conditionChange(this)">
                        <option selected>if</option>
                        <option >when</option>
                        <option >and</option>
                        <option >or</option>
                    </select>
                """
                list_group_item_2 = f"""DeviceID: <input value={condition.get('DeviceID')}>"""
                list_group_item_3 = f"""Device is : 
                                        <select>
                                            <option style="color: green;" {"selected" if condition.get('DeviceIsOn') else ""}>On</option>
                                            <option style="color: red;" {"selected" if not condition.get('DeviceIsOn') else ""}>Off</option>
                                        </select>
                                    """
            elif conditionType == "when":
                list_group_item_1 = """
                    <select onchange="conditionChange(this)">
                        <option >if</option>
                        <option selected>when</option>
                        <option >and</option>
                        <option >or</option>
                    </select>
                """
                list_group_item_2 = f"""time 
                                        <select>
                                            <option {"selected" if condition.get('timeOperator') == "=" else ""}>=</option>
                                            <option {"selected" if condition.get('timeOperator') == "<" else ""}>&lt;</option>
                                            <option {"selected" if condition.get('timeOperator') == ">" else ""}>&gt;</option>
                                        </select>
                                        <input type="datetime-local" value="{condition.get('time')}">
                                    """
                list_group_item_3 = f"""repeat : 
                                        <select>
                                            <option style="color: green;" {"selected" if condition.get('repeat') else ""}>On</option>
                                            <option style="color: red;" {"selected" if not condition.get('repeat') else ""}>Off</option>
                                        </select>
                                    """
            else:
                list_group_item_1 = """
                    <select onchange="conditionChange(this)">
                        <option selected>if</option>
                        <option >when</option>
                        <option >and</option>
                        <option >or</option>
                    </select>
                """
                list_group_item_2 = "DeviceID: <input>"
                list_group_item_3 = """Device is : 
                                        <select>
                                            <option style="color: green;">On</option>
                                            <option style="color: red;" selected>Off</option>
                                        </select>
                                    """

        else:
            if conditionType in ("and", "or"):
                list_group_item_1 = showCondition(
                    condition.get("conditionA"), edit)
                list_group_item_2 = conditionType.upper()
                list_group_item_3 = showCondition(
                    condition.get("conditionB"), edit)
            elif conditionType == "if":
                list_group_item_1 = conditionType.upper()
                list_group_item_2 = f"DeviceID: {condition.get('DeviceID')}"
                list_group_item_3 = f"Device is : {'On' if condition.get('DeviceIsOn') else 'Off'}"
            elif conditionType == "when":
                list_group_item_1 = conditionType.upper()
                list_group_item_2 = f"time {condition.get('timeOperator')} {condition.get('time')}"
                list_group_item_3 = f"repeat : {'True' if condition.get('repeat') else 'False'}"
            else:
                list_group_item_1 = ""
                list_group_item_2 = ""
                list_group_item_3 = ""

        return f"""
            <ul class="list-group">
            <li class="list-group-item list-group-item-action">{list_group_item_1}</li>
            <li class="list-group-item list-group-item-action">{list_group_item_2}</li>
            <li class="list-group-item list-group-item-action">{list_group_item_3}</li>
            </ul>
        """

    def showAction(action, edit=False):
        if edit:
            return f"""
                <ul class="list-group">
                <li class="list-group-item">DeviceID: 
                    <input id="ActionDeviceID" value="{action.get('DeviceID')}">
                </li>
                <li class="list-group-item">Turn: 
                    <select id="ActionDeviceIsOn">
                        <option style="color: green;"{"selected" if action.get('DeviceIsOn') else ""}>On</option>
                        <option style="color: red;"{"selected" if not action.get('DeviceIsOn') else ""}>Off</option>
                    </select>
                </li>
                </ul>
            """
        status = "On" if action.get("DeviceIsOn") else "Off"
        return f"""
            <ul class="list-group">
            <li class="list-group-item">DeviceID: {action.get("DeviceID")}</li>
            <li class="list-group-item">Turn {status}</li>
            </ul>
        """

    def showInstructionMeta(instructionMeta, edit=False, add=False):
        if (add):
            instructionMeta = {"condition": {}, "action": {}, }
            edit = True
        condition = instructionMeta.get("condition")
        action = instructionMeta.get("action")
        idInfo = 'id="InstructionMeta"' if edit else ""
        return f"""
            <ul class="list-group" {idInfo}>
            <li class="list-group-item">condition:</li>
            <li class="list-group-item">{showCondition(condition, edit)}</li>
            <li class="list-group-item">action:</li>
            <li class="list-group-item">{showAction(action, edit)}</li>
            </ul>
        """
    return dict(showInstructionMeta=showInstructionMeta)

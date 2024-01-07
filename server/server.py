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
import backend.backendModule as backendModule
import frontend.frontModule as frontModule

# init global config
HOST = "127.0.0.1"
if "GCC" in sys.version:
    HOST = "127.0.0.1"
CONNECTION_PORT = 54321
BACKEND_PORT = 12345
FRONTEND_PORT = 12345
SERVER_PORT = 12345

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SmartPillowProject'
# init end


# Flask frontend functions
@app.route("/", methods=["GET"])
def index():
    return frontModule.index()


@app.route("/register", methods=["GET"])
def register():
    return frontModule.register()


@app.route("/login", methods=["GET"])
def login():
    return frontModule.login()


@app.route("/overview", methods=["GET"])
def overview():
    return frontModule.overview()


@app.route("/device", methods=["GET"])
def device():
    return frontModule.device()


@app.route("/device_detail", methods=["GET"])
def device_detail():
    return frontModule.device_detail()


@app.route("/instruction", methods=["GET"])
def instruction():
    return frontModule.instruction()


@app.route("/instruction_detail", methods=["GET"])
def instruction_detail():
    return frontModule.instruction_detail()


@app.route("/account", methods=["GET"])
def account():
    return frontModule.account()


# Flask backend functions
@app.route("/_register", methods=["POST"])
def _register():
    return backendModule._register()


@app.route("/_login", methods=["POST"])
def _login():
    return backendModule._login()


@app.route("/_permission", methods=["POST"])
def _permission():
    return backendModule._permission()


@app.route("/_device", methods=["POST"])
def _device():
    return backendModule._device()


@app.route("/_instruction", methods=["POST"])
def _instruction():
    return backendModule._instruction()


@app.route("/_account", methods=["POST"])
def _account():
    return backendModule._account()


@app.route("/_trigger", methods=["POST"])
def _trigger():
    return backendModule._trigger()


# helper functions
@app.context_processor
def addShowInstructionMeta():
    return frontModule.addShowInstructionMeta()


# main
if __name__ == "__main__":
    connectionManagerInstance = backendModule.connectionManager
    connectionManagerInstance.start()
    app.run(host=HOST, port=SERVER_PORT, debug=False)

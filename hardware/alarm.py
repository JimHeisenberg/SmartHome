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


class Alarm(ConnectionManagerLocal.DeviceHandle):
    def doChangeStatus(self, turnDeviceOn=None):
        if turnDeviceOn is None:
            return None
        self.DeviceIsOn = turnDeviceOn
        if turnDeviceOn:
            os.system("mplayer /root/SmartHome/hardware/music.mp3 " +
                      "-loop 0 </dev/null >/dev/null 2>&1 &")
        else:
            os.system("pidof mplayer | xargs kill >/dev/null 2>&1")
        return True

    """
    class Music(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.lock = threading.Lock()
        self.lock.acquire()

    def run(self):
        while True:
            self.lock.acquire()
            os.system(
                "mplayer /root/SmartHome/hardware/music.mp3 -loop 0 </dev/null >/dev/null")
            self.lock.release()

    def stop(self):
        os.system("pidof mplayer | xargs kill ")
        self.lock.acquire()

    def play(self):
        self.lock.release()

    """
    # def initMusic(self):
    #    try:
    #        if self.music is None:
    #            self.music = Music()
    #        return self.music
    #    except AttributeError:
    #        self.music = Music()
    #    except Exception as e:
    #        print(e)


if __name__ == "__main__":
    a = Alarm(socket.socket(), None)
    a.doChangeStatus(True)
    time.sleep(10)
    a.doChangeStatus(False)

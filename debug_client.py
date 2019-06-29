from toysocks.client import SSLocal
from toysocks.encrypt import XOREncryptor, TaggedXOREncryptor
from toysocks.eventloop import EventLoop
from toysocks.port_selector import TimedPortSelector
import json
import sys
from pathlib import Path
import os
home = str(Path.home())

config = {
    "local_ip": "0.0.0.0",
    "local_port": 443,
    "remote_ip": "104.168.151.216",
    "remote_port": [3389],
    "password": "Find \"home directory\" in Python? - Stack Overflow"
}

local_ip = config["local_ip"]
local_port = config["local_port"]
remote_ip = config["remote_ip"]
remote_port = config["remote_port"]
password = config["password"]

if "tagged" in config and config["tagged"]:
  encryptor = TaggedXOREncryptor(password)
else:
  encryptor = XOREncryptor(password)
selector = TimedPortSelector(interval=6 * 3600)  # Switch port every x hours

event_loop = EventLoop()
ss_local = SSLocal(event_loop, (local_ip, local_port), (remote_ip, remote_port), encryptor, selector)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
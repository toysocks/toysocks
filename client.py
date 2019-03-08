from toysocks.client import SSLocal
from toysocks.encrypt import XOREncryptor
from toysocks.eventloop import EventLoop
import json
import sys
from pathlib import Path
import os
home = str(Path.home())

config_path = os.path.join(home, "toysocks.json")

config = json.load(open(config_path))

local_ip = config["local_ip"]
local_port = config["local_port"]
remote_ip = config["remote_ip"]
remote_port = config["remote_port"]
password = config["password"]

encryptor = XOREncryptor(password)

event_loop = EventLoop()
ss_local = SSLocal(event_loop, (local_ip, local_port), (remote_ip, remote_port), encryptor)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
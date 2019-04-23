from toysocks.client import SSLocal
from toysocks.encrypt import XOREncryptor, TaggedXOREncryptor
from toysocks.eventloop import EventLoop
from toysocks.port_selector import TimedPortSelector
import json
import sys
from pathlib import Path
import os
home = str(Path.home())

if len(sys.argv) == 1:
  config_path = os.path.join(home, "toysocks.json")
else:
  config_path = sys.argv[1]

config = json.load(open(config_path))

local_ip = config["local_ip"]
local_port = config["local_port"]
remote_ip = config["remote_ip"]
remote_port = config["remote_port"]
password = config["password"]

if "tagged" in config and config["tagged"]:
  encryptor = TaggedXOREncryptor(password)
else:
  encryptor = XOREncryptor(password)
selector = TimedPortSelector(interval=6 * 3600) # Switch port every x hours

event_loop = EventLoop()
ss_local = SSLocal(event_loop, (local_ip, local_port), (remote_ip, remote_port), encryptor, selector)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
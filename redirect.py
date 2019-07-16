from toysocks.redirect import SSLocalTcp
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

default_config = {
  "local_ip": "127.0.0.1"
}

config = json.load(open(config_path))
default_config.update(config)

local_ip = config["local_ip"]
remote_ip = config["remote_ip"]
remote_port = config["remote_port"]
password = config["password"]
port_to_address = config["port_to_address"]
port_to_address = {int(port): tuple(addr) for port, addr in port_to_address.items()}

if "tagged" in config and config["tagged"]:
  encryptor = TaggedXOREncryptor(password)
else:
  encryptor = XOREncryptor(password)
selector = TimedPortSelector(interval=6 * 3600) # Switch port every x hours

event_loop = EventLoop()
ss_local = SSLocalTcp(event_loop,
                      (remote_ip, remote_port),
                      encryptor,
                      selector,
                      port_to_address)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
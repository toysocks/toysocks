from toysocks.server import SSServer
from toysocks.encrypt import XOREncryptor, TaggedXOREncryptor
from toysocks.eventloop import EventLoop
import json
import sys
import logging

logging.basicConfig(level=logging.INFO)

sys.argv = ["", r'E:\shit\keg\toysocks-server-test.json']

if len(sys.argv) == 1:
  config_path = "/root/toysocks.json"
else:
  config_path = sys.argv[1]

config = json.load(open(config_path))

ip = config["ip"]
port = config["port"]
password = config["password"]

if "tagged" in config and config["tagged"]:
  encryptor = TaggedXOREncryptor(password)
else:
  encryptor = XOREncryptor(password)

event_loop = EventLoop()
ss_local = SSServer(event_loop, (ip, port), encryptor)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
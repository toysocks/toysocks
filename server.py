from toysocks.server import SSServer
from toysocks.encrypt import XOREncryptor
from toysocks.eventloop import EventLoop
import json
import sys
import logging

logging.basicConfig(level=logging.INFO)

config_path = "/root/toysocks.json"

config = json.load(open(config_path))

ip = config["ip"]
port = config["port"]
password = config["password"]

encryptor = XOREncryptor(password)

event_loop = EventLoop()
ss_local = SSServer(event_loop, (ip, port), encryptor)
event_loop.add_event(ss_local.coroutine)
event_loop.run_forever()
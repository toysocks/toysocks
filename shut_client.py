import json
import sys
from pathlib import Path
import os
import socket

home = str(Path.home())

config_path = os.path.join(home, "toysocks.json")

config = json.load(open(config_path))

local_port = config["local_port"]

sock = socket.socket()

sock.connect(('127.0.0.1', local_port))
sock.send(b'shutdown')
sock.close()
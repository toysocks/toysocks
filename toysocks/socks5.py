import re
import socket

ipv4_pattern = re.compile(r"(?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])\.){3}(?:(?:2([0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9]))")

def create_greating(methods: list=None):
    if methods is None:
        methods = [0]

    return b'\x05' + bytes([len(methods)]) + bytes(methods)


def decode_greating(greeting: bytes):
  """
    +---------------------+
    | VER | LEN | METHODS |
    +---------------------+
  """
  if len(greeting) < 3:
    raise ValueError("Invalid greeting: %s" % greeting)

  ver, length, methods = greeting[0], greeting[1], greeting[2:]
  return ver, length, set(methods)


def create_connection_request(dest: str, port_num: int):
  dest = dest.encode('utf-8')
              # CMD        # ADDR TYPE
  # return b'\x05\x01\x00' + b'\x03' + bytes([len(dest)]) + dest + int.to_bytes(port_num, 2, "big")
  return b'\x05\x01\x00' + create_socks_addr(dest, port_num)


def create_socks_addr(dest: str, port_num: int):
  if ipv4_pattern.match(dest):
    addr_type = b'\x01'
    addr_bytes = socket.inet_aton(dest) + int.to_bytes(port_num, 2, "big")
  else:
    addr_type = b'\x03'
    addr_length = len(dest.encode("utf-8"))
    addr_bytes = int.to_bytes(addr_length, 1, "big") + dest.encode("utf-8") + int.to_bytes(port_num, 2, "big")

  return addr_type + addr_bytes


def decode_connection_request(request: bytes):
  """
    +-----+----------+----------+-----------+-----------+----------+
    | VER | CMD CODE | RESERVED | ADDR TYPE | DEST ADDR | PORT NUM |
    +-----+----------+----------+-----------+-----------+----------+
    0     1           2          3             #VARIADIC     #2
  """
  ver, cmd_code = request[0], request[1]

  addr_type, dest_addr, port = decode_sock5_addr(request[3:])

  return ver, cmd_code, addr_type, dest_addr, int.from_bytes(port, "big")

def get_socks_addr_bytes_from_request(request: bytes):
  return request[3:]


def encode_connection_repsonse(ver, rep, addr_type, addr : bytes, port):

  port_bytes = [port >> 8, port & (255)]

  return bytes([ver, rep, 0, addr_type]) + addr + bytes(port_bytes)

def bytes_ip_to_string(ip : bytes):
  return ".".join([str(x) for x in ip])

def decode_sock5_addr(request : bytes):
  addr_type = request[0]
  if addr_type == 1:
    dest_addr = request[1 : 5]
    port = request[5 : 5 + 2]
  elif addr_type == 3:
    addr_len = request[1]
    dest_addr = request[1 : 1 + 1 + addr_len]
    port = request[1 + 1 + addr_len : 1 + 1 + addr_len + 2]
  elif addr_type == 4:
    dest_addr = request[1 : 17]
    port = request[17 : 17 + 2]
  else:
    raise ValueError("Invalid request bytes: %s" % addr_type)

  return addr_type, dest_addr, port
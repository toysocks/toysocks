
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
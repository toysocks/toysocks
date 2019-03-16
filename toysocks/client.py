from toysocks.eventloop import AsyncFunc, Future, EventLoop, register_read, register_write, \
  register_read_write, unregister
from selectors import EVENT_WRITE, EVENT_READ
from toysocks.utils import sock_callback, reg_socket_future_read, reg_socket_future_write,\
  close_if, port_to_hex_string, bytes_to_port_num
from toysocks.socks5 import decode_greating, decode_connection_request, \
  encode_connection_repsonse, get_socks_addr_bytes_from_request
from toysocks.utils import SocketFailure, check_socket
from toysocks.relay import relay
from toysocks.encrypt import Encryptor, XOREncryptor, Plain
from toysocks.port_selector import PortSelector

import traceback
import logging
from typing import *
import socket
import random

"""
client <---> ss-local <--[encrypted]--> ss-remote <---> target
"""


class SSLocal(AsyncFunc):
  """
  client <---> ss-local <--[encrypted]--> ss-remote ...
  """

  def __init__(self,
               loop: EventLoop,
               local_addr: Tuple[str, int],
               remote_addr: Tuple[str, Union[int, List[int]]],
               encryptor : Encryptor,
               port_selector: PortSelector):
    self.loop = loop
    self.local_ip, self.local_port = local_addr
    self.remote_ip, self.remote_port = remote_addr
    self.encryptor = encryptor
    self.port_selector = port_selector

  @property
  def coroutine(self):
    return self.run()

  def wait_client_connection(self, local_sock: socket.socket):
    future = Future()
    reg_socket_future_read(future, local_sock)
    yield future
    client_sock, client_addr = local_sock.accept()
    client_sock.setblocking(False)
    logging.info("Connection from %s:%s" % client_addr)
    self.loop.add_event(self.client_handle(client_sock, client_addr))

  def run(self):
    local_sock = socket.socket()
    local_sock.setblocking(False)
    local_sock.bind((self.local_ip, self.local_port))
    local_sock.listen()

    logging.info("Listening on from %s:%s" % (self.local_ip, self.local_port))
    try:
      while True:
        yield from self.wait_client_connection(local_sock)
    finally:
      local_sock.close()

  def client_handle(self, client_sock : socket.socket, client_addr : Tuple[str, int]):
    try:
      yield from self.socks_auth(client_sock, client_addr)
      yield from self.relay_connection(client_sock, client_addr)
    except ValueError as e:
      logging.error(str(e))
    except SocketFailure as e:
      logging.error(str(e))
    except ConnectionAbortedError as e:
      logging.error(str(e))
    except OSError as e:
      logging.error(str(e))
    finally:
      if client_sock.fileno() != -1:
        client_sock.close()

  def socks_auth(self, client_sock : socket.socket, client_addr : Tuple[str, int]):
    """
    Initial greeting from client:
    +---------------------+
    | VER | LEN | METHODS |
    +---------------------+
    """
    future = Future()
    reg_socket_future_read(future, client_sock)
    yield future
    greeting : bytes = client_sock.recv(4096)
    try:
      ver, length, methods = decode_greating(greeting)
      if not ver == 5 or 0 not in methods:
        return
    except ValueError as e:
      raise e

    """
    The server's choice is communicated:
    +-----+--------+
    | VER | METHOD |
    +--------------+
    """
    client_sock.send(bytes([5, 0]))
    # future = Future()
    # reg_socket_future_write(future, client_sock)
    # yield future


  def relay_connection(self, client_sock : socket.socket, client_addr : Tuple[str, int]):
    """
    Address: [1-byte type][variable-length host][2-byte port]
    The client's connection request is:
    +-----+----------+----------+-----------+-----------+----------+
    | VER | CMD CODE | RESERVED | ADDR TYPE | DEST TYPE | PORT NUM |
    +-----+----------+----------+-----------+-----------+----------+
    """
    future = Future()
    reg_socket_future_read(future, client_sock)
    yield future
    check_socket(client_sock)
    request_bytes = client_sock.recv(4096)
    try:
      logging.debug(str(decode_connection_request(request_bytes)))
    except:
      pass

    yield from self.local_relay(client_sock, client_addr, request_bytes)

  def select_port(self, ports: List[int]):
    return self.port_selector.select(ports)

  def local_relay(self, client_sock : socket.socket, client_addr : Tuple[str, int], request_bytes):
    try:
      ver, cmd_code, addr_type, dest_addr, port = decode_connection_request(request_bytes)

      remote_sock = socket.socket()
      remote_sock.setblocking(False)

      try:
        if addr_type == 3:
          #logging.info()
          if isinstance(self.remote_port, int):
            remote_sock.connect((self.remote_ip, self.remote_port))
          elif isinstance(self.remote_port, list):
            port_choice = self.select_port(self.remote_port)
            remote_sock.connect((self.remote_ip, port_choice))
          else:
            raise ValueError(self.remote_port)
        else:
          logging.error("Unknown addr_type: %d" % addr_type)
          return
      except BlockingIOError as e:
        pass

      future = Future()
      reg_socket_future_write(future, remote_sock)
      yield future

      future = Future()
      reg_socket_future_write(future, client_sock)
      yield future

      sock_name = client_sock.getsockname()
      client_hex_addr = socket.inet_aton(sock_name[0])
      client_hex_port = port_to_hex_string(sock_name[1])

      #response = encode_connection_repsonse(ver, 0, addr_type, dest_addr, port)
      response = b'\x05\x00\x00\x01' + client_hex_addr + client_hex_port
      #logging.debug("response:  %r" % response)

      check_socket(client_sock)
      client_sock.send(response)

      def client_data_to_local_data(data : bytes, offset : int):
        if offset == 0:
          sock_addr = get_socks_addr_bytes_from_request(request_bytes)
          whole_data = sock_addr + data

          return self.encryptor.encode(whole_data, offset), + len(sock_addr)
        else:
          whole_data = data
          return self.encryptor.encode(whole_data, offset), 0


      def local_data_to_client_data(data : bytes, offset : int):
        # return self.encryptor.decode(data, offset)
        decoded = self.encryptor.decode(data, offset)
        #logging.debug("data get from remote (%d, %d):\n%s" % (offset, len(decoded), decoded))
        return decoded, 0

      yield from relay(client_sock, remote_sock,
                       client_data_to_local_data, local_data_to_client_data)

    except ValueError as e:
      logging.error(str(e))
      traceback.print_exc()



if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)

  ver, length, methods = decode_greating(bytes([0, 1, 2, 3]))
  print(methods)

  encryptor = XOREncryptor("fuckyouleatherman")
  print(encryptor.xor)
  #encryptor = Plain()

  event_loop = EventLoop()
  ss_local = SSLocal(event_loop, ('127.0.0.1', 2333), ('127.0.0.1', [3456, 2888, 7999]), encryptor=encryptor)
  event_loop.add_event(ss_local.coroutine)
  event_loop.run_forever()

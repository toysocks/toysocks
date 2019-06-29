from toysocks.eventloop import AsyncFunc, Future, EventLoop, register_read, register_write, \
  register_read_write, unregister
from selectors import EVENT_WRITE, EVENT_READ
from toysocks.utils import sock_callback, reg_socket_future_read, reg_socket_future_write,\
  close_if, port_to_hex_string, bytes_to_port_num, reg_multi_sockets_future_read
from toysocks.socks5 import decode_greating, decode_connection_request, \
  encode_connection_repsonse, get_socks_addr_bytes_from_request, bytes_ip_to_string, create_socks_addr
from toysocks.utils import SocketFailure, check_socket, ShutdownException
from toysocks.relay import relay
from toysocks.encrypt import Encryptor, XOREncryptor, Plain, TaggedXOREncryptor
from toysocks.port_selector import PortSelector, TimedPortSelector
import logging

logging.basicConfig(level=logging.INFO)

import traceback
import logging
from typing import *
import socket
import time
import random

"""
client <---> ss-local <--[encrypted]--> ss-remote <---> target
"""


class SSLocalTcp(AsyncFunc):
  """
  client <---> ss-local <--[encrypted]--> ss-remote ...
  """

  def __init__(self,
               loop: EventLoop,
               remote_addr: Tuple[str, Union[int, List[int]]],
               encryptor : Encryptor,
               port_selector: PortSelector,
               port_to_address: Dict[int, Tuple[str, int]]):
    self.loop = loop
    self.remote_ip, self.remote_port = remote_addr
    self.encryptor = encryptor
    self.port_selector = port_selector
    self.port_to_address = port_to_address
    self.local_ports = list(self.port_to_address.keys())

  @property
  def coroutine(self):
    return self.run()

  def wait_client_connection(self, local_socks: List[socket.socket]):
    future = Future()
    reg_multi_sockets_future_read(future, local_socks)
    local_sock = yield future
    client_sock, client_addr = local_sock.accept()
    client_sock.setblocking(False)
    listen_ip, listen_port = client_sock.getsockname()
    dest_addr = self.port_to_address[listen_port]

    self.loop.add_event(self.client_handle(client_sock, client_addr, dest_addr))

  def run(self):
    local_socks = []
    for port in self.local_ports:
      local_sock = socket.socket()
      local_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      local_sock.setblocking(False)
      local_sock.bind(("127.0.0.1", port))
      local_sock.listen()
      local_socks.append(local_sock)

      logging.info("Listening on from %s:%s" % ("127.0.0.1", port))
    try:
      while True:
        yield from self.wait_client_connection(local_socks)
    finally:
      for s in local_socks:
        s.close()

  def client_handle(self,
                    client_sock : socket.socket,
                    client_addr : Tuple[str, int],
                    dest_addr: Tuple[str, int]):
    try:
      yield from self.local_relay(client_sock, client_addr, dest_addr)
    except ValueError as e:
      traceback.print_exc()
      logging.error(str(e))
    except SocketFailure as e:
      traceback.print_exc()
      logging.error(str(e))
    except ConnectionAbortedError as e:
      traceback.print_exc()
      logging.error(str(e))
    except OSError as e:
      traceback.print_exc()
      logging.error(str(e))
    finally:
      if client_sock.fileno() != -1:
        client_sock.close()

  def select_port(self, ports: List[int]):
    return self.port_selector.select(ports)

  def local_relay(self,
                  client_sock : socket.socket,
                  client_addr : Tuple[str, int],
                  dest_addr: Tuple[str, int]
                  ):
    try:

      remote_sock = socket.socket()
      remote_sock.setblocking(False)

      try:
        if isinstance(self.remote_port, int):
          remote_sock.connect((self.remote_ip, self.remote_port))
        elif isinstance(self.remote_port, list):
          port_choice = self.select_port(self.remote_port)
          remote_sock.connect((self.remote_ip, port_choice))
        else:
          raise ValueError(self.remote_port)
      except BlockingIOError as e:
        pass

      logging.info("connected to %s" % (remote_sock.getsockname(),))

      future = Future()
      reg_socket_future_write(future, remote_sock)
      yield future

      sock_addr = create_socks_addr(*dest_addr)
      remote_sock.send(self.encryptor.encode(sock_addr, 0))
      len_sock_addr = len(sock_addr)

      def client_data_to_local_data(data : bytes, offset : int):
        return self.encryptor.encode(data, offset + len_sock_addr), 0


      def local_data_to_client_data(data : bytes, offset : int):
        # return self.encryptor.decode(data, offset)
        decoded = self.encryptor.decode(data, offset)
        #logging.debug("data get from remote (%d, %d):\n%s" % (offset, len(decoded), decoded))
        return decoded, 0

      relay_start = time.time()
      yield from relay(client_sock, remote_sock,
                       client_data_to_local_data, local_data_to_client_data)
      logging.info("[%s:%d] for %r relay used %f" % (client_addr + (dest_addr, time.time() - relay_start)))


    except ValueError as e:
      logging.error(str(e))
      traceback.print_exc()



if __name__ == '__main__':
  pass
  # logging.basicConfig(level=logging.DEBUG)
  #
  # ver, length, methods = decode_greating(bytes([0, 1, 2, 3]))
  # print(methods)
  #
  # encryptor = TaggedXOREncryptor("fuckyouleatherman")
  # #encryptor = Plain()
  #
  # event_loop = EventLoop()
  # ss_local = SSLocal(event_loop,
  #                    ('127.0.0.1', 2333),
  #                    ('127.0.0.1', [3456, 2888, 7999]),
  #                    encryptor=encryptor,
  #                    port_selector=TimedPortSelector(interval=1000))
  # event_loop.add_event(ss_local.coroutine)
  # event_loop.run_forever()

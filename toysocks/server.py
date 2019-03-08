from toysocks.eventloop import AsyncFunc, Future, EventLoop, register_read, register_write, \
  register_read_write, unregister
from selectors import EVENT_WRITE, EVENT_READ
from toysocks.utils import sock_callback, reg_socket_future_read, reg_socket_future_write,\
  close_if
from toysocks.socks5 import decode_greating, decode_connection_request, \
  encode_connection_repsonse
from toysocks.utils import SocketFailure, check_socket, bytes_to_port_num
from toysocks.encrypt import Encryptor, XOREncryptor, Plain
from toysocks.relay import relay
from toysocks.socks5 import decode_sock5_addr

from typing import *
import socket
import logging

class SSServer(AsyncFunc):

  def __init__(self,
               loop: EventLoop,
               remote_addr: Tuple[str, int],
               encryptor : Encryptor):
    self.remote_ip, self.remote_port = remote_addr
    self.encryptor = encryptor
    self.loop = loop

  @property
  def coroutine(self):
    return self.run()

  def run(self):

    local_sock = socket.socket()
    local_sock.setblocking(False)
    local_sock.bind((self.remote_ip, self.remote_port))
    local_sock.listen()

    logging.info("Listening at %s:%s" % (self.remote_ip, self.remote_port))

    try:
      while True:
        yield from self.wait_client_connection(local_sock)
    finally:
      local_sock.close()

  def wait_client_connection(self, remote_sock: socket.socket):
    future = Future()
    reg_socket_future_read(future, remote_sock)
    yield future
    local_sock, local_addr = remote_sock.accept()
    local_sock.setblocking(False)
    logging.info("Connection from %s:%s" % local_addr)
    self.loop.add_event(self.local_handle(local_sock, local_addr))

  def local_handle(self, local_sock : socket.socket, local_addr : Tuple[str, int]):
    try:
      yield from self.server_relay(local_sock, local_addr)
    except ValueError as e:
      logging.error(str(e))
    except SocketFailure as e:
      logging.error(str(e))
    except ConnectionAbortedError as e:
      logging.error(str(e))
    except OSError as e:
      logging.error(str(e))
    finally:
      if local_sock.fileno() != -1:
        local_sock.close()

  def server_relay(self, local_sock, local_addr):

    server_sock = socket.socket()
    server_sock.setblocking(False)

    def local_data_to_server_data(data : bytes, offset : int):
      logging.debug("offset = %d, |data|: %d" % (offset, len(data)))
      decoded_data = self.encryptor.decode(data, offset)
      logging.debug("|decoded_data|: %d" % len(data))
      if offset == 0:
        addr_type, dest_addr, port = decode_sock5_addr(decoded_data)
        if addr_type != 3: # TODO: Type 1 and Type 4
          raise ValueError("Only url is supported! Sorry!")
        if addr_type == 3:
          real_addr = dest_addr[1:]
          try:
            logging.debug("Connecting to %s:%s" % (real_addr.decode('utf-8'), bytes_to_port_num(port)))
            server_sock.connect((real_addr.decode('utf-8'), bytes_to_port_num(port)))
          except BlockingIOError:
            pass

        logging.debug("head len: %d" % (1 + len(dest_addr) + len(port)))
        logging.debug("data recv from local:\n%s" % decoded_data[1 + len(dest_addr) + len(port): ])
        return decoded_data[1 + len(dest_addr) + len(port):], 0
      else:
        return decoded_data, 0

    def server_to_local_data(data : bytes, offset : int):
      encoded = self.encryptor.encode(data, offset)
      #logging.debug("data get from server (%d, %d):\n%s" % (offset, len(data), data))
      return encoded, 0

    yield from relay(local_sock, server_sock, local_data_to_server_data, server_to_local_data)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)

  ver, length, methods = decode_greating(bytes([0, 1, 2, 3]))
  print(methods)

  encryptor = XOREncryptor("fuckyouleatherman")
  print(encryptor.xor)
  #encryptor = Plain()

  event_loop = EventLoop()
  ss_local = SSServer(event_loop, ('127.0.0.1', 3456), encryptor)
  event_loop.add_event(ss_local.coroutine)
  event_loop.run_forever()


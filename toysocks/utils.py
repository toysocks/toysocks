import socket
from toysocks.eventloop import Future, unregister, register_read, register_write
from typing import *

def sock_callback(future : Future, sock : socket.socket, value=None):
  def cb(*args, **kwargs):
    unregister(sock.fileno())
    future.set_result(value)
  return cb

def reg_socket_future_read(f : Future, sock : socket.socket, value=None):
  register_read(sock.fileno(), sock_callback(f, sock, value))

def reg_socket_future_write(f : Future, sock : socket.socket, value=None):
  register_write(sock.fileno(), sock_callback(f, sock, value))

def close_if(cond : bool, sock : socket.socket):
  if cond:
    sock.close()

class SocketFailure(Exception):
  def __init__(self, message):
    # Call the base class constructor with the parameters it needs
    super(Exception, self).__init__(message)

def check_socket(sock : socket.socket):
  if sock.fileno() == -1:
    raise SocketFailure(str(sock) + " has an issue. ")


def port_to_hex_string(int_port):
  port_hex_string = bytes([int_port // 256, int_port % 256])
  return port_hex_string


def bytes_to_port_num(b : bytes):
  return 256 * b[0] + b[1]
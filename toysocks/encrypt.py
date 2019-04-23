from typing import *
import hashlib
import time

class Encryptor:

  def encode(self, data : bytes, offset : int = 0) -> bytes:
    raise NotImplementedError()

  def decode(self, data : bytes, offset : int = 0) -> bytes:
    raise NotImplementedError()

class XOREncryptor(Encryptor):

  def __init__(self, password : str):
    sha = hashlib.sha512()
    sha.update(password.encode('utf-8'))
    self.xor = sha.digest()

  def encode(self, data : bytes, offset : int = 0) -> bytes:
    return bytes([ self.xor[(offset + i) % len(self.xor) ] ^ data[i] for i in range(len(data)) ])

  def decode(self, data : bytes, offset : int = 0) -> bytes:
    return self.encode(data, offset)

class TaggedXOREncryptor(Encryptor):

  def __init__(self, password : str):
    self.xor_encoder = XOREncryptor(password)

  def encode(self, data : bytes, offset : int = 0) -> bytes:
    if offset == 0:
      return b'\xee' + self.xor_encoder.encode(data, offset)
    else:
      return self.xor_encoder.encode(data, offset)

  def decode(self, data : bytes, offset : int = 0) -> bytes:
    if offset == 0:
      return self.xor_encoder.encode(data[1:], offset)
    else:
      return self.xor_encoder.encode(data, offset - 1)


class Plain(Encryptor):

  def encode(self, data : bytes, offset : int = 0) -> bytes:
    return data

  def decode(self, data : bytes, offset : int = 0) -> bytes:
    return data

if __name__ == '__main__':
  xorenc = XOREncryptor("password")

  # data = "fuck you leatherman".encode('utf-8')
  #
  # encoded = xorenc.encode(data)
  # print(encoded)
  # print(len(encoded))
  #
  # decoded = xorenc.decode(encoded)
  # print(decoded)
  # print(len(decoded))
  #
  # data = open(__file__).read().encode('utf-8')
  #
  # encoded = xorenc.encode(data, 222)
  # print(encoded)
  # print(len(encoded))
  #
  # decoded = xorenc.decode(encoded, 222)
  # print(decoded)
  # print(len(decoded))
  #
  # part1 = b"aaaaaaaaaa"
  # part2 = b"aaaaaaaaaaaaaaaaa"
  #
  # abcd = xorenc.encode(part1) + xorenc.encode(part2, len(part1))
  # decoded = xorenc.decode(abcd[0:20], ) + xorenc.decode(abcd[20:], 20)
  # print(decoded)

  x2 = XOREncryptor2("password")
  t1 = time.time()
  for i in range(30000):
    x2.encode(b"a" * 1024)
  print(time.time() - t1)

  t1 = time.time()
  for i in range(30000):
    xorenc.encode(b"a" * 1024)
  print(time.time() - t1)
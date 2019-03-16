from typing import *
import hashlib

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

class Plain(Encryptor):

  def encode(self, data : bytes, offset : int = 0) -> bytes:
    return data

  def decode(self, data : bytes, offset : int = 0) -> bytes:
    return data

if __name__ == '__main__':
  xorenc = XOREncryptor("password")

  data = "fuck you leatherman".encode('utf-8')

  encoded = xorenc.encode(data)
  print(encoded)
  print(len(encoded))

  decoded = xorenc.decode(encoded)
  print(decoded)
  print(len(decoded))

  data = open(__file__).read().encode('utf-8')

  encoded = xorenc.encode(data, 222)
  print(encoded)
  print(len(encoded))

  decoded = xorenc.decode(encoded, 222)
  print(decoded)
  print(len(decoded))

  part1 = b"aaaaaaaaaa"
  part2 = b"aaaaaaaaaaaaaaaaa"

  abcd = xorenc.encode(part1) + xorenc.encode(part2, len(part1))
  decoded = xorenc.decode(abcd[0:20], ) + xorenc.decode(abcd[20:], 20)
  print(decoded)
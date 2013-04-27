#!/usr/bin/python
from socket import * 
from threading import Thread
import daemon
import logging
import serial
import time
import sys
import os

ser = None
allClients = []
BUFSIZ = 1024
serialDevice = ''

def serialReader():
  global ser
  global allClients
  global serialDevice
  while 1:
    try:
      # configure the serial connections (the parameters differs on the device you are connecting to)
      ser = serial.Serial(
        port=serialDevice,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
      )

#     ser.open()     # Doesn't seem to be needed
      ser.isOpen()
      logging.info('Serial port opened %s', ser)
      while 1:
        out = ser.read(1)
        for client in allClients:
          client.send(out)

    except:
      # Wait a while then try again
      logging.debug('Error on serial port')
      if ser is not None:
        ser.close()
      ser = None
      time.sleep(10)

def handler(clientsock,addr):
  global ser
  global allClients
  logging.info('connected from: %s', addr)
  allClients.append(clientsock)
  while 1:
    data = clientsock.recv(BUFSIZ)
    if not data: 
      break 
    if not (ser is None):
      ser.write(data)
  logging.debug('disconnected from: %s', addr)
  allClients.remove(clientsock)
  clientsock.close()

def mainProgram():
  global serialDevice
  global port
  if len(sys.argv)>=4 and sys.argv[1] == '-p':
    writePidFile(sys.argv[2])
    del sys.argv[2]
    del sys.argv[1]
  if len(sys.argv) != 3:
    print 'usage: ', sys.argv[0], ' device port'
    exit()
 
  logging.basicConfig(filename='/var/log/serproxy.log', filemode='w', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)

  serialDevice=sys.argv[1]
  port=int(sys.argv[2])

  Thread(target=serialReader).start()

  ser = None
  allClients = []

  listenAddr = ('', port)
  try:
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.bind(listenAddr)
    serversock.listen(2)
    logging.info('waiting for connection')

    while 1:
      clientsock, addr = serversock.accept()
      Thread(target=handler, args=(clientsock, addr)).start()
  except KeyboardInterrupt:
    if not ser is None:
      ser.close()
    os._exit(0)

def writePidFile(pidfile):
    pid = str(os.getpid())
    f = open(pidfile, 'w')
    f.write(pid)
    f.close()

if __name__=='__main__':
  if len(sys.argv)>=4 and sys.argv[1] == '-d':
    del sys.argv[1]
    with daemon.DaemonContext():
      mainProgram()  
  else:
    mainProgram()

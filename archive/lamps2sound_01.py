#! /usr/bin/python

import OSC
import time
from xbee import XBee
import serial
import os

PORT = '/dev/ttyAMA0'
BAUD_RATE = 9600


# Open serial port
ser = serial.Serial(PORT, BAUD_RATE)

# Open Pure Data
#os.system("pd -nogui -noadc -alsa ./lamps2sound.pd")

# Init OSC
client = OSC.OSCClient()
client.connect(('127.0.0.1', 9001))


# Create API object
xbee = XBee(ser)

while True :
	response = xbee.wait_read_frame()
	print response
	try:
		client.send(OSC.OSCMessage("/lamp",ord(response.get("rf_data")[0])))
	except:
		print "not connected"
		pass

       
ser.close()
os.system("killall pd")

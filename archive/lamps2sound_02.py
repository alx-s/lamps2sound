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
#os.system("killall pd")
#os.system("pd -nogui -noadc -alsa ./lamps2sound.pd")

# Init OSC
client = OSC.OSCClient()
client.connect(('127.0.0.1', 9001))


# Create API object
xbee = XBee(ser)

try:
	while True :
		response = xbee.wait_read_frame()
		print response
		try:
			lamp = ord(response.get("rf_data")[1])
			activity = ord(response.get("rf_data")[0])
			red = ord(response.get("rf_data")[2])
			green = ord(response.get("rf_data")[3])
			blue = ord(response.get("rf_data")[4])
			client.send(OSC.OSCMessage("/lamp",[lamp, activity, red, green, blue]))
		except:
			print "Can not send to pure data"
			pass
except KeyboardInterrupt:
#	os.system("killall pd")
	ser.close()

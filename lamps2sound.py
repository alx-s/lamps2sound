#! /usr/bin/python

import OSC
import time
from xbee import XBee
import serial
import os
import RPi.GPIO as GPIO

PORT = '/dev/ttyAMA0'
BAUD_RATE = 9600

GPIO.setmode(GPIO.BCM)
DEBUG = 1


## Open serial port ##
ser = serial.Serial(PORT, BAUD_RATE)


## Open Pure Data
#os.system("killall pd")
#os.system("pd -nogui -noadc -alsa -audiooutdev 1 -outchannels 6 ./lamps2sound.pd &")
#os.system("pd -nogui -noadc -alsa -audiooutdev 1 -outchannels 6 ../test_6-channels.pd &")

## Init OSC ##
client = OSC.OSCClient()
client.connect(('127.0.0.1', 9001))

## Maximum volume to deal with the power of the amplifiers ##
maxVol = 50 #maxVol must be set between 0 and 100

## Define analog reading used for volume control ##

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

# 10k trim pot connected to adc #0
potentiometer_adc = 0;

last_read = 0       # this keeps track of the last potentiometer value
tolerance = 5       # to keep from being jittery we'll only change
                    # volume when the pot has moved more than 5 'counts'


## Create API object ##
xbee = XBee(ser)

## Looping part of the code ##
try:
	while True :
		## Volume Management part ##
	        trim_pot_changed = False
     		trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
       		pot_adjust = abs(trim_pot - last_read)
		if ( pot_adjust > tolerance ):
                	trim_pot_changed = True
		if ( trim_pot_changed ):
                	set_volume = trim_pot / 10.24           # convert 10bit$
                	set_volume = round(set_volume)          # round out dec$
               		set_volume = int(set_volume)            # cast volume a$

                	print 'Volume = {volume}%' .format(volume = set_volume*maxVol/100)
	                set_vol_cmd = 'sudo amixer cset numid=2 -- {volume}% > /dev/null' .format(volume = set_volume)
                	os.system(set_vol_cmd)  # set volume

		last_read = trim_pot


		## data received from lamps' management ##
		response = xbee.wait_read_frame()
		#print response
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
		time.sleep(0.3/7) # 7 data sent in an approximately 300ms loop?? 
except KeyboardInterrupt:
#	os.system("killall pd")
	GPIO.cleanup()
	ser.close()
	

import machine											#import libraries and define global variables and setup pins
from data_collect import readdata, data_convert			#import readdata and data_convert function from data_collect.py 
import math
from array import *
import time
import ujson
import network
from umqtt.simple import MQTTClient
#--------------------------Initializing Output Pins---------------------------------------------
p12 =machine.Pin(12)								
pwm12 = machine.PWM(p12)								#PWM initialized as input for buzzer
p13 =machine.Pin(13)								
led2 = machine.PWM(p13)									#PWM initialized for LED2
p14 =machine.Pin(14)
led1 = machine.PWM(p14)									#PWM initialized for LED1
p15 =machine.Pin(15)
led3 = machine.PWM(p15)									#PWM initialized for LED3
seg_dis_agd = machine.Pin(16,machine.Pin.OUT)			#3.3V DC output pin initialized for a,g,d pins on 7 segments display
seg_dis_c = machine.Pin(2,machine.Pin.OUT)				#3.3V DC output pin initialized for c pin on 7 segments display
seg_dis_e = machine.Pin(0,machine.Pin.OUT)				#3.3V DC output pin initialized for e pins on 7 segments display
#--------------------------Set Default Info for publishment------------------------------------
SERVER = "192.168.0.10"									# Define SERVER ID
CLIENT_ID = "LJJ"										# Define CLIENT_ID
TOPIC = "esys/LJJ/"										# Define TOPIC

led1.freq(1000)											# Set LED with PWM frequency of 1000
led2.freq(1000)										
led3.freq(1000)
#--------------------------List of function that are used in the main loop---------------------
def connectwifi():
	ap_if = network.WLAN(network.AP_IF)
	ap_if.active(False)									#Disable automatic access point to reduce overheads
	sta_if = network.WLAN(network.STA_IF)
	sta_if.active(True)									#Activate station interface
	sta_if.connect('EEERover','exhibition')				#Connect to a specified WiFi network
	if sta_if.isconnected():
		print ("connected!")
	else:
		print("not connected!")

def publish(message):									#functions which publish the messages to the broker (sensor data and actions)
	client = MQTTClient(CLIENT_ID,SERVER)
	client.connect()
	client.publish("esys/LJJ/",message)

def sensor_lux(data_arr):											# function for sending readable luminosity data
	for i in range(0,3):
        text = ujson.dumps({'Light intensity': 'Sensor %d' % i, 'data': '%d' % data_arr[i])
        publish(text)

def send_volume(vol):												# function for sending volume level to broker
    vol_str = ''
    if(vol == 1):
        vol_str = 'low'
    elif(vol == 2):
        vol_str = 'medium'
    elif(vol == 3):
        vol_str = 'high'
    text = ujson.dumps({'action': 'Current volume level is %s' % vol_str})
    publish(text)

def send_music(track):												# function for sending music track number
    text = ujson.dumps({'action': 'Switch to track No. %d' % (track + 1)})
    publish(text)

def play_or_pause(play):											# function for sending play or pause messages
	if play == 1:
		text = ujson.dumps({'action': 'Play!'})
	else:
		text = ujson.dumps({'action': 'Paused!'})
	publish(text)
#-------------------Set Default values returned from sensor------------------------------------
threshold = readdata()												# read initial luminosity and record as reference 
data_sum = threshold[0] + threshold[1] + threshold[2]
data_avg = data_sum/3
low_vol = data_avg * 0.15											# Setting low level volume threshold
med_vol = data_avg * 0.3											# Setting medium level volume threshold
#-------------------Frequency constant for different notes-------------------------------------
C3=const(131)														#frequency of music scales 
D3=const(147)
E3=const(165)
F3=const(175)
G3=const(196)
A3=const(220)
B3=const(247)
C4=const(262)
D4=const(294)
E4=const(330)
F4=const(349)
G4=const(392)
A4=const(440)
B4=const(494)
rest=const(0) 
#--------------------Our Tracks----------------------------
tone3 = array('I',[E4,D4,C4,D4,E4,E4,E4,D4,D4,D4,E4,G4,G4,E4,D4,C4,D4,E4,E4,E4,D4,D4,E4,D4,C4,rest]) #sheep
tone2 = array('I',[E4,E4,E4,rest,E4,E4,E4,rest,E4,G4,C4,D4,E4,rest,F4,F4,F4,F4,F4,E4,E4,E4,E4,D4,D4,E4,D4,rest,G4,rest,E4,E4,E4,rest,E4,E4,E4,rest,E4,G4,C4,D4,E4,rest,F4,F4,F4,F4,F4,E4,E4,E4,G4,G4,F4,D4,C4,rest]) #jingle bells
tone1 = array('I',[G3,A3,C4,D4,E4,rest,G3,A3,C4,D4,E4,rest,E4,D4,C4,D4,A3,rest,A3,C4,A3,D4,G3,rest,G4,G4,D4,D4,E4,rest,E4,D4,C4,D4,E4,rest,E4,D4,C4,D4,A3,rest,A3,C4,A3,D4,rest,rest]) #springnew(by Mr Wang)
#--------------------Main Loop-----------------------------
def play():
	connectwifi()
	global state,wait,pause,song,volume_sensed,volume_fin,sensordata	# global variables (actions) used in statechange function
	state = 0															# Default state for the FSM
	wait = 0
	pause = False														# Pause is initially set as False so song playing
	temp_pause = False													# Temporary memory for pause, used for determine when to send pause message
	song = 0															# Action of switch song, when +1 switch to next song, -1 switch to previous song
	sensordata = 0000													# Define as the input for FSM
	volume_sensed = 0													# Sensed volume from input
	volume_fin = 1														# Final volume for the buzzer
	volume_temp = 0														# Temporary memory for volume to determine when to send volume level message
	music_temp = 0														# Temporary memory for music track number to determine when to send music message
	music = 0															# Default playing track 1
	i = 0																# initialize iteration variable for arrays

	while True :
		for k in range(0,3):											# use a for loop to read sensor data three times for each tone
			sensordata = sensormsg(sensordata)							# read sensor data
			state,wait,pause,song,volume_sensed,volume_fin= statechange(sensordata,state,wait,volume_sensed,pause,song,volume_fin) #use sensor data and apply them to the statechane function to get the new state
			print(sensordata,state,wait,song,volume_sensed,volume_fin,pause)
			#sensor_lux(readdata())
			if pause and temp_pause == False:							# Send Pause message
				play_or_pause(0)
				temp_pause = pause										# temp_pause state equals the pause state
			elif temp_pause and pause == False:							# Send Play message
				play_or_pause(1)
				temp_pause = pause
			
			if volume_fin != volume_temp:								# Send volume level message
				send_volume(volume_fin)
				volume_temp = volume_fin								# volume_temp level equals volume_fin level

			if music != music_temp:										# Send music track number
				send_music(music)
				music_temp = music
			
			if volume_fin == 1:
				led1.duty(512)											# Light up first LED
				led2.duty(0)
				led3.duty(0)
			elif volume_fin == 2:
				led1.duty(512)											# Light up 2 LEDs
				led2.duty(512)
				led3.duty(0)
			elif volume_fin == 3:
				led1.duty(512)											# Light up all 3 LEDs
				led2.duty(512)
				led3.duty(512)
			while pause:
				sensordata = sensormsg(sensordata)						# Data still collecting while pauseing, if play action sensed, Pause is False and escape the loop
				state,wait,pause,song,volume_sensed,volume_fin = statechange(sensordata,state,wait,volume_sensed,pause,song,volume_fin)
				print(sensordata,state,wait,song,volume_sensed,volume_fin,pause)
				pwm12.duty(0)
				pwm12.duty
				time.sleep_ms(50)
			if song != 0:												# No song switch action detected
				music = (music + song)%3								# Total 3 songs therefore loop to the first one if overheads
				i = 0
				song = 0
			if music == 0:												# Play first song
				seg_dis_c.on()											# 7_seg display 1
				seg_dis_agd.off()
				seg_dis_e.off()
				if i==len(tone1):										# Song reloaded from the start
					i = 0
				pwm12.freq(tone1[i])
				if tone1[i] == 0:
					pwm12.duty(0)
				else:
					pwm12.duty(volume_fin*100)
			elif music == 1:											# Play second song
				seg_dis_agd.on()										# 7_seg display 2
				seg_dis_c.off()
				seg_dis_e.on()
				if i==len(tone2):
					i = 0
				pwm12.freq(tone2[i])
				if tone2[i] == 0:
					pwm12.duty(0)
				else:
					pwm12.duty(volume_fin*100)
			elif music == 2:											# Play third song
				seg_dis_agd.on()										# 7_seg display 3
				seg_dis_e.off()
				seg_dis_c.on()
				if i==len(tone3):
					i = 0
				pwm12.freq(tone3[i]) 
				if tone3[i] == 0:
					pwm12.duty(0)
				else:
					pwm12.duty(volume_fin*100)
			pwm12.duty
			time.sleep_ms(100)											# the duration of 1/3 of a time signature in music
		i+=1															# iterator + 1
		pwm12.duty(0)
		time.sleep_ms(20)												# small gap between music for rythme purpose

#def stop():
#	pwm12.duty(0)
#	pwm12.duty
	
def statechange(msg,state,wait,volume_sensed,pause,song,volume_fin):	#this algorithm use the concept of FSM to represent different actions
	wait_song_sw = 20													#define wait time for different actions
	wait_pause = 5
	wait_vol_ctrl = 10
																		
	if state == 0:														#initial state, also used to detect pause action
		if wait < wait_pause:
			if msg == 1000:
				state = 1
				wait = 0
			if msg == 0010:
				state = -1
				wait = 0
			if msg == 0100:
				wait += 1
			if int(msg/10) == 111:										#enter volume control mode
				state =5
				volume_sensed = msg%10									#extract the last digit, which is the volume level
				wait = 0
			if msg == 0000:
				wait = 0
		else: 
			if msg == 0000 :
				pause = not pause										#hand released, so active the pause action and reset the wait
				wait = 0
	elif state == 1:													#enter this state when the first sensor has triggered
		if wait <wait_song_sw:
			if msg== 0000:
				wait += 1
			elif msg ==1000:
				wait += 1
			elif msg == 0100:
				state = 2
				wait = 0
			elif int(msg/10) == 111: 
				state =5
				volume_sensed = msg%10	
				wait = 0 
			else: 
				state = 0
				wait = 0
	
		else: 
			state = 0
			wait = 0

	elif state == 2:													#enter this state when the first and second sensor has triggered
		if wait <wait_song_sw:
			if msg == 0000:
				wait += 1
			elif msg == 0100:
				wait += 1
			elif msg == 0010:
				song = 1
				state = 0
				wait = 0 
			elif int(msg/10) == 111 : 
				state = 5
				volume_sensed = msg%10
				wait = 0	 
			else: 
				state = 0
				wait = 0
		else: 
			state = 0
			wait = 0

	elif state == -1:													#state used for reverse switching of songs
		if wait <wait_song_sw:
			if msg == 0000:
				wait += 1
			elif msg == 0010:
				wait += 1
			elif msg == 0100:
				state = -2
				wait = 0
			elif int(msg/10) == 111: 
				state =5
				volume_sensed = msg%10
				wait = 0 
			else: 
				state = 0
				wait = 0
		else: 
			state = 0
			wait = 0
	elif state == -2:													#state used for reverse switching of songs
		if wait <wait_song_sw:
			if msg == 0000:
				wait += 1
			elif msg == 0100:
				wait += 1
			elif msg == 1000:
				song = -1
				state = 0
				wait = 0 
			elif int(msg/10) == 111: 
				state = 5
				volume_sensed = msg%10
				wait = 0	 
			else:
				state = 0
				wait = 0
	
		else: 
			state = 0
			wait = 0
	elif state == 5:													#state used for volume control
		if int(msg/10) ==111:											
			if wait < wait_vol_ctrl:
				if msg%10 == volume_sensed:								#counter used for avoiding sensor to be covered by mistake
					wait +=1
				else:
					wait = 0
					volume_sensed = msg%10
			else: 
				#stateled.duty(512)
				#stateled.freq(1000)
				volume_fin = volume_sensed
				state = 0
				wait = 0
		else:
			state = 0
			wait = 0
	return state,wait,pause,song,volume_sensed,volume_fin

def sensormsg(sensordata):  #the sensor data msg has four digits, the first three represent the three sensor's state(on/off), the last digits used for volume control, which is the actual luminosity(percentage of threshold)
	real_time = readdata()												#collecting data from sensors
	vc_init = [x * 0.6 for x in threshold]								#set threshold for distinguish dark and light condition 
	vc_init = [round(x) for x in vc_init]								#transfer threshold from float to integer 
	if (real_time[0] < vc_init[0] and real_time[1] < vc_init[1] and real_time[2] < vc_init[2]):
		real_time_sum = real_time[0] + real_time[1] + real_time[2]		
		real_time_avg = real_time_sum / 3								#calculate the average luminosity of three sensors
		if (real_time_avg < low_vol):
			sensordata = 1111											#low level
		elif (real_time_avg > med_vol):
			sensordata = 1113											#high level
		else:
			sensordata = 1112											#medium level
	elif(real_time[0] < vc_init[0]):
		sensordata = 0010												#third sensor triggered
	elif(real_time[1] < vc_init[1]):
		sensordata = 0100												#second sensor triggered
	elif(real_time[2] < vc_init[2]):
		sensordata = 1000												#first sensor triggered
	else:
		sensordata = 0000
	return sensordata

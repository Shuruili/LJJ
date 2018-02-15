import machine

i2c = machine.I2C(scl=machine.Pin(5),sda=machine.Pin(4),freq=100000)		# Define i2c member from I2C class, define scl Pin as Pin 5, define sda Pin as Pin 4
i2c.writeto_mem(0x49,0x0,bytearray([0x03]))			#ADDR connect to 3.3V, sensor slave address = 0x49
													#0x0 -> 0h -> Control Register
													#Control Register 0x03 = 0011 -> POWER UP, 0x00 -> POWER OFF
i2c.writeto_mem(0x39,0x0,bytearray([0x03]))			#ADDR floating, sensor slave address = 0x39
i2c.writeto_mem(0x29,0x0,bytearray([0x03]))

def readdata():
	datalow_vis1 = i2c.readfrom_mem(0x39, 0x8C, 1) # COMMAND REGISTER 0x8 = 1000, 0xC = DATA0LOW, 1 byte data
	datahigh_vis1 = i2c.readfrom_mem(0x39, 0x8D, 1)	#C,D are CH0 register responsible for collecting visible light and IR data
	datalow_IR1 = i2c.readfrom_mem(0x39, 0x8E, 1)	
	datahigh_IR1 = i2c.readfrom_mem(0x39, 0x8F, 1)	#E,F are CH1 register responsible for collecting IR data
	datalow_vis1 = int.from_bytes(datalow_vis1,'big')  # convert to integer from byte, byteorder = 'big' -> MSB at beginning of byte array
	datahigh_vis1 = int.from_bytes(datahigh_vis1, 'big')
	#print(datalow_vis1)
	#print(datahigh_vis1)
	datalow_IR1 = int.from_bytes(datalow_IR1,'big')
	datahigh_IR1 = int.from_bytes(datahigh_IR1,'big')
	data_vis1 = datalow_vis1 + 256 * datahigh_vis1
	data_IR1 = datalow_IR1 + 256 * datahigh_IR1
	data1 = round(data_convert(data_vis1, data_IR1))	#using mathematical equations given in the datasheet and convert raw data to readable lux data

	datalow_vis2 = i2c.readfrom_mem(0x49, 0x8C, 1) # COMMAND REGISTER 0x8 = 1000, 0xC = DATA0LOW, 1 byte data
	datahigh_vis2 = i2c.readfrom_mem(0x49, 0x8D, 1)	
	datalow_IR2 = i2c.readfrom_mem(0x49, 0x8E, 1)
	datahigh_IR2 = i2c.readfrom_mem(0x49, 0x8F, 1)
	datalow_vis2 = int.from_bytes(datalow_vis2,'big')  # convert to integer from byte, byteorder = 'big' -> MSB at beginning of byte array
	datahigh_vis2 = int.from_bytes(datahigh_vis2, 'big')
	#print(datalow_vis2)
	#print(datahigh_vis2)
	datalow_IR2 = int.from_bytes(datalow_IR2,'big')
	datahigh_IR2 = int.from_bytes(datahigh_IR2,'big')
	data_vis2 = datalow_vis2 + 256 * datahigh_vis2
	data_IR2 = datalow_IR2 + 256 * datahigh_IR2
	data2 = round(data_convert(data_vis2, data_IR2))
	
	datalow_vis3 = i2c.readfrom_mem(0x29, 0x8C, 1) # COMMAND REGISTER 0x8 = 1000, 0xC = DATA0LOW, 1 byte data
	datahigh_vis3 = i2c.readfrom_mem(0x29, 0x8D, 1)
	datalow_IR3 = i2c.readfrom_mem(0x29, 0x8E, 1)
	datahigh_IR3 = i2c.readfrom_mem(0x29, 0x8F, 1)
	datalow_vis3 = int.from_bytes(datalow_vis3,'big')  # convert to integer from byte, byteorder = 'big' -> MSB at beginning of byte array
	datahigh_vis3 = int.from_bytes(datahigh_vis3, 'big')
	#print(datalow_vis3)
	#print(datahigh_vis3)
	datalow_IR3 = int.from_bytes(datalow_IR3,'big')
	datahigh_IR3 = int.from_bytes(datahigh_IR3,'big')
	data_vis3= datalow_vis3 + 256 * datahigh_vis3
	data_IR3 = datalow_IR3 + 256 * datahigh_IR3
	data3 = round(data_convert(data_vis3, data_IR3))

	return [data1, data2, data3]

def data_convert(Full_Spec, IR):					# Equations are given in the datasheet
	ratio = IR/Full_Spec							# Calculate ratio between IR and Full Spectrum light(visible light and IR)
	if ratio > 1.3:
		return 0
	elif ratio > 0.8:
		return (0.00146 * Full_Spec - 0.00112 * IR)
	elif ratio > 0.61:
		return (0.0128 * Full_Spec - 0.0153 * IR)
	elif ratio > 0.5:
		return (0.0224 * Full_Spec - 0.031 * IR)
	else:
		power = ratio**1.4
		return (0.0304 * Full_Spec - 0.062 * Full_Spec * power)
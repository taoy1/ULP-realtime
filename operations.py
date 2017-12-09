import re

#
# Generate the execution assembly code if input of this sensor 
# is IO instead of another sensor with higher frequency.
#
# Params:
# sensor: name of this sensor (sanitized)
# op: operations to conduct on the input, currently only null
# input: input of this sensor in the JSON file
# out_buf: variable name of the output buffer in the assembly
# out_bufsize: variable name of the size of output buffer in the assembly
# out_idx: variable name of the index of output buffer in the assembly
# is_pingpong: if the output is used by CPU, is needs pingpong buffer

def parsePingpong(program, is_pingpong):
	m = re.search('{if is_pingpong}', program)
	program_half1 = program[:m.start()]
	program_half2 = program[program.find('{endif}', m.end())+len('{endif}'):]

	if is_pingpong:
		if_branch = program[m.end():program.find('{else}', m.end())]
		program = program_half1 + if_branch + program_half2
	else:
		else_branch = program[program.find('{else}', m.end())+len('{else}'):program.find('{endif}', m.end())]
		program = program_half1 + else_branch + program_half2
	return program

def generateProgramIO(sensor, op, input, out_buf, out_bufsize, out_idx, is_pingpong):
	if op == "null":
		if input.startswith("ADC_"):
			print("------------- Generating adc -------------\r\n")
			ADC_N = int(input[4:])
			program = open('templates/operations/adc.S').read()
			program = re.sub('adc_channel', str(ADC_N), program)
	program = re.sub('out_bufsize', out_bufsize, program)
	program = re.sub('out_buf', out_buf, program)
	program = re.sub('out_idx', out_idx, program)
	program = re.sub('\[s\]', sensor, program)

	program = parsePingpong(program, is_pingpong)	

	return program

def generateProgramBuf(sensor, op, in_buf, out_buf, in_bufsize, in_bufsize_num, out_bufsize, out_idx, is_pingpong):
	if op == "null":
		return "\r\n"
	elif op == "sum":
		print("------------- Generating sum -------------\r\n")
		ret = ""
		program = open('templates/operations/sum.S').read()
		program = re.sub('<<[^>]*>>\r*\n*', '', program)
		program = re.sub('in_bufsize', in_bufsize, program)
		program = re.sub('out_bufsize', out_bufsize, program)
		program = re.sub('in_buf', in_buf, program)
		program = re.sub('out_buf', out_buf, program)
		program = re.sub('out_idx', out_idx, program)
		program = re.sub('\[s\]', sensor, program)

		program = parsePingpong(program, is_pingpong)

		last = 0
		for m in re.finditer('{{[^}]*}}', program):
			ret += program[last:m.start()]
			for i in range(0, in_bufsize_num):
				s = program[m.start()+2:m.end()-2]
				s = re.sub('\[4d\]', str(i*4), s)
				ret += s + "\r\n"
			last = m.end()
		ret += program[last:]

		return ret
	else:
		sys.exit("Cannot handle operation <%s> of sensor <%s>." % (op, sensor))


# print(generateProgramBuf("sensor_1", "sum", "buf_sensor_1", "buf_sensor_2", "bufsize_sensor_1", 10, "bufsize_sensor_2", "buf_idx_sensor_2"));
# print(generateProgramIO("sensor_1", "null", "ADC_6", "buf_sensor_2", "bufsize_sensor_2", "buf_idx_sensor_2"))
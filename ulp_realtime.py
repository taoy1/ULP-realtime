import os, sys, re, json
from pprint import pprint
from fractions import gcd
import operations

################ Constants ################
ULP_no_work_runtime = 162 # As measured, the current template's nop running time is 162 microseconds
pingpong_min_interval_us = 1000000 # If CPU cannot run too frequently too keep the timing correct
instructions_1_cycle = ['add', 'sub', 'and', 'or', 'move', 'nop']
instructions_2_cycle = ['ld', 'st']
time_ALU = 4.622
################ Functions ################

def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)

def is_input_IO(s_input):
	return s_input.startswith("ADC") or s_input.startswith("GPIO")

def generateProgram(config, clusters, char):
	i = ord(char) - ord('a')
	intervals = sorted(clusters.keys())
	s_interval = intervals[i]

	program = ""
	for sensor in clusters[s_interval]:
		input = config[sensor]["input"]
		op = config[sensor]["op"]

		sanitized_sensor = re.sub(r'\s','_',sensor)
		sanitized_input = re.sub(r'\s','_',input)

		if input == "null":
			continue;

		print("Generating execution code for sensor <%s>, interval = %d, bufsize = %d" % (sensor, s_interval, bufsizes[sensor]))
		if is_input_IO(input):
			program += operations.generateProgramIO(sanitized_sensor, op, input, 
						"buf_%s" % sanitized_sensor,
						"bufsize_%s" % sanitized_sensor,
						"buf_idx_%s" % sanitized_sensor,
						is_pingpong_buf[sensor])
		else:
			program += operations.generateProgramBuf(sanitized_sensor, op, 
						"buf_%s" % sanitized_input,
						"buf_%s" % sanitized_sensor,
						"bufsize_%s" % sanitized_input,
						bufsizes[input],
						"bufsize_%s" % sanitized_sensor,
						"buf_idx_%s" % sanitized_sensor,
						is_pingpong_buf[sensor])

	return program

def remove_comments(program):
	offset = 0
	ret = ""
	while True:
		nextS = program.find('/*', offset)
		nextE = program.find('*/', offset)

		if nextS < 0 and nextE < 0:
			break

		if nextE < nextS:
			sys.exit("Error parsing the comments of this program:\r\n" + program)

		next_nextS = program.find('/*', nextS+2)
		if next_nextS != -1 and next_nextS < nextE:
			sys.exit("Cannot parse comments in comments of this program:\r\n" + program)

		ret += program[offset: nextS]
		offset = nextE + 2

	ret += program[offset:]
	return ret

def calculate_cycles(program, startline = 0):

	program = remove_comments(program)
	cnt = 0
	lines = program.splitlines()
	lines = [line.strip() for line in lines] # remove spaces in the beginning and the end

	i = 0
	for line in lines:
		if i < startline:
			i += 1
			continue
		i += 1
		words = re.split('\s', line) # split into words
		instruction = words[0].lower()
		if instruction.endswith(":"):
			continue
		if instruction in instructions_1_cycle:
			cnt += 1
			continue
		if instruction in instructions_2_cycle:
			cnt += 2
			continue
		if instruction == "adc":
			cnt += 16
			continue
		if instruction == "jump":
			cnt += 1
			m = re.search('jump ([^,^\s]+)\s*,\s*(.+)', line)
			if m == None:
				m = re.search('jump ([^\s]*)', line)
				if m == None:
					sys.exit("Error parsing jump: " + line)
				else:
					# Jump with no condition
					label_name = m.group(1)
					# Get label position
					if not (label_name + ":") in lines:
						sys.exit("Cannot find label: " + label_name)
					label_pos = lines.index(label_name + ":")
					# Calculate the cycles from that label
					return cnt + calculate_cycles(program, label_pos)
			else:
				# Jump with condition
				label_name = m.group(1)
				# Get label position
				if not (label_name + ":") in lines:
					sys.exit("Cannot find label: " + label_name)
				label_pos = lines.index(label_name + ":")
				# Calculate the cycles from that label and from the next line,
				# the two cycles are required to be the same

				cycle_true = calculate_cycles(program, label_pos)
				cycle_false = calculate_cycles(program, i)

				if cycle_true != cycle_false:
					sys.exit("Error: The codes after branch %s at line #%d do not have the same cycle numbers!"
							 "Compensate the one with fewer cycles with nop." % (label_name, i))
				return cnt + cycle_true
	return cnt

################ Verifying configuration file ################

# Load JSON
configfile = sys.argv[1]
config = json.load(open(configfile))

# Verify JSON format
hasCPU = False
for sensor_name in config:
	if sensor_name == "//":
		continue
	if sensor_name == "CPU":
	 	hasCPU = True
	if "interval_in_us" not in config[sensor_name]:
		sys.exit("Attribute <%s> does not exist in sensor <%s>" % ("interval_in_us", sensor_name))
	if "input" not in config[sensor_name]:
		sys.exit("Attribute <%s> does not exist in sensor <%s>" % ("input", sensor_name))
	if "op" not in config[sensor_name]:
		sys.exit("Attribute <%s> does not exist in sensor <%s>" % ("op", sensor_name))

if not hasCPU:
	sys.exit("CPU configuration has not been specified")

# Verify inputs
inputs = []
for sensor_name in config:
	if sensor_name == "//" or sensor_name == "CPU":
		continue
	s_input = config[sensor_name]["input"]
	if s_input == "null":
		continue

	if s_input in inputs:
		sys.exit("Do not support one sensor being the input of multiple sensors")

	s_interval = config[sensor_name]["interval_in_us"]
	if s_input in config.keys():
		inputs.append(s_input)
		in_interval = config[s_input]["interval_in_us"]
		if s_interval % in_interval != 0 or s_interval == in_interval:
			sys.exit("Interval of sensor <%s> is not a multiple of sensor <%s>" % (sensor_name, s_input))

# Cluster and verify intervals
clusters = {}
for sensor_name in config:
	if sensor_name == "//":
		continue

	s_interval = config[sensor_name]["interval_in_us"]

	if sensor_name == "CPU":
		if s_interval < pingpong_min_interval_us:
			sys.exit("CPU interval is too short. CPU cannot read ULP buffer")
		continue

	if s_interval not in clusters:
		clusters[s_interval] = [];
	clusters[s_interval].append(sensor_name)

if len(clusters.keys()) > 4:
	sys.exit("Current ULP realtime framework does not "
			 "support more than 4 different frequencies")

################ Start generating assembly ################
n_clusters = len(clusters.keys())
interval_gcd = reduce(gcd, clusters.keys())
period = reduce(lcm, clusters.keys()) / interval_gcd
interval_cluster = interval_gcd / n_clusters 

print("Configuration verification has passed. "
	  "ULP realtime framework will run at (%d) interval." % interval_cluster)
print("Below are sensors in each clusters:")
pprint(clusters)

if not os.path.exists(r'output'):
    os.makedirs(r'output')
assembly_file = open('output/ulp_realtime.S', 'w')

# Write header
assembly_file.write(open('templates/headers.S').read())

# Write constants in the .set and .bss section
set_string = ""
bss_string = ""

set_string += ('.set n_clusters, %d\r\n' % n_clusters)
set_string += ('.set period, %d\r\n' % period)
bss_string += ('	.global pingpong\r\npingpong:\r\n	.long 0\r\n\r\n')

char_clusters = []
ord_char = ord('a')
for interval in sorted(clusters.keys()):
	char = unichr(ord_char)
	char_clusters.append(char)
	ord_char += 1
	set_string += (".set period_%s, %d\r\n" % (char, interval / interval_gcd))
	bss_string += ("	.global run_cnt_pp0_%s\r\n"
				   "run_cnt_pp0_%s:\r\n"
				   "	.long 0\r\n\r\n"
				   % (char, char))
	bss_string += ("	.global run_cnt_pp1_%s\r\n"
				   "run_cnt_pp1_%s:\r\n"
				   "	.long 0\r\n\r\n"
				   % (char, char))

bss_string += "	/* Cycles counting each cluster */\r\n"
for char in char_clusters:
	bss_string += ("cycle_%s:\r\n	.long 0\r\n\r\n" % char)

bufsizes = {}
is_pingpong_buf = {}
bss_string += "\r\n	/* Buffers */\r\n"
for sensor_name in config:
	if sensor_name == "//":
		continue
	s_input = config[sensor_name]["input"]
	if s_input == "null" or is_input_IO(s_input):
		continue
	s_interval = config[sensor_name]["interval_in_us"]
	in_interval = config[s_input]["interval_in_us"]

	# If specified, use user's buffer size, otherwise use default buffer size for input
	if "bufsize" in config[s_input]:
		bufsizes[s_input] = int(config[s_input]["bufsize"])
	else:
		bufsizes[s_input] = s_interval / in_interval

	sanitized_input = re.sub(r'\s','_',s_input)

	set_string += (".set bufsize_%s, %d\r\n" % (sanitized_input, bufsizes[s_input]))
	# if not CPU, use single buffer; otherwise use pingpong buffer
	if sensor_name != "CPU":
		bss_string += ("	.global buf_%s\r\nbuf_%s:\r\n	.skip bufsize_%s * 4, 0\r\n\r\n" % (sanitized_input, sanitized_input, sanitized_input))
		bss_string += ("buf_idx_%s:\r\n	.long 0\r\n\r\n" % (sanitized_input))
		is_pingpong_buf[s_input] = False
	else:
		bss_string += ("	.global buf_%s_pp0\r\nbuf_%s_pp0:\r\n	.skip bufsize_%s * 4, 0\r\n\r\n" % (sanitized_input, sanitized_input, sanitized_input))
		bss_string += ("	.global buf_%s_pp1\r\nbuf_%s_pp1:\r\n	.skip bufsize_%s * 4, 0\r\n\r\n" % (sanitized_input, sanitized_input, sanitized_input))
		bss_string += ("buf_idx_%s_pp0:\r\n	.long 0\r\n\r\n" % (sanitized_input))
		bss_string += ("buf_idx_%s_pp1:\r\n	.long 0\r\n\r\n" % (sanitized_input))
		is_pingpong_buf[s_input] = True

# Write variables in the .bss section
assembly_file.write(set_string + "\r\n")
assembly_file.write(open('templates/bss.S').read())
assembly_file.write(bss_string + "\r\n")

# Write .text section
last = 0;
text = open('templates/text.S').read()
cycles_cluster = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
for m in re.finditer('{{[^}]*}}', text):

	assembly_file.write(text[last:m.start()])
	g = ""
	i = 1
	for char in char_clusters:
		if g != "":
			g += '\r\n'
		substr = text[m.start()+2: m.end()-2]
		substr = re.sub('\[x\]', char, substr)
		substr = re.sub('\[d\]', str(i), substr)

		if re.search('\[code\]', substr) != None:
			program = generateProgram(config, clusters, char)
			print(program)
			cycles = calculate_cycles(program)
			if cycles > 0:
				print("--------------------------")
				print("The number of cycles is %d" % cycles)
				print("--------------------------")

			cycles_cluster[char] += cycles
			substr = re.sub('\[code\]', program, substr)

		g += substr
		i += 1

	assembly_file.write(g)
	last = m.end()

assembly_file.write(text[last:])

# Finish writing assembly
assembly_file.close()

################ Start generating C ################
main = open('templates/main.c').read()
main_output = ""
last = 0;
for m in re.finditer('{{[^}]*}}', main):
	main_output += main[last:m.start()]
	g = ""
	i = 1
	for char in char_clusters:
		if g != "":
			g += '\r\n'
		substr = main[m.start()+2: m.end()-2]
		substr = re.sub('\[x\]', char, substr)

		g += substr
		i += 1

	main_output += g
	last = m.end()

main_output += main[last:]
main = main_output

print("\r\nCycles of each cluster's execution code are:")
pprint(cycles_cluster)
sleep_period_0 = interval_cluster - ULP_no_work_runtime
sleep_period_1 = int(round(interval_cluster - ULP_no_work_runtime - cycles_cluster['a'] * time_ALU))
sleep_period_2 = int(round(interval_cluster - ULP_no_work_runtime - cycles_cluster['b'] * time_ALU))
sleep_period_3 = int(round(interval_cluster - ULP_no_work_runtime - cycles_cluster['c'] * time_ALU))
sleep_period_4 = int(round(interval_cluster - ULP_no_work_runtime - cycles_cluster['d'] * time_ALU))

main = re.sub('\[sleep_period_0\]', str(sleep_period_0), main)
main = re.sub('\[sleep_period_1\]', str(sleep_period_1), main)
main = re.sub('\[sleep_period_2\]', str(sleep_period_2), main)
main = re.sub('\[sleep_period_3\]', str(sleep_period_3), main)
main = re.sub('\[sleep_period_4\]', str(sleep_period_4), main)
main = re.sub('\[CPU_interval\]', str(config["CPU"]["interval_in_us"]), main)

c_file = open('output/main.c', 'w')
c_file.write(main)
c_file.close()

print("---------------------------------------------------------------")
print("Program generated.")
print("The generated files are output/main.c and output/ulp_realtime.S")
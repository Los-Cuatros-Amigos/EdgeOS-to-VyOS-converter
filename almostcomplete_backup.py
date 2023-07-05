#!/bin/python3

import sys
import re
import copy

def print_status():
	interfaces_layout = [f"{interface} -> {action}" for interface, action in zip(interfaces, interfaces_action)]
	print("Interface Status:")
	print("\n".join(interfaces_layout) + "\n" * 2)

def take_input(user_input, interfaces, action):
	prompt_string = f"{interfaces[action]} -> "
	for line in range(len(interfaces) + 4):
		sys.stdout.write("\033[F")  # Move cursor up one line
		sys.stdout.write("\033[K")  # Clear line
		sys.stdout.flush()
	print_status()	
	if not valid:
		sys.stdout.write("\033[F")  # Move cursor up one line
		print("[INVALID INPUT]")
	user_input = input(prompt_string)	
	return user_input

# Checking that user passed in config file
if (len(sys.argv) < 2):
	print('You must pass in an input config file...')
	quit()
elif (len(sys.argv) > 2):
	print('Too many parameters passed...')
	quit();
contents = open(sys.argv[1]).read() # Copying contents of config into local string

# Regex string to search for and delete
deletions = [
	r'^([\s\S]*?)(?=firewall \{\n[\s]*?all-ping enable)',
	r'^.*modify[\s\S]*?(?=\n\s*name\s+INSIDE-LOCAL {)',
	r'^.*in {\n\s*?modify ROUTE-L-INTERNAL[\s\S]*?\n[\s\S]*?}'
]

# Format: [regex to situate inserted text, text to insert]
insertions = [
	[r'^.*policy {', '''policy {
	route ROUTE-L-INTERNAL {
		rule 1000 {
			description "vlan10 routing"
			set {
				table 10
			}
			source {
				group {
					network-group ''' + re.search(r'(?<=network-group )NET-L-.*?(?= {)', contents, re.MULTILINE)[0] + '''
				}
			}	
		}
	}'''],
	[r'^.*?ip {\s*ospf {', '''			policy {
				route ROUTE-L-INTERNAL
			}
			ip {
				ospf {''']
]

valid = True

# Iterating through all expressions in deletions array
for expression in deletions:
	# Replacing all occurences of regex expressions with blank space
	contents = re.sub(expression, '', contents, 0, re.MULTILINE)

# Iterates through all expressions in insertions array and inserts text accordingly
for expression in insertions:
	# Replacing all occurences of regex expressions with new text
	contents = re.sub(expression[0], expression[1], contents, 0, re.MULTILINE)

interfaces = re.findall(r'(?<=\s{4}ethernet )[\S]*', contents, re.MULTILINE)
interfaces_action = interfaces.copy()

user_input = "null"
while (user_input != "f"):
	for action in range(len(interfaces_action)):
		while (user_input != "f"):
			user_input = take_input(user_input, interfaces, action)
			match user_input:
				case "": # Keep the same
					break
				case "f": # Finish
					break
				case "d": # Delete
					interfaces_action[action] = "delete"
					break
				case _:
					if (re.search(r'^eth[0-9]*', user_input) == None):
						valid = False
						sys.stdout.write("\033[F")  # Move cursor up one line
						sys.stdout.write("\033[F")  # Move cursor up one line
						print("[INVALID INPUT]\n")
						continue
					interfaces_action[action] = user_input
					interfaces_action[int(user_input[3:])] = f"replaced by {interfaces[action]}"
					valid = True
					break

# Deleting whole interfaces and replacing eth interface numbers with new values
for action in range(len(interfaces_action)):
	if (interfaces_action[action] == "delete"):
		contents = re.sub(r'\s{4}ethernet ' + interfaces[action] + '[\s\S]*?\s{4}}', '', contents, re.MULTILINE)
		continue
	contents = re.sub(r'(?<=\s{4}ethernet )' + interfaces[action], interfaces_action[action], contents, re.MULTILINE)

contents = re.sub(r'\n\s*\n', '\n', contents) # Clearing out all empty lines

# Writing modified string to file
with open('config.boot', 'w+') as file:
	file.write(contents)

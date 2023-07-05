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
	quit()
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

swapping = "swapping with "
replaced = "replaced by "
replacing = "replacing "

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
	for current_eth in range(len(interfaces_action)):
		while (user_input != "f"):
			user_input = take_input(user_input, interfaces, current_eth)
			match user_input:
				case "": # Keep the same
					break
				case "f": # Finish
					break
				case "d": # Delete
					interfaces_action[current_eth] = "delete"
					break
				case _:
					# Performing regex on input for sanitization and valid eth capture)
					evaluation = re.search(r'^eth(0|[1-9][0-9]*)$', user_input) 
					# If no valid eth is captured or the integer of the eth is out of bounds of existing eths
					if (evaluation == None or int(evaluation[0][3:]) >= len(interfaces)): 
						valid = False # Adds error message to TUI 
						# Move cursor up a couple lines to insert error message after screen has been cleared and refreshed
						sys.stdout.write("\033[F" * 2)  
						print("[INVALID INPUT]\n")

						continue # Skipping to prompt for new user input
					else:
						# If the interface action of the eth passed in user input is to replace the active interface:
						if (interfaces_action[int(user_input[3:])] == f"{replacing}{interfaces[current_eth]}"):
							# Set interface action of user input eth to swap state with current eth 
							interfaces_action[current_eth] = f"{swapping}{interfaces[int(user_input[3:])]}"
							# Setting interface action of current eth to swap state of user input eth, creating the swap pair 
							interfaces_action[int(user_input[3:])] = f"{swapping}{interfaces[current_eth]}" 
						# If the interface action of the eth passed in user input is not to replace the active interface
						else:
							# If the interface action of the eth passed in user input is set to swap with another eth 
							if (interfaces_action[int(user_input[3:])][:len(swapping)] == swapping): 
								# If the interface action of the current eth is set to swap
								if (interfaces_action[current_eth][:len(swapping)] == swapping):
									# If eth passed in user input is already in a swap pair with active interface
									if (interfaces_action[current_eth][len(swapping):] == user_input):
										break
									else:
										# Setting the interface action of the non-referenced swap partner in the swap break to itself
										interfaces_action[int(interfaces_action[int(user_input[3:])][len(swapping) + 3:])] = interfaces_action[int(user_input[3:])][len(swapping):]

										# Set the interface action of the eth listed as the swap partner based on the interface action of the current eth to the swap partner listed in the interface action of the current eth, completing pair 
										interfaces_action[int(interfaces_action[current_eth][len(swapping) + 3:])] = interfaces_action[current_eth][len(swapping):]
										interfaces_action[current_eth] = f"{replacing}{interfaces[int(user_input[3:])]}"
										for action in range(len(interfaces_action)):
											if (interfaces_action[action] == f"{replaced}{interfaces[current_eth]}"):
												interfaces_action[action] = interfaces[action]
										interfaces_action[int(user_input[3:])] = f"{replaced}{interfaces[current_eth]}"
										continue
								else:
									interfaces_action[int(interfaces_action[int(user_input[3:])][len(swapping) + 3:])] = interfaces_action[int(user_input[3:])][len(swapping):]
									interfaces_action[int(user_input[3:])] = f"{replaced}{interfaces[current_eth]}"	
									interfaces_action[current_eth] = f"{replacing}{user_input}"
									break
							else:
								if (interfaces_action[current_eth][:len(replaced)] == replaced):
									interfaces_action[int(interfaces_action[current_eth][len(replaced) + 3:])] = interfaces[int(interfaces_action[int(current_eth)][len(replaced) + 3:])]

								if (interfaces_action[int(user_input[3:])][:len(replaced)] == replaced):
									interfaces_action[int(interfaces_action[int(user_input[3:])][len(replaced) + 3:])] = interfaces_action[int(user_input[3:])][len(replaced):]
								elif (interfaces_action[int(user_input[3:])][:len(replacing)] == replacing):
									interfaces_action[int(interfaces_action[int(user_input[3:])][len(replacing) + 3:])] = interfaces_action[int(user_input[3])][len(replacing):]	
								for action in range(len(interfaces_action)):
									if (interfaces_action[action] == f"{replaced}{interfaces[current_eth]}"):
										interfaces_action[action] = interfaces[action]
								interfaces_action[int(user_input[3:])] = f"{replaced}{interfaces[current_eth]}"			

								interfaces_action[current_eth] = f"{replacing}{user_input}"
								if (interfaces[current_eth] == user_input):
									interfaces_action[current_eth] = user_input
									break
					valid = True
					break

# Deleting whole interfaces and replacing eth interface numbers with new values
for action in range(len(interfaces_action)):
	print("iterating")
	interface_item = interfaces[current_eth]
	match interfaces_action[current_eth]:
		case "delete":	
			contents = re.sub(r'\s{4}ethernet ' + interfaces[current_eth] + '[\s\S]*?\s{4}}', '', contents, re.MULTILINE)
		case str(interface_item):
			print(f"same {interface_item}")
			print(interfaces_action[current_eth] == interface_item)
			continue
		case _:
			print("subbing")
			contents = re.sub(r'(?<=\s{4}ethernet )' + interfaces[current_eth], interfaces_action[current_eth[12:]], contents, re.MULTILINE)

contents = re.sub(r'\n\s*\n', '\n', contents) # Clearing out all empty lines

# Writing modified string to file
with open('config.boot', 'w+') as file:
	file.write(contents)

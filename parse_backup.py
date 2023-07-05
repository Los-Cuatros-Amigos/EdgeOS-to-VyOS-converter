#!/bin/python3

import sys
import re

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

# Iterating through all expressions in deletions array
for expression in deletions:
	# Replacing all occurences of regex expressions with blank space
	contents = re.sub(expression, '', contents, 0, re.MULTILINE)

# Iterates through all expressions in insertions array and inserts text accordingly
for expression in insertions:
	# Replacing all occurences of regex expressions with new text
	contents = re.sub(expression[0], expression[1], contents, 0, re.MULTILINE)

contents = re.sub(r'\n\s*\n', '\n', contents) # Clearing out all empty lines

# Writing modified string to file
with open(f'{sys.argv[1]}_vyos', 'w+') as file:
	file.write(contents)

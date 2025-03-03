import os
## this is to test multiprocessing and file creation
# has to be importable as required by multiprocess
def paralleltest(string):
	"""
	Function to test async write to file and filename.
	"""

	with open(string+'.txt', 'w') as file:
		file.write(string + '\n')

	# with open('testtext.txt', 'w') as file:
	# 	file.write(string + '\n')
		
	# os.system('mv testtext.txt '+string+'_test.txt')

import os
## this is to test multiprocessing and file creation
# has to be importable as required by multiprocess
def paralleltest(string):
	"""
	Function to test async write to file and filename.
	"""
	os.system('echo "'+string+'"" > testtext.txt')
	os.system('mv testtext.txt '+string+'_test.txt')

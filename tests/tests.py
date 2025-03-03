import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u
from paralleltest import paralleltest #local file and function
from spike.tools import objloc

@pytest.mark.parametrize(
	"obj, expected",
	[
		(objloc('M51'), 
		SkyCoord('202.469575 47.19525833', unit = (u.deg, u.deg), frame = 'icrs')),

		(objloc('10:00:30.03 +02:08:59.47'), 
		SkyCoord('10:00:30.03 +02:08:59.47', unit = (u.hour, u.deg), frame = 'icrs')),

		(objloc('150.125125 2.1498528'),
		SkyCoord('150.125125 2.1498528', unit = (u.deg, u.deg), frame = 'icrs'))
		
	])

def test_objloc(obj, expected):
	from spike.tools import objloc
	assert obj == expected


def test_multiprocessing():
	# simple check on async file creation
	# if this doesn't pass on the assert, user should not use the parallel option
	import os
	from multiprocessing import Pool, cpu_count
	pool = Pool(processes = (cpu_count() - 1))
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		pool.apply_async(paralleltest, args = (i))
	pool.close()
	pool.join()
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		with open(i+'.txt') as file:
			checkstring = file.read()
		assert i+'\n' == checkstring
		os.system('rm '+i+'_test.txt')




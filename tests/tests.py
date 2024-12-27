import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u
from paralleltest import paralleltest #local file and function

@pytest.mark.parametrize(
	"obj, expected",
	[
		('M51', 
		SkyCoord('202.469575 47.1952583', unit = (u.deg, u.deg), frame = 'icrs')),

		(objloc('10:00:30.03 +02:08:59.47'), 
		SkyCoord('10:00:30.03 +02:08:59.47', unit = (u.hour, u.deg), frame = 'icrs')),

		(objloc('150.125125 2.1498528'),
		SkyCoord('150.125125 2.1498528', unit = (u.deg, u.deg), frame = 'icrs'))
		
	])

def test_objloc(obj, expected):
	from spike.tools import objloc
	assert objloc(obj) == expected


def test_multiprocessing():
	## confirm that multiprocessing is working as expected for simultaneous file generation
	import os
	from multiprocessing import Pool, cpu_count
	pool = Pool(processes = (cpu_count() - 1))
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		pool.apply_async(os.system, args = ('touch '+i+'_test.txt'))
	pool.close()
	pool.join()
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		assert os.path.exists(i+'_test.txt')
		os.system('rm '+i+'_test.txt')


def test_multiprocessing():
	# more extensive/robust check on async file creation



def test_psfgen():
	## have to assert that aliases actually exist (for TinyTim, SExtractor, etc.)

	## test TinyTim,

	## test PSFEx, 

	# the generated models will be in test_data
	# will keep minimal data, too, for empirical PSF tests
	# this will be annoying to set up -- will finish everything else first
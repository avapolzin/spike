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
	# if this doesn't pass on the assert, user should not use the parallel option
	import os
	from multiprocessing import Pool, cpu_count
	pool = Pool(processes = (cpu_count() - 1))
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		pool.apply_async(paralleltest, args = (i))
	pool.close()
	pool.join()
	for i in ['a', 'b', 'c', 'd', 'e', 'f']:
		with open(i+'_test.txt') as file:
		    checkstring = file.read()
		assert i == checkstring
		os.system('rm '+i+'_test.txt')



def test_psfgen():
	"""
	Test image processing and PSF generation steps of spike.

	Attempts to confirm the existence of optional executables before running.
	"""
	import shutil
	import spike
	## have to search for executables and aliases
	## can use which I guess? 
	## sex, psfex -- executables
	## tiny1,2,3 (or just TINYTIM) -- alias; WEBBPSF_PATH -- alias

	# https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
	# https://stackoverflow.com/questions/51785022/check-if-sourced-bash-profile-command-exists

	# https://stackoverflow.com/questions/41230547/check-if-program-is-installed-in-c

	coords = spike.tools.objloc() # will need to work out my choice
	img = './test_data/imexample.fits'
	imcam = 'ACS/WFC'
	pos = spike.tools.checkpixloc(coords, img, imcam)

	## test TinyTim
	try:
	    TINY_PATH = os.environ['TINYTIM']
	except:
	    TINY_PATH = None

	if TINY_PATH:
		ttex = fits.open('./test_data/ttout.fits')
		outtiny = spike.psfgen.tinypsf(coords, img, imcam, pos)
		assert outtiny == ttex[0].data

	## test PSFEx
	SE_PATH = shutil.which('sex')
	PSFEX_PATH = shutil.which('psfex')
	if SE_PATH and PSFEX_PATH:
		psfexex = np.load('./test_data/psfexout.npy')
		outpsfex = spike.psfgen.sepsf(coords, img, imcam, pos)
		assert outpsfex == psfexex

	## test WebbPSF
	try:
	    WEBBPSF_PATH = os.environ['WEBBPSF_PATH']
	except:
	    WEBBPSF_PATH = None

	if WEBBPSF_PATH:
		wex = fits.open('./test_data/wout.fits')
		outw = spike.psfgen.jwpsf(coords, img, imcam, pos)
		assert outw == wex[3].data

		





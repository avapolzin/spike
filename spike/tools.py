from astropy.coordinates import SkyCoord, name_resolve
import astropy
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS, utils
import numpy as np


def objloc(obj):
	"""
	Get object location.

	Parameters:
		obj (str): Name or coordinates for object of interest. If coordinates, should be in
			HH:MM:SS DD:MM:SS or degree formats. Names must be resolvable in SIMBAD.
	Returns:
		coords (astropy coordinates object)
	"""
	isname = False #check if obj is name or coordinates
	for s in obj:
		if s.isalpha():
			isname = True
			break

	if isname:
		coords = name_resolve.get_icrs_coordinates(obj)

	if not isname:
		if ':' in obj:
			coords = SkyCoord(obj, unit = (u.hour, u.deg), frame = 'icrs')
		if not ':' in obj:
			coords = SkyCoord(obj, unit = u.deg, frame = 'icrs')

	return coords


def checkpixloc(coords, img, inst, camera = None):
	"""
	Get object location on detector. 

	Parameters:
		coords (astropy skycoord object): Coordinates of object of interest or list of skycoord objects.
		img (str): Path to image.
		inst (str): Instrument of interest. 
				HST: 'ACS', 'WFC3', 'WFPC1', WFPC2', 'FOC', 'NICMOS', 'STIS'
				JWST: 'MIRI', 'NIRCAM', 'NIRISS'
				Roman: 'WFI', 'CGI'
		camera (str): Camera associated with instrument.
				HST/ACS: 'WFC', 'HRC'
				HST/WFC3: 'UVIS', 'IR'
				JWST/NIRISS: 'Imaging', 'AMI' #AMI has different multi-extension mode

	Returns:
		[X, Y, chip] (list): Pixel coordinates and, if relevant, chip number (HST) or detector name (Roman).
				Only returned if object coordinates fall onto detector - returns NaNs if not.

	"""
	hdu = fits.open(img)
	if camera:
		imcam = inst.upper() + '/' + camera.upper()
	if not camera:
		imcam = inst.upper()

	### instrument checks ###
	if imcam in ['ACS/WFC', 'WFC3/UVIS']:
		chip1 = hdu[4]
		chip2 = hdu[1]
		chips = [chip1, chip2]

		chip = np.nan
		for a in chips:
			wcs1 = WCS(a.header, fobj = hdu)
			datshape = a.data.shape
			if type(coords) != astropy.coordinates.sky_coordinate.SkyCoord:
				xcoord_out = []
				ycoord_out = []
				chip_out = []
				for coord in coords:
					check = utils.skycoord_to_pixel(coord, wcs1)
					if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
						xcoord_out.append(check[0])
						ycoord_out.append(check[1])
						if a == chip1:
							chip_out.append('1')
						if a == chip2:
							chip_out.append('2')
				if len(xcoord_out) >= 1:
					out = [[xcoord_out[i], ycoord_out[i], chip_out[i]] for i in range(len(coords))]
				if len(xcoord_out) == 0:
					out = [np.nan] * 3
			if type(coords) == astropy.coordinates.sky_coordinate.SkyCoord:
				check = utils.skycoord_to_pixel(coords, wcs1)
				if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
					x_coord = check[0]
					y_coord = check[1]
					if a == chip1:
						chip = '1'
					if a == chip2:
						chip = '2'
		if np.isnan(chip):
			out = [np.nan, np.nan, chip]
		else:
			out = [x_coord, y_coord, chip]

	if imcam in ['ACS/HRC', 'WFC3/IR', 'MIRI', 'NIRCAM', 'NIRISS/IMAGING']:
		# for WFC3, only checks the final readout by design
		chip = 0 #no chip
		wcs1 = WCS(hdu[1].header, fobj = hdu)
		datshape = hdu[1].data.shape
		check = utils.skycoord_to_pixel(coord, wcs)
		if np.logical_and(0 <= check[0] <= datshape[0], 0 <= check[1] <= datshape[1]):
			x_coord = check[0]
			y_coord = check[1]
			out = [x_coord, y_coord, chip]
		else:
			out = [np.nan] * 3

	# if imcam in ['WFI', 'CGI']: #need to get detector name rather than chip number
	# 	#will have to look at simulated imaging to see how to do this
	# 	#UGH



	return out

def to_asdf(save = True):
	"""
	Convert .fits file to .asdf, by simply wrapping data and header extensions.


	"""



def pysextractor():
	"""
	Wrapper to easily call SExtractor from python. 
	Using this in lieu of sep for easier compatibility with PSFEx.

	Parameters:

	"""

def rewrite_header(obj, header):
	"""
	Write HST and JWST image headers to the model PSFs and modify the coordinates and WCS.


	"""

def write_header(obj, header_params):
	"""
	Write Roman image headers to model PSFs and modify coordinates and WCS.
	Takes in dictionary of relevant header keys given size of files.

	
	"""



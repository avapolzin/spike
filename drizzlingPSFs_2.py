from astropy import coordinates
import astropy.units as u
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy import wcs
from astropy.wcs.utils import skycoord_to_pixel
from ccdproc import ImageFileCollection
from drizzlepac import tweakreg
from drizzlepac import tweakback
from drizzlepac import astrodrizzle
import numpy as np
import glob
import os
import subprocess
from subprocess import call
import numpy as np

# #########
#  * * * * 
# #########

camera = 15
chip = 1
pix_coord = '2021 2021'
filt = 'F814W'
obj_type = 1
spec_choice = 11
PSF_diam = 3.0
exit = ':q'
command_list = [camera, chip, pix_coord, filt, obj_type, spec_choice, PSF_diam, exit]
command_list = [str(i) for i in command_list if i] 
obj_coord = "10h00m30.03s +02d08m59.47s"
coord = coordinates.SkyCoord(obj_coord, frame = "fk5")
tiny1 = subprocess.Popen('~/tinytim-7.5/tiny1 tinytest.param', shell=True, stdin=subprocess.PIPE, 
                      stdout=subprocess.PIPE)
newline = os.linesep
tiny1.communicate(newline.join(command_list).encode())





def generate_file_lists(filts, file_types):
	#might want to make arbitrary *filts, *file_types
	"""
	Generates lists of the CALACS/drizzled data products.

	INPUT:
		filts (str, arr_like): list of filters in use, e.g. ["F814W", "F606W", "F475W"] or ["F660N"]
		file_types (str, arr_like): list of data product types in working directory, e.g. ["flt", "drz"] or ["flc", "drc"]

	RETURNS:
		file_dict (dict): dictionary containing all necessary files, sorted by file type and filter

	"""

	for i in file_types:
		for k in filts:
			file_dict[k + "_" + i] = []

	for j in all_files:
		for i in file_types:
			for k in filts:
				if np.logical_or(fits.getheader(j)['FILTER1'] == k, fits.getheader(j)['FILTER2'] == k):
					if i in j:
						file_dict[k + "_" + i].append(j)

	file_dict["drizzled_list"] = []
	for j in all_files:
		if np.logical_or("drc" in j, "drz" in j):
			file_dict["drizzled_list"].append(j)
		else:
			continue
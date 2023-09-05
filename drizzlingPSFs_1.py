#Drizzling ACS PSFs
# will make it for my PSFs first and then generalize -- maybe worth creating a more formal wrapper
# essentially a wrapper for drizzlepac and TinyTim
from astropy import coordinates
import astropy.units as u
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
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
# import argparse #add plotting/tweak flag later ??


# #########
#  * * * * 
# #########


path = "./COSMOS_blob_project/PSF_drizzling/"
"""
Path to your files from your current directory.
"""
obj_coord = "10h00m30.03s +02d08m59.47s"

coord = coordinates.SkyCoord(obj_coord, frame = "fk5")
"""
RA, Dec of interest (str) -- readable by SkyCoord.
"""

all_files = glob.glob(path + "*.fits")
file_dict = {}
to_drizzle = {}

# shift = tweak_shift - int(tweak_shift)

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
						file_dict[k + "_" + i].append(j.replace(path, ""))

	file_dict["drizzled_list"] = []
	for j in all_files:
		if np.logical_or("drc" in j, "drz" in j):
			file_dict["drizzled_list"].append(j.replace(path, ""))
		else:
			continue




def tweak(files = all_files, file_lists = file_dict):
#def tweak(files, file_lists, filts, file_types): #only need these if toggling astrodrizzle
	"""
	Align drizzled files and calculate/write to header offsets for CALACS products.
	(Optional -- can be done prior to working with PSFs, toggle with -t flag.) #WILL ADD FLAG LATER!!!!

	INPUT:
		files (arr_like): all FITS files in working directory (all_files)
		file_lists (arr_like):  all relevant file lists sorted by file type and filter (file_dict)
		filts (str, arr_like): list of filters in use, e.g. ["F814W", "F606W", "F475W"] or ["F660N"]
		file_types (str, arr_like): list of data product types in working directory, e.g. ["flt", "drz"] or ["flc", "drc"]
		delim (str): delimiter for prodmatch (see next item)

		Also requires: 
		prodmatch (file): named for drizzled file (sans '.fits'), contains names (sans '.fits') of constituent CALACS products
			-- for instance j8pu41010_drc.txt would contain 'j8pu41dmq_flc
															 j8pu41dqq_flc
															 j8pu41dvq_flc
															 j8pu41e7q_flc' written line by line

	RETURNS:
		"tweaked" files with offsets for drizzling
	"""

	tweakreg.TweakReg(file_dict["drizzled_list"], threshold=6.0, searchrad=3.0, dqbits=-16,
        configobj = None, interactive=False, shiftfile=True, expand_refcat=True,
        outshifts='shift_searchrad.txt', updatehdr=True)
	#may need to play with these values to generalize them a bit


	#might want to just do tweakback on the PSFs and then autodrizzle the PSFs.... that seems like the right
	# course of action ...

	for i in file_dict["drizzled_list"]:
		drizzled_file = i.replace(".fits", ".txt")
		prodmatch = pd.read_csv(path + "drizzled_file", header = None)
		prodmatch_list = prodmatch.readlines()
		tweakback.tweakback(i,input=prodmatch_list)

	# might add toggle to use astrodrizzle on image from here? Seems unnecessary




############# Define variables for generate_PSFs() ################
PSF_diam = '3.0' #arcseconds, ACS suggestion from Tiny Tim -- won't make this value an option
exit = ':q'
###################################################################

def generate_PSFs(filts, files = glob.glob(path + "*.fits"), file_lists = file_dict, camera = '15', obj_type = '1', spec_choice = '11', 
	coord = coord, tinypath = '~/tinytim-7.5/', temp = None, photon_index = None, spectral_index = None, spec_file = None):
	"""
	Use TinyTim to generate PSFs to be drizzled.

	INPUTS:
		filts (str, arr_like): list of filters in use, e.g. ["F814W", "F606W", "F475W"] or ["F660N"]
		files (arr_like): all FITS files in working directory (all_files)
		file_lists (arr_like):  all relevant file lists sorted by file type and filter (file_dict)
		camera (str): 15 is ACS Wide-Field Camera, 16 is ACS High Resolution Channel; for others refer to 
			TinyTim documentation (this module is only equipped -- sans-modification -- for ACS WFC3 and HRC)
		obj_type (str): default = 1 (choose spectrum from list), see TinyTim documentation (or below) for others
		spec_choice (str or None): default = 11 (Type G2V) -- must result in undersampled PSF, 
			see TinyTim documentation for other options, 
		coord: astropy.SkyCoord value for RA, Dec of interest
		tinypath (str): path to directory with 'tiny' executables; default = '~/tinytim-7.5/'

		temp (str, optional): only if obj_type = '2' (blackbody), in Kelvin -- i.e., '5800'
		photon_index (str, optional): only if obj_type = '3' (power law -- f(nu) = nu^i), e.g. '1'
		spectral_index (str, optional): only if obj_type = '4' (power law -- f(lambda) = lambda^i), e.g. '1'
		spec_file (str, optional): only if obj_type = '5' (user-provided spectrum, ASCII table), file name (and path, 
			if necessary) for this spectrum 
			{WARNING: have not checked that this doesn't further modify what needs to be fed to the command line}


	RETURN:
		TinyTim PSFs for all data products and final drizzled PSF for each filter ('filter_psf_USE.fits'). Each of the CALACS products has two
			PSFs generated -> 'filename_psf.fits' (modeled PSF) and 'filename_psf_distort.fits' (modeled PSF with ACS geometric correction)
		
	"""
	if obj_type == '1':
		obj_q2 = spec_choice
	if obj_type == '2':
		obj_q2 = temp
	if obj_type == '3':
		obj_q2 = photon_index
	if obj_type == '4':
		obj_q2 = spectral_index
	if obj_type == '5':
		obj_q2 = spec_file

	possible_CALACS = ["flc", "flt", "crj", "crc"]

	for filt in filts:

		for key in file_dict.keys():
			for x in possible_CALACS:
				if x in key:
					file_list = file_dict[filt + '_' + x]


		PSF_outputs = []

		for i in file_list:
			filename = i.replace(".fits", "")

			hdu = fits.open(path + i)
			global_header = hdu[0].header

			if camera == '15':
				chip1 = hdu[4]
				chip2 = hdu[1]
				chips = [chip1, chip2]

				for a in chips:
					wcs = WCS(a.header, fobj = hdu)
					check = skycoord_to_pixel(coord, wcs)
					if np.logical_and(0 <= check[0] <= 4095, 0 <= check[1] <= 2047):
						x_coord = check[0]
						y_coord = check[1]
						if a == chip1:
							chip = '1'
						if a == chip2:
							chip = '2'
					else:
						continue

			if camera == '16':
				wcs = WCS(hdu[1].header, fobj = hdu)
				check = skycoord_to_pixel(coord, wcs)
				if np.logical_and(0 <= check[0] <= 1023, 0 <= check[1] <= 1023):
					x_coord = check[0]
					y_coord = check[1]
				else:
					continue

			pix_coord = str(x_coord) + ' ' + str(y_coord)


			command_list = [camera, chip, pix_coord, filt, obj_type, obj_q2, PSF_diam, exit]
			command_list = [str(i) for i in command_list if i] 

			tiny1 = subprocess.Popen(tinypath+'tiny1 tinytest.param', shell=True, stdin=subprocess.PIPE, 
	                      stdout=subprocess.PIPE)
			newline = os.linesep
			tiny1.communicate(newline.join(command_list).encode())

			tiny2 = os.system(tinypath+'tiny2 tinytest.param')
			tiny3 = os.system(tinypath+'tiny3 tinytest.param')
			os.rename(':q00_psf.fits', filename+'_psf.fits') # (tiny2 result)
			os.rename(':q00.fits', filename+'_psf_distort.fits') # usable file, geometrically distorted (tiny3 result)

			PSF_outputs.append(filename + '_psf_distort.fits')






















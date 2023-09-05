from astropy import coordinates
import astropy.units as u
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy import wcs
# from astropy.wcs import WCS
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
from pyraf import iraf
from scipy import ndimage
# import argparse #add plotting/tweak flag later






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

# tiny1 = os.system('tiny1 tinytest.param')
tiny1 = subprocess.Popen('~/tinytim-7.5/tiny1 tinytest.param', shell=True, stdin=subprocess.PIPE, 
                      stdout=subprocess.PIPE)
newline = os.linesep

tiny1.communicate(newline.join(command_list).encode())

# tiny2 = subprocess.Popen('~/tinytim-7.5/tiny2 tinytest.param', shell=True, stdin=subprocess.PIPE, 
#                       stdout=subprocess.PIPE)




# tiny3 = subprocess.Popen('~/tinytim-7.5/tiny3 tinytest.param', shell=True, stdin=subprocess.PIPE, 
#                       stdout=subprocess.PIPE)

tiny2 = os.system('~/tinytim-7.5/tiny2 tinytest.param')
tiny3 = os.system('~/tinytim-7.5/tiny3 tinytest.param')
os.rename(':q00_psf.fits', 'test_psf.fits')
os.rename(':q00.fits', 'test_psf_distort.fits')

path = './COSMOS_blob_project/PSF_drizzling/'
all_files = glob.glob(path + "*.fits")

file_dict = {}
to_drizzle = {}
to_add = {'file': [], 'psf_file': [], 'chip': [], 'filt': []}

def tweak(files = all_files, file_lists = file_dict):
#def tweak(files, file_lists, filts, file_types): #only need these if toggling astrodrizzle
	"""
	Align drizzled files and calculate/write to header offsets for CALACS products.
	(Optional -- can be done prior to working with PSFs, toggle with -t flag.) #WILL ADD FLAG LATER!!!!

	*** Tweakreg and tweakback are desctructive of the original file and can't be run twice, don't work in the directory
		where you're keeping original files ***

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
		prodmatch = open(drizzled_file)
		prodmatch_list = prodmatch.readlines()
		prodmatch_list = [path + k.replace('\n', '') + '.fits' for k in prodmatch_list]
		# ^to tweakback the flc files and then feed that header to the PSFs
		#prodmatch_list = [k.replace('\n', '') + "_psf_distort.fits" for k in prodmatch_list]
		# okay, back to original idea... 
		print(prodmatch_list)
		tweakback.tweakback(i, input=prodmatch_list)


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


def generate_PSFs(filts, files = all_files, file_lists = file_dict, camera = '15', obj_type = '1', spec_choice = '11', coord = coord, 
	tinypath = '~/tinytim-7.5/', temp = None, photon_index = None, spectral_index = None, spec_file = None):
	"""
	Use TinyTim to generate PSFs to be drizzled.

	INPUTS:
		filts (str, arr_like): list of filters in use, e.g. ["F814W", "F606W", "F475W"] or ["F660N"]
		files (arr_like): all FITS files in working directory (all_files)
		file_lists (arr_like):  all relevant file lists sorted by file type and filter (file_dict)
		camera (str): 15 is ACS Wide-Field Camera, 16 is ACS High Resolution Channel; for others refer to 
			TinyTim documentation (this module is only equipped -- sans-modification -- for ACS WFC and HRC)
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

		to_drizzle[filt] = []

		for key in file_dict.keys():
			for x in possible_CALACS:
				if x in key:
					file_list = file_dict[filt + '_' + x]
			# if any(ext in key for ext in possible_CALACS):
			# 	file_list = file_dict[filt + '_' + ext]



		# PSF_outputs = []

		for i in file_list:
			to_add["file"].append(i)
			to_add["filt"].append(filt)

			filename = i.replace(".fits", "")
			filename = filename.replace(path, "")
			to_add["psf_file"].append(filename+'_psf_distort.fits')

			hdu = fits.open(i, mode = 'update')
			global_header = hdu[0].header

			if camera == '15':
				chip1 = hdu[4]
				chip2 = hdu[1]
				chips = [chip1, chip2]
				wcsdvarr_1 = hdu[11]
				wcsdvarr_2 = hdu[12]
				wcsdvarr_3 = hdu[13]
				wcsdvarr_4 = hdu[14]
				wcscorr = hdu[15]

				for a in chips:
					wcs1 = wcs.WCS(a.header, fobj = hdu)
					check = skycoord_to_pixel(coord, wcs1)
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
				chip = None
				wcs1 = WCS(hdu[1].header, fobj = hdu)
				check = skycoord_to_pixel(coord, wcs)
				if np.logical_and(0 <= check[0] <= 1023, 0 <= check[1] <= 1023):
					x_coord = check[0]
					y_coord = check[1]
				else:
					continue

			pix_coord = str(x_coord) + ' ' + str(y_coord)
			print(chip, pix_coord)
			to_add["chip"].append(chip)


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
			to_drizzle[filt].append(filename+'_psf_distort.fits')

			# #last ditch to tweakback the PSFs themselves  -- this seems to be the proper way to do it, but I'll try
					# the other way and come back to this if the other way doesn't work

			w = wcs.WCS(naxis = 2)
			w.wcs.crpix = [0.0, 0.0]
			w.wcs.cdelt = [1.0, 1.0]
			w.wcs.crval = [0.0, 0.0]
			w.wcs.latpole = 90.0
			#w.wcs.cd = [[1, 0], [0, 1]]
			w.wcs.cdfix()

			w_header = w.to_header()

			psf_hdu = fits.open(filename+'_psf_distort.fits', mode = 'update')
			psf_hdu[0].header.extend(w_header)



			if camera == '15':
				chip1 = hdu[4]
				chip2 = hdu[1]
				chips = [chip1, chip2]
				wcsdvarr_1 = hdu[11]
				wcsdvarr_2 = hdu[12]
				wcsdvarr_3 = hdu[13]
				wcsdvarr_4 = hdu[14]
				wcscorr = hdu[15]

				psf_hdu.append(chip2)
				psf_hdu.append(hdu[2])
				psf_hdu[2].data = np.zeros(shape=np.shape(psf_hdu[0].data))
				psf_hdu.append(hdu[3])
				psf_hdu[3].data = np.zeros(shape=np.shape(psf_hdu[0].data))
				psf_hdu.append(chip1)
				psf_hdu.append(hdu[5])
				psf_hdu[5].data = np.zeros(shape=np.shape(psf_hdu[0].data))
				psf_hdu.append(hdu[6])
				psf_hdu[6].data = np.zeros(shape=np.shape(psf_hdu[0].data))
				psf_hdu.append(hdu[7])
				psf_hdu[7].data = hdu[7].data
				psf_hdu.append(hdu[8])
				psf_hdu[8].data = hdu[8].data
				psf_hdu.append(hdu[9])
				psf_hdu[9].data = hdu[9].data
				psf_hdu.append(hdu[10])
				psf_hdu[10].data = hdu[10].data
				## might need to resize all of these
				psf_hdu.append(wcsdvarr_1)
				psf_hdu[11].data = wcsdvarr_1.data
				psf_hdu.append(wcsdvarr_2)
				psf_hdu[12].data = wcsdvarr_2.data
				psf_hdu.append(wcsdvarr_3)
				psf_hdu[13].data = wcsdvarr_3.data
				psf_hdu.append(wcsdvarr_4)
				psf_hdu[14].data = wcsdvarr_4.data
				psf_hdu.append(wcscorr)
				psf_hdu[15].data = wcscorr.data



				if chip == '1':
					chip2.data = np.zeros(shape=np.shape(psf_hdu[0].data))
					chip1.data = psf_hdu[0].data
				if chip == '2':
					chip1.data = np.zeros(shape=np.shape(psf_hdu[0].data))
					chip2.data = psf_hdu[0].data



			if camera == '16':
				psf_hdu.append(hdu[1])
				psf_hdu[1].data = psf_hdu[0].data
				## Not sure if this will require more extensions...
				# can get to that problem when necessary
				psf_hdu[1]["CRPIX1A"] = 37.0
				psf_hdu[1]["CRPIX2A"] = 37.0



			print(psf_hdu.info())

			# print(psf_hdu[0].header)

			os.system('wcslint '+filename+'_psf_distort.fits')

			#fits.writeto(filename+'_psf_distort.fits',  data = psf_hdu[0].data, header = psf_hdu[0].header.extend(w_header), overwrite = True)
			# print(psf_hdu)
			# break




			# flc_hdu = fits.open(i)
			# flc_header = flc_hdu[0].header
			# psf_dat = fits.open(filename+'_psf_distort.fits')[0].data

			# psf_hdu=fits.PrimaryHDU(psf_dat,header=flc_header)
			# psf_hdu.writeto(filename+'_psf_distort.fits',overwrite=True)
			# psf_hdu = fits.open(filename+'_psf_distort.fits')
			# psf_hdu.append(flc_hdu[1])
			# psf_hdu.append(flc_hdu[2])
			# psf_hdu.append(flc_hdu[3])
			# psf_hdu.append(flc_hdu[4])
			# psf_hdu.append(flc_hdu[5])
			# psf_hdu.append(flc_hdu[6])
			# psf_hdu.append(flc_hdu[7])
			# psf_hdu.append(flc_hdu[8])
			# psf_hdu.append(flc_hdu[9])
			# psf_hdu.append(flc_hdu[10])
			# psf_hdu.append(flc_hdu[11])
			# psf_hdu.append(flc_hdu[12])
			# psf_hdu.append(flc_hdu[13])
			# psf_hdu.append(flc_hdu[14])
			# psf_hdu.append(flc_hdu[15])


	tweak()

	# add_df = pd.DataFrame(to_add)

	# for i in range(len(add_df["file"])):
	# 	hdu = fits.open(add_df["file"][i])
	# 	if np.logical_or(chip == '2', chip == None):
	# 		rel_hdu = hdu[1]
	# 	if chip == '1':
	# 		rel_hdu = hdu[4]

	# 	if i != 0:
	# 		iraf.wregister()
# 


	# for file in all_files:
	# 	psfname = file.replace(".fits", "_psf_distort.fits")
	# 	psfname = psfname.replace(path, "")
	# 	if os.path.exists(psfname):
	# 		flc_header = fits.open(file)[0].header
	# 		psf_dat = fits.open(psfname)[0].data

	# 		psf_hdu=fits.PrimaryHDU(psf_dat,header=flc_header)
	# 		psf_hdu.writeto(psfname,overwrite=True)
	# 	else:
	# 		continue






########## This is for the easier way to do this, may need to just project and add myself... normalize?? ############

	for filt in filts:
		print(to_drizzle[filt])

		for i in to_drizzle[filt]:
			psf_hdu = fits.open(i, mode = 'update')
			print(psf_hdu.info())


		astrodrizzle.AstroDrizzle(to_drizzle[filt],
	    output=filt+'_psf_USE',
	    # preserve=False,
	    driz_cr_corr=True,
	    clean=False,
	    configobj=None,
	    final_pixfrac = 0.8,
	    wcskey = ' ', #'TWEAK',
	    build=True,combine_type='imedian', combine_nhigh=3)

generate_file_lists(filts = ["F814W", "F606W", "F475W"], file_types = ["flc", "drc"])
generate_PSFs(filts = ["F814W", "F606W", "F475W"])






from spike import psf


############################################## HST #############################################
acs_path = '/path/to/acs/data'
## files contained in directory:
# j8pu42ecq_flc.fits
# j8pu42egq_flc.fits
# j8pu42esq_flc.fits
# j8pu42evq_flc.fits

### test TinyTim output ###
psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
	inst = 'ACS', camera = 'WFC', method='TinyTim', savedir = 'psfs_tiny', verbose = True,
	pretweaked = False)

# ### test TinyTim (Gillis et al. mod) output ###
psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
	inst = 'ACS', camera = 'WFC', method='TinyTim_Gillis', savedir = 'psfs_tinygillis', verbose = True,
	pretweaked = True)

# ### test STDPSF output ###
psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
	inst = 'ACS', camera = 'WFC', method='stdpsf', savedir = 'psfs_stdpsf', verbose = True,
	pretweaked = True)

# ### test ePSF output ###
psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
	inst = 'ACS', camera = 'WFC', method='epsf', savedir = 'psfs_epsf', verbose = True,
	pretweaked = True, thresh = 200)

# ### test PSFEx output ###
psf.hst(img_dir = acs_path, obj = '10:00:33.0178 +02:09:52.304', img_type = 'flc', 
	inst = 'ACS', camera = 'WFC', method='PSFEx', savedir = 'psfs_psfex', verbose = True,
	pretweaked = True)



############################################# JWST #############################################
nircam_path = '/path/to/nircam/data'
## files contained in directory:
# jw02514162001_03201_00001_nrca2_cal.fits
# jw02514162001_03201_00002_nrca2_cal.fits
# jw02514162001_03201_00003_nrca2_cal.fits

## test WebbPSF output ###
psf.jwst(img_dir = nircam_path, obj = '10:00:31.432 +02:10:26.29', img_type = 'cal',
	inst = 'NIRCam', method='webbpsf', savedir = 'psfs_webbpsf', verbose = True,
	pretweaked = False)

### test STDPSF output ###
psf.jwst(img_dir = nircam_path, obj = '10:00:31.432 +02:10:26.29', img_type = 'tweakregstep', 
	inst = 'NIRCam', method='stdpsf', savedir = 'psfs_jwst_stdpsf', verbose = True,
	pretweaked = True)

### test ePSF output ###
psf.jwst(img_dir = nircam_path, obj = '10:00:31.432 +02:10:26.29', img_type = 'tweakregstep', 
	inst = 'NIRCam', method='epsf', savedir = 'psfs_jwst_epsf', verbose = True,
	pretweaked = True, starselect = 'IRAF', thresh = 3)

### test PSFEx output ###
psf.jwst(img_dir = nircam_path, obj = '10:00:31.432 +02:10:26.29', img_type = 'tweakregstep', 
	inst = 'NIRCam', method='PSFEx', savedir = 'psfs_jwst_psfex', verbose = True,
	pretweaked = True)


################################# code to generate figures #####################################
import matplotlib.pyplot as plt
import numpy as np
import albumpl.cmap
from astropy.io import fits


fig, ax = plt.subplots(1, 5, figsize = (20, 4), gridspec_kw = {'wspace':0.1})

tt = fits.open('psfs_tiny/150d08m15.267s+2d09m52.304s_F475W_psf_drz.fits')
ttim = tt[1].data[325:465, 940:1080]
ax[0].imshow(ttim, vmin = np.percentile(ttim, 20), vmax = np.percentile(ttim, 97), origin = 'lower', cmap = 'LondonCalling_r')
ax[0].text(10, 125, s = 'TinyTim', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[0].axis('off')

ttg = fits.open('psfs_tinygillis/150d08m15.267s+2d09m52.304s_F475W_psf_drz.fits')
ttgim = ttg[1].data[325:465, 940:1080]
ax[1].imshow(ttgim, vmin = np.percentile(ttgim, 20), vmax = np.percentile(ttgim, 97), origin = 'lower', cmap = 'LondonCalling_r')
ax[1].text(10, 125, s = 'TinyTim (Gillis+20)', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[1].axis('off')

std = fits.open('psfs_stdpsf/150d08m15.267s+2d09m52.304s_F475W_psf_drz.fits')
stdim = std[1].data[325:465, 940:1080]
# ax[2].imshow(stdim, vmin = np.percentile(stdim[stdim != 0], 5), vmax = np.percentile(stdim[stdim != 0], 60), origin = 'lower', cmap = 'LondonCalling_r')
ax[2].imshow(stdim, vmin = np.percentile(stdim, 20), vmax = np.percentile(stdim, 99), origin = 'lower', cmap = 'LondonCalling_r')
ax[2].text(10, 125, s = 'STDPSF', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[2].axis('off')

epsf = fits.open('psfs_epsf/150d08m15.267s+2d09m52.304s_F475W_psf_drz.fits')
epsfim = epsf[1].data[325:465, 940:1080]
ax[3].imshow(epsfim, vmin = np.percentile(epsfim, 20), vmax = np.percentile(epsfim, 97), origin = 'lower', cmap = 'LondonCalling_r')
ax[3].text(10, 125, s = 'ePSF', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[3].axis('off')


psfex = fits.open('psfs_psfex/150d08m15.267s+2d09m52.304s_F475W_psf_drz.fits')
psfexim_ = psfex[1].data[325:465, 940:1080]
ax[4].imshow(psfexim_, vmin = np.percentile(psfexim_[psfexim_ >0], 20), vmax = np.percentile(psfexim_[psfexim_ >0], 95), origin = 'lower', cmap = 'LondonCalling_r')
ax[4].text(10, 125, s = 'PSFEx', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[4].axis('off')

fig.savefig('spike_psf_hstcompare.png', bbox_inches = 'tight')


fig, ax = plt.subplots(1, 4, figsize = (16, 4), gridspec_kw = {'wspace':0.1})

jw = fits.open('psfs_webbpsf/100031+021026_F115W_resamplestep.fits')
jwim = jw[1].data[1114-70: 1114+70, 553-70:553+70]
ax[0].imshow(jwim, vmin = np.nanpercentile(jwim, 20), vmax = np.nanpercentile(jwim, 97), origin = 'lower', cmap = 'LondonCalling_r')
ax[0].text(10, 125, s = 'WebbPSF', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[0].axis('off')

std = fits.open('psfs_jwst_stdpsf/100031+021026_F115W_resamplestep.fits')
stdim = std[1].data[1114-70: 1114+70, 553-70:553+70]
ax[1].imshow(stdim, vmin = np.nanpercentile(stdim, 20), vmax = np.nanpercentile(stdim, 99), origin = 'lower', cmap = 'LondonCalling_r')
ax[1].text(10, 125, s = 'STDPSF', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[1].axis('off')

## this one has to be generated with different values than the defaults -- ePSF is very sensitive to threshold value
epsf = fits.open('psfs_jwst_epsf/100031+021026_F115W_resamplestep.fits')
epsfim = epsf[1].data[1114-70: 1114+70, 553-70:553+70]
ax[2].imshow(epsfim, vmin = np.nanpercentile(epsfim, 20), vmax = np.nanpercentile(epsfim, 97), origin = 'lower', cmap = 'LondonCalling_r')
ax[2].text(10, 125, s = 'ePSF', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[2].axis('off')


psfex = fits.open('psfs_jwst_psfex/100031+021026_F115W_resamplestep.fits')
psfexim_ = psfex[1].data[1114-70: 1114+70, 553-70:553+70]
ax[3].imshow(psfexim_, vmin = np.nanpercentile(psfexim_[psfexim_ >0], 20), vmax = np.nanpercentile(psfexim_[psfexim_ >0], 95), origin = 'lower', cmap = 'LondonCalling_r')
ax[3].text(10, 125, s = 'PSFEx', fontsize = 15, fontfamily = 'monospace', color = '#343530')
ax[3].axis('off')


fig.savefig('spike_psf_jwstcompare.png', bbox_inches = 'tight')



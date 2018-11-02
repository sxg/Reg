"""
CLI for 4D image registration of .mat files using the FMRIB Software Library (FSL).
"""

import tempfile as tf
import os
import sys
import time
import click
import numpy as np
import nibabel as nib
import hdf5storage

@click.command()
@click.argument("path")
@click.option("-f", "--fnirt-path", default="/usr/local/fsl/bin/fnirt",
              help="Path to FSL's FNIRT executable. Defaults to /usr/local/fsl/bin/fnirt.")
@click.option("-o", "--output-path", default="./registeredImages.mat",
              help="Output path including file name and .mat extension for registered images.\
               Defaults to current path with file name registeredImages.mat.")
@click.option("-n", "--name", required=True, help="Image dataset name.")
@click.option("-a", "--anchors", default="1",
              help="Comma-separated list of anchor frames. Defaults to the first frame.")
@click.version_option()
def cli(path, fnirt_path, output_path, name, anchors):
    """4D .mat image registration tool using the FMRIB Software Library's FNIRT tool."""

    # Data validation
    _, ext = os.path.splitext(output_path)
    if ext != ".mat":
        sys.exit('Need to specify an output path with .mat file name. You provided {0}.'
                 .format(output_path))
    if os.path.exists(output_path):
        sys.exit('Output path {0} already exists.'.format(output_path))

    # Parse and convert anchor indexes to Python indexes
    anchors = [int(x) - 1 for x in anchors.split(",")]

    # Load the image file
    data = hdf5storage.loadmat(path)
    if not name in data: # Validate the dataset name
        sys.exit('Dataset not found in file at {0}.'.format(path))

    # Load the dataset
    img = np.absolute(data[name])
    img = img / img.flatten().max() * 100 # FSL likes signal intensities 0–100

    # Create a temporary directory and do the work
    with tf.TemporaryDirectory() as tmp_path:
        # Convert .mat to .nii
        mat_to_nii(img, tmp_path)
        # Register the data
        reg_data(fnirt_path, tmp_path, anchors, img.shape[3])
        # Load the registered data
        reg_img = load_reg_vols(tmp_path, anchors, img.shape)
        # Save the registered data
        hdf5storage.savemat(output_path, {"registeredImages": reg_img})

# Helpers

def reg_data(fnirt_path, tmp_path, anchors, n_vols):
    """Registers a dataset using FNIRT."""

    n_reg = 0
    n_to_reg = n_vols - len(anchors)
    click.echo("Registering {0} of {1} volumes.".format(n_to_reg, n_vols))
    start = time.time()

    last_unreg = 0
    for anchor in anchors:
        for vol in range(last_unreg, anchor):
            n_reg += 1
            click.echo("[{0}/{1}] Registering volume {2} to anchor {3}..."
                       .format(n_reg, n_to_reg, (vol + 1), (anchor + 1)))
            reg_vols(fnirt_path, tmp_path, anchor, vol)
        last_unreg = anchor + 1

        # Handle edge case where final volumes are registered to the last anchor
        if anchor == anchors[-1] and anchor != (n_vols - 1):
            for vol in range(last_unreg, n_vols):
                reg_vols(fnirt_path, tmp_path, anchor, vol)

    end = time.time()
    click.echo("Total elapsed time: {0}.".format(elapsed_time(start, end)))

def reg_vols(fnirt_path, tmp_path, anchor, vol):
    """Registers two volumes using FNIRT."""
    anchor_path = os.path.join(tmp_path, "%d.nii" % (anchor + 1))
    vol_path = os.path.join(tmp_path, "%d.nii" % (vol + 1))
    out_path = os.path.join(tmp_path, "%d_reg.nii" % (vol + 1))
    start = time.time()
    os.system("{0} --ref={1} --in={2} --iout={3}"
              .format(fnirt_path, anchor_path, vol_path, out_path))
    end = time.time()
    click.echo("Done. Elapsed time: {0}.".format(elapsed_time(start, end)))

def load_reg_vols(tmp_path, anchors, shape):
    """Loads registered data into a numpy array."""
    reg_img = np.empty(shape=shape)
    for vol in range(0, shape[3]):
        vol_path = ""
        if vol in anchors:
            vol_path = os.path.join(tmp_path, "%d.nii" % (vol + 1))
        else:
            vol_path = os.path.join(tmp_path, "%d_reg.nii.gz" % (vol + 1))
        reg_img[:, :, :, vol] = nib.load(vol_path).get_data()
    return reg_img

def mat_to_nii(img, tmp_path):
    """Save 4D .mat data as individual .nii volume files."""
    for i in range(0, img.shape[3]):
        vol_nii = nib.Nifti1Image(np.squeeze(img[:, :, :, i]), np.eye(4))
        vol_nii.to_filename(os.path.join(tmp_path, "%d.nii" % (i + 1)))

def elapsed_time(start, end):
    """Create a pretty string with the elapsed time."""
    hours, rem = divmod(end - start, 3600)
    mins, secs = divmod(rem, 60)
    return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(mins), secs)

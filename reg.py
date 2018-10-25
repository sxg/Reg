"""
CLI for 4D image registration of .mat files using the FMRIB Software Library (FSL)
"""

import tempfile as tf
import os
import sys
import click
import numpy as np
import nibabel as nib
import hdf5storage

@click.command()
@click.argument("path")
@click.option("-f", "--fnirt-path", default="/usr/local/fsl/bin/fnirt",
              help="Path to FSL's FNIRT executable. Defaults to /usr/local/fsl/bin/fnirt.")
@click.option("-n", "--name", default="regimages", help="Image dataset name.")
@click.option("-a", "--anchors", default="1",
              help="Comma-separated list of anchor frames. Defaults to the first frame.")
def cli(path, fnirt_path, name, anchors):
    """CLI that prints "Hello, world!"""

    # Parse and convert anchor indexes to Python indexes
    anchors = [int(x) - 1 for x in anchors.split(",")]

    # Load the image file
    data = hdf5storage.loadmat(path)
    if not name in data: # Validate the dataset name
        sys.exit('ImageName')

    # Load the dataset
    img = np.absolute(data[name])
    img = img / img.flatten().max() * 100 # FSL likes signal intensities 0–100

    # Create a temporary directory and do the work
    with tf.TemporaryDirectory() as tmp_path:
        click.echo("Created temporary directory: {0}".format(tmp_path))
        # Convert .mat to .nii
        mat_to_nii(img, tmp_path)
        input("Press <Enter> to continue...")

def mat_to_nii(img, tmp_path):
    """Save 4D .mat data as individual .nii volume files."""
    for i in range(0, img.shape[3]):
        vol_nii = nib.Nifti1Image(np.squeeze(img[:, :, :, i]), np.eye(4))
        vol_nii.to_filename(os.path.join(tmp_path, "%d.nii" % (i + 1)))

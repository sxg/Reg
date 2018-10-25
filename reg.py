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
        # Register the data
        reg_data(fnirt_path, tmp_path, anchors, img.shape[3])
        input("Press <Enter> to continue...")

def reg_data(fnirt_path, tmp_path, anchors, n_vols):
    """Registers a dataset using FNIRT."""
    last_unreg = 0
    for anchor in anchors:
        for vol in range(last_unreg, anchor):
            reg_vols(fnirt_path, tmp_path, anchor, vol)
        last_unreg = anchor + 1

        # Handle edge case where final volumes are registered to the last anchor
        if anchor == anchors[-1] and anchor != (n_vols - 1):
            for vol in range(last_unreg, n_vols):
                reg_vols(fnirt_path, tmp_path, anchor, vol)

def reg_vols(fnirt_path, tmp_path, anchor, vol):
    """Registers two volumes using FNIRT."""
    anchor_path = os.path.join(tmp_path, "%d.nii" % (anchor + 1))
    vol_path = os.path.join(tmp_path, "%d.nii" % (vol + 1))
    out_path = os.path.join(tmp_path, "%d_reg.nii" % (vol + 1))
    # Dry run. TO DO: actually execute FNIRT.
    click.echo("{0} --ref={1} --in={2} --iout={3}"
               .format(fnirt_path, anchor_path, vol_path, out_path))

def mat_to_nii(img, tmp_path):
    """Save 4D .mat data as individual .nii volume files."""
    for i in range(0, img.shape[3]):
        vol_nii = nib.Nifti1Image(np.squeeze(img[:, :, :, i]), np.eye(4))
        vol_nii.to_filename(os.path.join(tmp_path, "%d.nii" % (i + 1)))

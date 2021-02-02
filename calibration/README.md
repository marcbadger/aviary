# Plan to improve calibration

## Calibration issues
Calibrations are ok, but not great. We will try to improve them by either:
1. improving detection of apriltags
1. annotating or detecting 3D points that can be seen by multiple cameras
and then jointly optimizing 3D point positions and camera calibration parameters.

## Installation instructions
If you have pytorch and opencv installed, you can probably run this with a few additional packages, which are listed in [requirements.txt](../requirements.txt).
Or you can [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/marcbadger/aviary/blob/calibration_fix/calibration/fix_calibration_notebook.ipynb).

## Running the notebook
If you installed locally,
1. activate the environment
1. ```cd aviary/calibration```
1. ```jupyter notebook fix_calibration_notebook.ipynb```
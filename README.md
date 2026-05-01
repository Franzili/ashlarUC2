**ATTENTION:** This is a modified version used by UC2 and mirrored by PyPi to make it installable for ImSwitch. 

# ASHLAR: Alignment by Simultaneous Harmonization of Layer/Adjacency Registration

## Whole-slide microscopy image stitching and registration in Python

**Ashlar** performs fast, high-quality stitching of microscopy images. It also
co-registers multiple rounds of cyclic imaging for methods such as CyCIF and
CODEX. Ashlar can read image data directly from BioFormats-supported microscope
vendor file formats as well as a directory of plain TIFF files. Output is saved
as pyramidal, tiled OME-TIFF.

Note that Ashlar requires unstitched individual "tile" images as input, so it is
not suitable for microscopes or slide scanners that only provide pre-stitched
images.

**Visit [labsyspharm.github.io/ashlar/](https://labsyspharm.github.io/ashlar/) for the most up-to-date information on ASHLAR.**

## UC2 / ImSwitch extensions

This fork adds two additional input methods on top of the standard Ashlar readers:

### 1. In-memory NumPy array stitching

Pass a pre-loaded `(N_tiles, N_channels, H, W)` numpy array together with an
explicit position list (in microns) and a pixel size:

```python
from ashlarUC2.scripts.ashlar import process_images
import numpy as np

tiles = np.zeros((4, 1, 256, 256), dtype=np.uint16)   # shape: (N, C, H, W)
position_list = np.array([[0, 0], [0, 130], [130, 0], [130, 130]])  # (x, y) µm

process_images(
    filepaths=[tiles],
    output="stitched.ome.tif",
    position_list=position_list,
    pixel_size=0.5,    # µm / pixel
    maximum_shift=50,  # µm
)
```

### 2. ImSwitch individual TIFF tiles (`ImSwitchTiffReader`)

Load tiles that follow the ImSwitch `OMEWriter._write_individual_tiff` filename
convention directly from disk:

```
t{YYYYMMDD_HHMMSS}_x{X}_y{Y}_z{Z}_c{cIdx}_{channelName}_i{iter}_p{power}.tif
```

where `X`, `Y`, `Z` are stage coordinates in µm × 1000.

**Python API:**

```python
from ashlarUC2.scripts.ashlar import process_images, build_imswitch_reader

reader = build_imswitch_reader(
    "/path/to/tiles/timepoint_0000",   # directory or list of file paths
    pixel_size=0.5,   # µm / pixel
)

process_images(
    filepaths=[reader],
    output="stitched.ome.tif",
    maximum_shift=50,
)
```

**Command-line via `convert_experiment_tiffs.py` (ImSwitch post-processing):**

The `convert_experiment_tiffs.py` script in the ImSwitch repository now includes
an `ashlar` stitching mode in addition to the simple grid-placement modes:

```bash
# Ashlar-stitched output only
python convert_experiment_tiffs.py /path/to/tiles --mode ashlar \
    --pixel-size 0.5 --maximum-shift 50 --align-channel 0

# All modes including ashlar
python convert_experiment_tiffs.py /path/to/tiles --mode all \
    --pixel-size 0.5 --maximum-shift 50
```

Output: `<out_dir>/ashlar/ashlar_stitched_t{TTTT}.ome.tif`

The ashlar mode uses sub-pixel edge-alignment across all tiles and is
recommended when accurate registration is required.  Simple grid-placement
modes (`stitch`, `mip`, `tile-config`) remain available for quick previews.

## Usage

```
ashlar [-h] [-o PATH] [-c CHANNEL] [--flip-x] [--flip-y]
       [--flip-mosaic-x] [--flip-mosaic-y]
       [--output-channels CHANNEL [CHANNEL ...]] [-m SHIFT]
       [--stitch-alpha ALPHA] [--filter-sigma SIGMA]
       [--tile-size PIXELS] [--ffp FILE [FILE ...]]
       [--dfp FILE [FILE ...]] [--plates] [-q] [--version]
       FILE [FILE ...]

Stitch and align multi-tile cyclic microscope images

positional arguments:
  FILE                  Image file(s) to be processed, one per cycle

optional arguments:
  -h, --help            Show this help message and exit
  -o PATH, --output PATH
                        Output file. If PATH ends in .ome.tif a pyramidal OME-
                        TIFF will be written. If PATH ends in just .tif and
                        includes {cycle} and {channel} placeholders, a series
                        of single-channel plain TIFF files will be written. If
                        PATH starts with a relative or absolute path to
                        another directory, that directory must already exist.
                        (default: ashlar_output.ome.tif)
  -c CHANNEL, --align-channel CHANNEL
                        Reference channel number for image alignment.
                        Numbering starts at 0. (default: 0)
  --flip-x              Flip tile positions left-to-right
  --flip-y              Flip tile positions top-to-bottom
  --flip-mosaic-x       Flip output image left-to-right
  --flip-mosaic-y       Flip output image top-to-bottom
  --output-channels CHANNEL [CHANNEL ...]
                        Output only specified channels for each cycle.
                        Numbering starts at 0. (default: all channels)
  -m SHIFT, --maximum-shift SHIFT
                        Maximum allowed per-tile corrective shift in microns
                        (default: 15)
  --stitch-alpha ALPHA  Significance level for permutation testing during
                        alignment error quantification. Larger values include
                        more tile pairs in the spanning tree at the cost of
                        increased false positives. (default: 0.01)
  --filter-sigma SIGMA  Filter images before alignment using a Gaussian kernel
                        with s.d. of SIGMA pixels (default: no filtering)
  --tile-size PIXELS    Pyramid tile size for OME-TIFF output (default: 1024)
  --ffp FILE [FILE ...]
                        Perform flat field illumination correction using the
                        given profile image. Specify one common file for all
                        cycles or one file for every cycle. Channel counts
                        must match input files. (default: no flat field
                        correction)
  --dfp FILE [FILE ...]
                        Perform dark field illumination correction using the
                        given profile image. Specify one common file for all
                        cycles or one file for every cycle. Channel counts
                        must match input files. (default: no dark field
                        correction)
  --plates              Enable plate mode for HTS data
  -q, --quiet           Suppress progress display
  --version             Show program's version number and exit
```

## Tests

```bash
# Run all tests
python -m pytest ashlarUC2/test/ -v

# Run only the numpy / ImSwitch tile tests
python -m pytest ashlarUC2/test/test_ashlar_numpy.py -v
# or directly:
python ashlarUC2/test/test_ashlar_numpy.py
```

`test_ashlar_numpy.py` contains two self-contained tests:

| Test | Description |
|------|-------------|
| `test_numpy_stitching` | Stitches 4 synthetic tiles supplied as an in-memory numpy array |
| `test_imswitch_tiff_reader` | Writes synthetic tiles to disk using the ImSwitch filename convention, then reads and stitches them via `ImSwitchTiffReader` |

## Installation

### Pip install

Ashlar can be installed in most Python environments using `pip`:
``` bash
pip install ashlarUC2
```

### Using a conda environment

If you don't already have [miniconda](https://docs.conda.io/en/latest/miniconda.html)
or [Anaconda](https://www.anaconda.com/products/individual), download the python
3.x version and install. Then, run the following commands from a terminal (Linux/Mac)
or command prompt (Windows):

Create a named conda environment with python 3.10:
```bash
conda create -y -n ashlar python=3.10
```

Activate the conda environment:
```bash
conda activate ashlar
```

In the activated environment, install dependencies and ashlar itself:
```bash
conda install -y -c conda-forge numpy scipy matplotlib networkx scikit-image=0.19 scikit-learn "tifffile>=2023.3.15" zarr pyjnius blessed
pip install ashlarUC2
```

### Docker image

The docker image of ashlar is on DockerHub at `labsyspharm/ashlar` which should be
suitable for many use cases.


```
ashlar [-h] [-o PATH] [-c CHANNEL] [--flip-x] [--flip-y]
       [--flip-mosaic-x] [--flip-mosaic-y]
       [--output-channels CHANNEL [CHANNEL ...]] [-m SHIFT]
       [--stitch-alpha ALPHA] [--filter-sigma SIGMA]
       [--tile-size PIXELS] [--ffp FILE [FILE ...]]
       [--dfp FILE [FILE ...]] [--plates] [-q] [--version]
       FILE [FILE ...]

Stitch and align multi-tile cyclic microscope images

positional arguments:
  FILE                  Image file(s) to be processed, one per cycle

optional arguments:
  -h, --help            Show this help message and exit
  -o PATH, --output PATH
                        Output file. If PATH ends in .ome.tif a pyramidal OME-
                        TIFF will be written. If PATH ends in just .tif and
                        includes {cycle} and {channel} placeholders, a series
                        of single-channel plain TIFF files will be written. If
                        PATH starts with a relative or absolute path to
                        another directory, that directory must already exist.
                        (default: ashlar_output.ome.tif)
  -c CHANNEL, --align-channel CHANNEL
                        Reference channel number for image alignment.
                        Numbering starts at 0. (default: 0)
  --flip-x              Flip tile positions left-to-right
  --flip-y              Flip tile positions top-to-bottom
  --flip-mosaic-x       Flip output image left-to-right
  --flip-mosaic-y       Flip output image top-to-bottom
  --output-channels CHANNEL [CHANNEL ...]
                        Output only specified channels for each cycle.
                        Numbering starts at 0. (default: all channels)
  -m SHIFT, --maximum-shift SHIFT
                        Maximum allowed per-tile corrective shift in microns
                        (default: 15)
  --stitch-alpha ALPHA  Significance level for permutation testing during
                        alignment error quantification. Larger values include
                        more tile pairs in the spanning tree at the cost of
                        increased false positives. (default: 0.01)
  --filter-sigma SIGMA  Filter images before alignment using a Gaussian kernel
                        with s.d. of SIGMA pixels (default: no filtering)
  --tile-size PIXELS    Pyramid tile size for OME-TIFF output (default: 1024)
  --ffp FILE [FILE ...]
                        Perform flat field illumination correction using the
                        given profile image. Specify one common file for all
                        cycles or one file for every cycle. Channel counts
                        must match input files. (default: no flat field
                        correction)
  --dfp FILE [FILE ...]
                        Perform dark field illumination correction using the
                        given profile image. Specify one common file for all
                        cycles or one file for every cycle. Channel counts
                        must match input files. (default: no dark field
                        correction)
  --plates              Enable plate mode for HTS data
  -q, --quiet           Suppress progress display
  --version             Show program's version number and exit
```

## Installation

### Pip install

Ashlar can be installed in most Python environments using `pip`:
``` bash
pip install ashlar
```

### Using a conda environment

If you don't already have [miniconda](https://docs.conda.io/en/latest/miniconda.html)
or [Anaconda](https://www.anaconda.com/products/individual), download the python
3.x version and install. Then, run the following commands from a terminal (Linux/Mac)
or command prompt (Windows):

Create a named conda environment with python 3.10:
```bash
conda create -y -n ashlar python=3.10
```

Activate the conda environment:
```bash
conda activate ashlar
```

In the activated environment, install dependencies and ashlar itself:
```bash
conda install -y -c conda-forge numpy scipy matplotlib networkx scikit-image=0.19 scikit-learn "tifffile>=2023.3.15" zarr pyjnius blessed
pip install ashlar
```

### Docker image

The docker image of ashlar is on DockerHub at `labsyspharm/ashlar` which should be
suitable for many use cases.

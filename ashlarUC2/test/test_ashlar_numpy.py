"""
Tests for ashlarUC2 using in-memory numpy arrays and on-disk ImSwitch-style
TIFF tiles.

Usage:
    python -m pytest ashlarUC2/test/test_ashlar_numpy.py -v
    # or run directly:
    python ashlarUC2/test/test_ashlar_numpy.py
"""

import os
import re
import tempfile

import numpy as np
import tifffile

from ashlarUC2.scripts.ashlar import process_images, build_imswitch_reader
from ashlarUC2.reg import ImSwitchTiffReader


# ---------------------------------------------------------------------------
# Helper: create a synthetic gradient tile so adjacent tiles share edge content
# (makes alignment more reliable in tests).
# ---------------------------------------------------------------------------

def _make_tile(x_offset: int, y_offset: int, height: int = 128, width: int = 128,
               dtype=np.uint16) -> np.ndarray:
    """Return a synthetic tile with a smooth intensity gradient that depends on (x, y)."""
    ramp_y = np.linspace(y_offset, y_offset + height, height, dtype=np.float32)
    ramp_x = np.linspace(x_offset, x_offset + width, width, dtype=np.float32)
    tile = (ramp_y[:, None] + ramp_x[None, :]).astype(np.float32)
    # Normalise to dtype range
    info = np.iinfo(dtype)
    tile = (tile / tile.max() * info.max).astype(dtype)
    return tile


# ---------------------------------------------------------------------------
# Test 1: numpy-array in-memory stitching
# ---------------------------------------------------------------------------

def test_numpy_stitching():
    """Stitch 4 synthetic tiles supplied as a numpy array."""
    num_images = 4
    num_channels = 1
    height, width = 128, 128
    pixel_size = 0.5  # µm/px
    # 50 % overlap between tiles → step = 64 px = 32 µm
    step_um = (width // 2) * pixel_size  # 32 µm

    # Build tiles with consistent content at overlapping edges
    tiles = np.zeros((num_images, num_channels, height, width), dtype=np.uint16)
    grid_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (row, col)
    for idx, (row, col) in enumerate(grid_positions):
        tiles[idx, 0] = _make_tile(col * width // 2, row * height // 2)

    # position_list: (x, y) top-left corner of each tile in microns
    # Here x = col * step_um, y = row * step_um
    position_list = np.array(
        [[col * step_um, row * step_um] for row, col in grid_positions],
        dtype=float,
    )

    with tempfile.TemporaryDirectory() as tmp:
        out_file = os.path.join(tmp, "ashlar_numpy_test.tif")
        result = process_images(
            filepaths=[tiles],
            output=out_file,
            align_channel=0,
            flip_x=False,
            flip_y=False,
            flip_mosaic_x=False,
            flip_mosaic_y=False,
            output_channels=None,
            maximum_shift=50,
            stitch_alpha=0.01,
            maximum_error=None,
            filter_sigma=0,
            filename_format="cycle_{cycle}_channel_{channel}.tif",
            pyramid=False,
            tile_size=1024,
            ffp=None,
            dfp=None,
            barrel_correction=0,
            plates=False,
            quiet=True,
            position_list=position_list,
            pixel_size=pixel_size,
        )
        assert result == 0 or result is None, f"process_images returned {result}"
        assert os.path.isfile(out_file), "Output TIFF not written"
        mosaic = tifffile.imread(out_file)
        assert mosaic.ndim >= 2, "Output must be at least 2-D"
        print(f"  numpy test passed – mosaic shape: {mosaic.shape}")


# ---------------------------------------------------------------------------
# Test 2: on-disk ImSwitch TIFF stitching via ImSwitchTiffReader
# ---------------------------------------------------------------------------

def test_imswitch_tiff_reader():
    """Load synthetic ImSwitch-style TIFFs from disk and stitch with ashlar."""
    height, width = 128, 128
    pixel_size = 0.5  # µm/px — 1 px = 0.5 µm

    # 4-tile 2×2 grid with 50% overlap
    # step in µm * 1000 (integer storage convention)
    step_um1000 = int((width // 2) * pixel_size * 1000)   # 32000

    grid = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (row_idx, col_idx)
    timestamp = "20260426_144148"

    with tempfile.TemporaryDirectory() as tmp:
        tile_dir = os.path.join(tmp, "tiles", "timepoint_0000")
        os.makedirs(tile_dir)

        file_paths = []
        for iterator, (row, col) in enumerate(grid):
            x_um1000 = col * step_um1000
            y_um1000 = row * step_um1000
            fname = (
                f"t{timestamp}"
                f"_x{x_um1000}"
                f"_y{y_um1000}"
                f"_z0"
                f"_c0_LED"
                f"_i{iterator:04d}"
                f"_p11755.tif"
            )
            tile = _make_tile(col * width // 2, row * height // 2,
                              height=height, width=width)
            fpath = os.path.join(tile_dir, fname)
            tifffile.imwrite(fpath, tile)
            file_paths.append(fpath)

        # Test reader directly
        reader = ImSwitchTiffReader(file_paths, pixel_size=pixel_size)
        assert reader.metadata.num_channels == 1
        assert reader.metadata._num_images == 4
        img0 = reader.read(0, 0)
        assert img0.shape == (height, width)

        # Test via process_images
        out_file = os.path.join(tmp, "ashlar_imswitch_test.ome.tif")
        reader2 = build_imswitch_reader(file_paths, pixel_size=pixel_size)
        result = process_images(
            filepaths=[reader2],
            output=out_file,
            align_channel=0,
            maximum_shift=50,
            quiet=True,
        )
        assert result == 0 or result is None, f"process_images returned {result}"
        assert os.path.isfile(out_file), "Output OME-TIFF not written"
        mosaic = tifffile.imread(out_file)
        assert mosaic.ndim >= 2, "Output must be at least 2-D"
        print(f"  imswitch test passed – mosaic shape: {mosaic.shape}")


# ---------------------------------------------------------------------------
# Run standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running test_numpy_stitching ...")
    test_numpy_stitching()
    print("Running test_imswitch_tiff_reader ...")
    test_imswitch_tiff_reader()
    print("All tests passed.")


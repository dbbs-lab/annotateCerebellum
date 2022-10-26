"""
This module proposes tools and interfaces to visualize and modify volumetric annotation for the
cerebellum.

.. autosummary::

   annotation_image
   canvas_image
   paint_tools
   utils

"""
__version__ = "0.0.1"
__author__ = "Dimitri RODARIE"

from annotate_cerebellum.utils import load_nrrd_npy_file, save_nrrd_npy_file
from annotate_cerebellum.annotation_image import AnnotationImage
from annotate_cerebellum.canvas_image import AutoScrollbar, CanvasImage
from annotate_cerebellum.paint_tools import PaintTools

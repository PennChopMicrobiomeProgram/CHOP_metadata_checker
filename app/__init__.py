import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "metadatalib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from app.metadatalib.src.metadatalib import __version__ as metadatalib_version

__version__ = metadatalib_version

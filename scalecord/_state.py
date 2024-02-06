"""
* Global Application State
"""
# Standard Library Imports
from pathlib import Path
import os

# Pathing
_ROOT = Path(__file__).parent.parent
if _ROOT != Path(os.getcwd()):
    os.chdir(_ROOT)

__all__ = ['_ROOT']

__author__ = 'Arve Seljebu'
__email__ = 'arve.seljebu@gmail.com'
from os.path import join, dirname
__version__ = open(join(dirname(__file__), 'VERSION')).read().strip()

__all__ = ['Experiment', 'compress', 'decompress',
            'attribute', 'attribute_as_str', 'attributes']

from .experiment import (Experiment, compress, decompress,
                            attribute, attribute_as_str, attributes)

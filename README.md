# leicaexperiment

[![build-status-image]][travis]
[![pypi-version]][pypi]
[![wheel]][pypi]

## Overview
This is a python module for interfacing with *Leica LAS AF/X Matrix Screener*
experiments.

The module can be used to:

- stitch wells from an experiment exported with the *LAS AF Data Exporter*
- batch compress images lossless
- programmatically select slides/wells/fields/images given by attributes like
    - slide (S)
    - well position (U, V)
    - field position (X, Y)
    - z-stack position (Z)
    - channel (C)


## Features

- Access experiment as a python object
- Compress to PNGs without loosing precision, metadata or colormap
- ImageJ stitching (Fiji is installed via [fijibin](https://github.com/arve0/fijibin))


## Installation

Install using `pip`...

```bash
pip install leicaexperiment
```

## Examples

#### stitch experiment
```python
from leicaexperiment import Experiment

# path should contain AditionalData and slide--S*
experiment = Experiment('path/to/experiment')

# if path is omitted, experiment path is used for output files
stitched_images = experiment.stitch('/path/to/output/files/')

# get information about placement of images in the stitch
xs, ys, attrs = experiment.stitch_coordinates(well_x=0, well_y=0)
```

#### stitch specific well
```python
from leicaexperiment import Experiment

# path should contain AditionalData and slide--S*
stitched_images = experiment.stitch('/path/to/well')
```

#### do stuff on all images
```python
from leicaexperiment import Experiment

experiment = Experiment('path/to/experiment--')

for image in experiment.images:
    do stuff...
```

#### do stuff on specific wells/fields
```python
from leicaexperiment import attribute

# select specific parts
selected_wells = [well for well in experiment.wells if 'U00' in well]
for well in selected_wells:
    do stuff...

def condition(path):
    x_above = attribute(path, 'X') > 1
    x_below = attribute(path, 'X') < 5
    return x_above and x_below

selected_fields = [field for field in experiment.fields if condition(field)]
for field in selected_fields:
    do stuff..
```

#### subtract data
```python
from leicaexperiment import attribute

# get all channels
channels = [attribute(image, 'C') for image in experiment.images]
min_ch, max_ch = min(channels), max(channels)
```

#### batch lossless compress of experiment
```python
from leicaexperiment import Experiment, compress

e = Experiment('/path/to/experiment')
pngs = compress(e.images)
print(pngs)
```


## API reference

API reference is at http://leicaexperiment.rtfd.org.


## Development
Install dependencies and link development version of leicaexperiment to pip:
```bash
git clone https://github.com/arve0/leicaexperiment
cd leicaexperiment
pip install -r requirements.txt
```

#### run test
```bash
pip install tox
tox
```

#### extra output, jump into pdb upon error
```bash
DEBUG=leicaexperiment tox -- --pdb -s
```

#### build api reference
```bash
pip install -r docs/requirements.txt
make docs
```



[build-status-image]: https://secure.travis-ci.org/arve0/leicaexperiment.png?branch=master
[travis]: http://travis-ci.org/arve0/leicaexperiment?branch=master
[pypi-version]: https://pypip.in/version/leicaexperiment/badge.svg
[pypi]: https://pypi.python.org/pypi/leicaexperiment
[wheel]: https://pypip.in/wheel/leicaexperiment/badge.svg

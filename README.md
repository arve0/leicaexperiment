# LeicaExperiment #
This is an python class which can be used to read the structured output from a Leica LAS Matrix Scan when using the data exporter (ome.tifs organized in slide/chamber/field folders).

## Install ##
```
pip install leicaexperiment
```

## Examples ##
### merge z-stack ###
```
from leicaexperiment import Experiment
experiment = Experiment('path/to/experiment--')
for well in experiment.wells:
    for channel in range(well.channels):
        for z in range(well.z_stacks):
            img = well.merge(z, channel)
            do stuff...
```

### do stuff on all images ###
```
experiment = Experiment('path/to/experiment--')
for well in experiment.wells:
    for field in well.fields:
        for image in field.images:
            image_data = imread(image.fullpath)
            do stuff...
```
Also see [merger.py](/merger.py) example.


## Dependencies ##
- tifffile
- numpy

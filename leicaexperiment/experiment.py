# encoding: utf-8
"""
Access matrix scans from Leica LAS AF MatrixScreener (Data Exporter)
through an object.
"""
##
# imports
##
import ast, os, re, pydebug, fijibin.macro
from collections import namedtuple
from lxml import objectify

# multiprocessing
from .utils import chop
from joblib import Parallel, delayed
from multiprocessing import cpu_count

try:
    _pools = cpu_count()
except NotImplementedError:
    _pools = 4

# compress
import json
from PIL import Image
from PIL.ImagePalette import ImagePalette
from copy import copy

# debug with `DEBUG=leicaexperiment python script.py`
debug = pydebug.debug('leicaexperiment')

# glob for consistent cross platform behavior
def glob(pattern):
    "Sorted glob."
    from glob import glob as sysglob
    return sorted(sysglob(pattern))

# variables in case custom folders
_slide = 'slide'
_chamber = 'chamber'
_field = 'field'
_image = 'image'
_additional_data = 'AdditionalData'
_scanning_template = r'{ScanningTemplate}'


# classes
class Experiment:
    def __init__(self, path):
        """Leica LAS AF MatrixScreener experiment.

        Parameters
        ----------
        path : string
            Path to matrix scan containing ``slide-SXX`` and ``AdditinalData``.

        Attributes
        ----------
        path : string
            Full path to experiment.
        dirname : string
            Path to folder below experiment.
        basename : string
            Foldername of experiment.
        """
        _set_path(self, path)

        self._slide_path = _pattern(self.path, _slide)
        self._well_path = _pattern(self._slide_path, _chamber)
        self._field_path = _pattern(self._well_path, _field)
        self._image_path = _pattern(self._field_path, _image)

        # alias
        self.chambers = self.wells

    @property
    def slides(self):
        "List of paths to slides."
        return glob(self._slide_path)

    @property
    def wells(self):
        "List of paths to wells."
        return glob(self._well_path)

    @property
    def fields(self):
        "List of paths to fields."
        return glob(self._field_path)

    @property
    def images(self):
        "List of paths to images."
        tifs = _pattern(self._image_path, extension='tif')
        pngs = _pattern(self._image_path, extension='png')
        imgs = []
        imgs.extend(glob(tifs))
        imgs.extend(glob(pngs))
        return imgs

    @property
    def stitched(self):
        "List of stitched images if they are in experiment folder."
        return glob(_pattern(self.path, 'stitched'))

    @property
    def scanning_template(self):
        "Path to {ScanningTemplate}name.xml of experiment."
        tmpl = glob(_pattern(self.path, _additional_data, _scanning_template,
                        extension='*.xml'))
        if tmpl:
            return tmpl[0]
        else:
            return ''

    def __str__(self):
        return 'leicaexperiment.Experiment({})'.format(self.path)

    def __repr__(self):
        return self.__str__()


    def image(self, well_x, well_y, field_x, field_y):
        """Get path of specified image.

        Parameters
        ----------
        well_x : int
            Starts at 0.
        well_y : int
            Starts at 0.
        field_x : int
            Starts at 0.
        field_y : int
            Starts at 0.

        Returns
        -------
        string
            Path to image or empty string if image is not found.
        """
        return next((i for i in self.images
                     if attribute(i, 'u') == well_x and
                        attribute(i, 'v') == well_y and
                        attribute(i, 'x') == field_x and
                        attribute(i, 'y') == field_y), '')


    def well_images(self, well_x, well_y):
        """Get list of paths to images in specified well.


        Parameters
        ----------
        well_x : int
            Starts at 0.
        well_y : int
            Starts at 0.

        Returns
        -------
        list of strings
            Paths to images or empty list if no images are found.
        """
        return list(i for i in self.images
                    if attribute(i, 'u') == well_x and
                       attribute(i, 'v') == well_y)


    def columns(self, well_x, well_y):
        """List of columns for given well.

        Parameters
        ----------
        well_x : int
            Starts at 0.
        well_y : int
            Starts at 0.

        Returns
        -------
        list of ints
            Columns found for specified well.
        """
        imgs = self.well_images(well_x, well_y)
        return list(set([attribute(img, 'y') for img in imgs]))


    def rows(self, well_x, well_y):
        """List of rows for given well.

        Parameters
        ----------
        well_x : int
            Starts at 0.
        well_y : int
            Starts at 0.

        Returns
        -------
        list of ints
            Rows found for specified well.
        """
        imgs = self.well_images(well_x, well_y)
        return list(set([attribute(img, 'x') for img in imgs]))


    def stitch(self, folder=None):
        """Stitches all wells in experiment with ImageJ. Stitched images are
        saved in experiment root.

        Images which already exists are omitted stitching.

        Parameters
        ----------
        folder : string
            Where to store stitched images. Defaults to experiment path.

        Returns
        -------
        list
            Filenames of stitched images. Files which already exists before
            stitching are also returned.
        """
        debug('stitching ' + self.__str__())
        if not folder:
            folder = self.path

        # create list of macros and files
        macros = []
        files = []
        for well in self.wells:
            f,m = stitch_macro(well, folder)
            macros.extend(m)
            files.extend(f)

        chopped_arguments = zip(chop(macros, _pools), chop(files, _pools))
        chopped_filenames = Parallel(n_jobs=_pools)(delayed(fijibin.macro.run)
                                      (macro=arg[0], output_files=arg[1])
                                      for arg in chopped_arguments)

        # flatten
        return [f for list_ in chopped_filenames for f in list_]


    def compress(self, delete_tif=False, folder=None):
        """Lossless compress all images in experiment to PNG. If folder is
        omitted, images will not be moved.

        Images which already exists in PNG are omitted.

        Parameters
        ----------
        folder : string
            Where to store PNGs. Defaults to the folder they are in.
        delete_tif : bool
            If set to truthy value, ome.tifs will be deleted after compression.

        Returns
        -------
        list
            Filenames of PNG images. Files which already exists before
            compression are also returned.
        """
        return compress(self.images, delete_tif, folder)


    def field_metadata(self, well_x=0, well_y=0, field_x=0, field_y=0):
        """Get OME-XML metadata of given field.

        Parameters
        ----------
        well_x : int
            X well coordinate.
        well_y : int
            Y well coordinate.
        field_x : int
            X field coordinate.
        field_y : int
            Y field coordinate.

        Returns
        -------
        lxml.objectify.ObjectifiedElement
            lxml object of OME-XML found in slide/chamber/field/metadata.
        """
        def condition(path):
            attrs = attributes(path)
            return (attrs.u == well_x and attrs.v == well_y
                        and attrs.x == field_x and attrs.y == field_y)

        field = [f for f in self.fields if condition(f)]

        if field:
            field = field[0]
            filename = _pattern(field, 'metadata', _image, extension='*.ome.xml')
            filename = glob(filename)[0] # resolve, assume found
            return objectify.parse(filename).getroot()


    def stitch_coordinates(self, well_x=0, well_y=0):
        """Get a list of stitch coordinates for the given well.

        Parameters
        ----------
        well_x : int
            X well coordinate.
        well_y : int
            Y well coordinate.

        Returns
        -------
        (xs, ys, attr) : tuples with float and collections.OrderedDict
            Tuple of x's, y's and attributes.
        """
        well = [w for w in self.wells
                    if attribute(w, 'u') == well_x and
                       attribute(w, 'v') == well_y]

        if len(well) == 1:
            well = well[0]
            tile = os.path.join(well, 'TileConfiguration.registered.txt')

            with open(tile) as f:
                data = [x.strip()
                            for l in f.readlines()
                                if l[0:7] == 'image--'
                                    for x in l.split(';')] # flat list
                coordinates = (ast.literal_eval(x) for x in data[2::3])
                # flatten
                coordinates = sum(coordinates, ())
                attr = tuple(attributes(x) for x in data[0::3])
            return coordinates[0::2], coordinates[1::2], attr

        else:
            print('leicaexperiment stitch_coordinates({}, {}) Well not found'.format(well_x, well_y))



# methods
def stitch_macro(path, output_folder=None):
    """Create fiji-macros for stitching all channels and z-stacks for a well.

    Parameters
    ----------
    path : string
        Well path.
    output_folder : string
        Folder to store images. If not given well path is used.

    Returns
    -------
    output_files, macros : tuple
        Tuple with filenames and macros for stitched well.
    """
    output_folder = output_folder or path
    debug('stitching ' + path + ' to ' + output_folder)

    fields = glob(_pattern(path, _field))

    # assume we have rectangle of fields
    xs = [attribute(field, 'X') for field in fields]
    ys = [attribute(field, 'Y') for field in fields]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    fields_x = len(set(xs))
    fields_y = len(set(ys))

    # assume all fields are the same
    # and get properties from images in first field
    images = glob(_pattern(fields[0], _image))

    # assume attributes are the same on all images
    attr = attributes(images[0])

    # find all channels and z-stacks
    channels = []
    z_stacks = []
    for image in images:
        channel = attribute_as_str(image, 'C')
        if channel not in channels:
            channels.append(channel)

        z = attribute_as_str(image, 'Z')
        if z not in z_stacks:
            z_stacks.append(z)

    debug('channels ' + str(channels))
    debug('z-stacks ' + str(z_stacks))

    # create macro
    _, extension = os.path.splitext(images[-1])
    if extension == '.tif':
        # assume .ome.tif
        extension = '.ome.tif'
    macros = []
    output_files = []
    for Z in z_stacks:
        for C in channels:
            filenames = os.path.join(

                    _field + '--X{xx}--Y{yy}',
                    _image + '--L' + attr.L +
                    '--S' + attr.S +
                    '--U' + attr.U +
                    '--V' + attr.V +
                    '--J' + attr.J +
                    '--E' + attr.E +
                    '--O' + attr.O +
                    '--X{xx}--Y{yy}' +
                    '--T' + attr.T +
                    '--Z' + Z +
                    '--C' + C +
                    extension)
            debug('filenames ' + filenames)

            cur_attr = attributes(filenames)._asdict()
            output_file = 'stitched--U{U}--V{V}--C{C}--Z{Z}.png'.format(**cur_attr)

            output = os.path.join(output_folder, output_file)
            debug('output ' + output)
            output_files.append(output)
            if os.path.isfile(output):
                # file already exists
                print('leicaexperiment stitched file already exists {}'.format(output))
                continue
            macros.append(fijibin.macro.stitch(path, filenames,
                                  fields_x, fields_y,
                                  output_filename=output,
                                  x_start=x_min, y_start=y_min))

    return (output_files, macros)


def compress(images, delete_tif=False, folder=None):
    """Lossless compression. Save images as PNG and TIFF tags to json. Can be
    reversed with `decompress`. Will run in multiprocessing, where
    number of workers is decided by ``leicaexperiment.experiment._pools``.

    Parameters
    ----------
    images : list of filenames
        Images to lossless compress.
    delete_tif : bool
        Wheter to delete original images.
    folder : string
        Where to store images. Basename will be kept.

    Returns
    -------
    list of filenames
        List of compressed files.
    """
    if type(images) == str:
        # only one image
        return [compress_blocking(images, delete_tif, folder)]

    filenames = copy(images) # as images property will change when looping


    return Parallel(n_jobs=_pools)(delayed(compress_blocking)
                     (image=image, delete_tif=delete_tif, folder=folder)
                     for image in filenames)


def compress_blocking(image, delete_tif=False, folder=None, force=False):
    """Lossless compression. Save image as PNG and TIFF tags to json. Process
    can be reversed with `decompress`.

    Parameters
    ----------
    image : string
        TIF-image which should be compressed lossless.
    delete_tif : bool
        Wheter to delete original images.
    force : bool
        Wheter to compress even if .png already exists.

    Returns
    -------
    string
        Filename of compressed image, or empty string if compress failed.
    """

    debug('compressing {}'.format(image))
    try:
        new_filename, extension = os.path.splitext(image)
        # remove last occurrence of .ome
        new_filename = new_filename.rsplit('.ome', 1)[0]

        # if compressed file should be put in specified folder
        if folder:
            basename = os.path.basename(new_filename)
            new_filename = os.path.join(folder, basename + '.png')
        else:
            new_filename = new_filename + '.png'

        # check if png exists
        if os.path.isfile(new_filename) and not force:
            compressed_images.append(new_filename)
            msg = "Aborting compress, PNG already exists: {}".format(new_filename)
            raise AssertionError(msg)
        if extension != '.tif':
            msg = "Aborting compress, not a TIFF: {}".format(image)
            raise AssertionError(msg)

        # open image, load and close file pointer
        img = Image.open(image)
        fptr = img.fp # keep file pointer, for closing
        img.load() # load img-data before switching mode, also closes fp

        # get tags and save them as json
        tags = img.tag.as_dict()
        with open(new_filename[:-4] + '.json', 'w') as f:
            if img.mode == 'P':
                # keep palette
                tags['palette'] = img.getpalette()
            json.dump(tags, f)

        # check if image is palette-mode
        if img.mode == 'P':
            # switch to luminance to keep data intact
            debug('palette-mode switched to luminance')
            img.mode = 'L'
        if img.mode == 'I;16':
            # https://github.com/python-pillow/Pillow/issues/1099
            img = img.convert(mode='I')

        # compress/save
        debug('saving to {}'.format(new_filename))
        img.save(new_filename)

        fptr.close() # windows bug Pillow
        if delete_tif:
            os.remove(image)

    except (IOError, AssertionError) as e:
        # print error - continue
        print('leicaexperiment {}'.format(e))
        return ''

    return new_filename



def decompress(images, delete_png=False, delete_json=False, folder=None):
    """Reverse compression from tif to png and save them in original format
    (ome.tif). TIFF-tags are gotten from json-files named the same as given
    images.


    Parameters
    ----------
    images : list of filenames
        Image to decompress.
    delete_png : bool
        Wheter to delete PNG images.
    delete_json : bool
        Wheter to delete TIFF-tags stored in json files on compress.

    Returns
    -------
    list of filenames
        List of decompressed files.
    """
    if type(images) == str:
        # only one image
        return decompress([images])

    filenames = copy(images) # as images property will change when looping

    decompressed_images = []
    for orig_filename in filenames:
        debug('decompressing {}'.format(orig_filename))
        try:
            filename, extension = os.path.splitext(orig_filename)

            # if decompressed file should be put in specified folder
            if folder:
                basename = os.path.basename(filename)
                new_filename = os.path.join(folder, basename + '.ome.tif')
            else:
                new_filename = filename + '.ome.tif'

            # check if tif exists
            if os.path.isfile(new_filename):
                decompressed_images.append(new_filename)
                msg = "Aborting decompress, TIFF already exists: {}".format(orig_filename)
                raise AssertionError(msg)
            if extension != '.png':
                msg = "Aborting decompress, not a PNG: {}".format(orig_filename)
                raise AssertionError(msg)

            # open image, load and close file pointer
            img = Image.open(orig_filename)
            img.load() # load img-data before switching mode, also closes fp

            # get tags from json
            info = {}
            with open(filename + '.json', 'r') as f:
                tags = json.load(f)
                # convert dictionary to original types (lost in json conversion)
                for tag,val in tags.items():
                    if tag == 'palette':
                        # hack hack
                        continue
                    if type(val) == list:
                        val = tuple(val)
                    if type(val[0]) == list:
                        # list of list
                        val = tuple(tuple(x) for x in val)
                    info[int(tag)] = val

            # check for color map
            if 'palette' in tags:
                img.putpalette(tags['palette'])

            # save as tif
            debug('saving to {}'.format(new_filename))
            img.save(new_filename, tiffinfo=info)
            decompressed_images.append(new_filename)

            if delete_png:
                os.remove(orig_filename)
            if delete_json:
                os.remove(filename + '.json')

        except (IOError, AssertionError) as e:
            # print error - continue
            print('leicaexperiment {}'.format(e))

    return decompressed_images


def attribute(path, name):
    """Returns the two numbers found behind --[A-Z] in path. If several matches
    are found, the last one is returned.

    Parameters
    ----------
    path : string
        String with path of file/folder to get attribute from.
    name : string
        Name of attribute to get. Should be A-Z or a-z (implicit converted to
        uppercase).

    Returns
    -------
    integer
        Returns number found in path behind --name as an integer.
    """
    matches = re.findall('--' + name.upper() + '([0-9]{2})', path)
    if matches:
        return int(matches[-1])
    else:
        return None


def attribute_as_str(path, name):
    """Returns the two numbers found behind --[A-Z] in path. If several matches
    are found, the last one is returned.

    Parameters
    ----------
    path : string
        String with path of file/folder to get attribute from.
    name : string
        Name of attribute to get. Should be A-Z or a-z (implicit converted to
        uppercase).

    Returns
    -------
    string
        Returns two digit number found in path behind --name.
    """
    matches = re.findall('--' + name.upper() + '([0-9]{2})', path)
    if matches:
        return matches[-1]
    else:
        return None

def attributes(path):
    """Get attributes from path based on format --[A-Z]. Returns namedtuple
    with upper case attributes equal to what found in path (string) and lower
    case as int. If path holds several occurrences of same character, only the
    last one is kept.

        >>> attrs = attributes('/folder/file--X00-X01.tif')
        >>> print(attrs)
        namedtuple('attributes', 'X x')('01', 1)
        >>> print(attrs.x)
        1

    Parameters
    ----------
    path : string

    Returns
    -------
    collections.namedtuple
    """
    # number of charcters set to numbers have changed in LAS AF X !!
    matches = re.findall('--([A-Z]{1})([0-9]{2,4})', path)

    keys = []
    values = []
    for k,v in matches:
        if k in keys:
            # keep only last key
            i = keys.index(k)
            del keys[i]
            del values[i]
        keys.append(k)
        values.append(v)

    lower_keys = [k.lower() for k in keys]
    int_values= [int(v) for v in values]

    attributes = namedtuple('attributes', keys + lower_keys)

    return attributes(*values + int_values)



# helper functions
def _pattern(*names, **kwargs):
    """Returns globbing pattern for name1/name2/../lastname + '--*' or
    name1/name2/../lastname + extension if parameter `extension` it set.

    Parameters
    ----------
    names : strings
        Which path to join. Example: _pattern('path', 'to', 'experiment') will
        return `path/to/experiment--*`.
    extension : string
        If other extension then --* is wanted.
        Example: _pattern('path', 'to', 'image', extension='*.png') will return
        `path/to/image*.png`.

    Returns
    -------
    string
        Joined glob pattern string.
    """
    if 'extension' not in kwargs:
        kwargs['extension'] = '--*'
    return os.path.join(*names) + kwargs['extension']


def _set_path(self, path):
    "Set self.path, self.dirname and self.basename."
    import os.path
    self.path = os.path.abspath(path)
    self.dirname = os.path.dirname(path)
    self.basename = os.path.basename(path)

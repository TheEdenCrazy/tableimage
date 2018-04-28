"""
Contains a universal API for providing access to two-dimensional data, even without PIL (though it is officially added as a library)
"""
import abc
from ._typing import *
from . import imagemanipulation
try:
    from PIL import Image
    _has_pil=True
except ImportError as e:
    from _dummy_pil import Image
    _has_pil=False


class RowDivider(object):
    """
    Class to divide rows in a list of things.
    """
    def __eq__(self, other) -> bool:
        return isinstance(other, RowDivider)

    def __hash__(self) -> int:
        return id(RowDivider)

RGB=Tuple[int, int, int]


class PixelAccess(abc.ABC):
    """
    Provide API for accessing and analysing pixels.
    """
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def getsize(self) -> Tuple[int, int]:
        """
        Get the size of the image in pixels. (width, height)
        """

    @abc.abstractmethod
    def getpixel(self, x: int, y: int) -> RGB:
        """
        Get the pixel value for a given set of co-ordinates, as an (R, G, B) tuple. (0, 0) is top-left.
        Can throw an index-error if out of range, though implementations can allow out-of-range access. 
        """

    def getcontiguousrows(self) -> List[Union[Tuple[int, RGB], RowDivider]]:
        """
        Convert the image into a list of rows of contiguous colour. This returns a list of tuples containing a length and colour. 
        This list also contains RowDivider instances where one row of pixels jumps to the next. Any output of this function can 
        be guaranteed to have one RowDivider at the end of each row, including at the end of the final row.

        A default implementation is provided, but if a more efficient one is available, override this function.
        """
        result = []
        for y in range(self.getsize()[1]):
            curr_colour=None
            pixel_count=0
            for x in range(self.getsize()[0]):  # Go over all the pixels on the row.
                pixel_colour = self.getpixel(x, y)
                if curr_colour != pixel_colour:
                    if curr_colour is not None: # Otherwise we get mysterious NoneTypes down the road.
                        result.append((pixel_count, curr_colour))
                    curr_colour=pixel_colour
                    pixel_count=1
                else:
                    pixel_count += 1  # This row got 1 pixel longer.
            # Add the last one and a RowDivider
            result.append((pixel_count, curr_colour))
            result.append(RowDivider())
        return result


class PixelAccessPillow(PixelAccess):
    """
    Pixel access for a Pillow/PIL image. If the image contains transparency, it must be blended with a background 
    colour (default is white).
    """
    def __init__(self, image: Image.Image, background: RGB=(255, 255, 255)):
        """
        Create an RGB pixel accessor to a PIL image. Note that if the image has alpha-transparency, it must be blended with a background
        colour - default is white.
        """
        super().__init__()
        if not _has_pil:
            raise NotImplementedError()
        if 'A' in image.getbands():
            self._image: Image.Image = imagemanipulation.pure_pil_alpha_to_background_colour_img(image.convert(mode="RGBA"), background)
        else:
            self._image: Image.Image = image.convert(mode="RGB")

    def getsize(self) -> Tuple[int, int]:
        return self._image.size

    def getpixel(self, x, y) -> RGB:
        return self._image.getpixel((x, y))

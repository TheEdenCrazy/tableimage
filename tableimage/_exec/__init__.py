"""
Used for running the module as an independent program rather than using it as a library.
"""
from .. import imagemanipulation, rowlist_to_html_css, data
import argparse
import sys
_sys = sys
from . import info
from PIL import Image
from .._typing import *


class FileTypeWithAppendMode(object):
    """Factory for creating file object types

    Instances of FileType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.

    Based on the class from argparse, but allowing for certain stuff with mode a where the primary purpose is writing.
    """

    def __init__(self, mode='r', bufsize=-1, encoding=None, errors=None):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                return _sys.stdin
            elif 'w' in self._mode or 'a' in self._mode:
                return _sys.stdout
            else:
                msg = _('argument "-" with mode %r') % self._mode
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as e:
            message = _("can't open '%s': %s")
            raise ArgumentTypeError(message % (string, e))

    def __repr__(self):
        args = self._mode, self._bufsize
        kwargs = [('encoding', self._encoding), ('errors', self._errors)]
        args_str = ', '.join([repr(arg) for arg in args if arg != -1] +
                             ['%s=%r' % (kw, arg) for kw, arg in kwargs
                              if arg is not None])
        return '%s(%s)' % (type(self).__name__, args_str)


def make_parser() -> argparse.ArgumentParser:
    """
    Create a parser for the command-line args.
    """
    parser = argparse.ArgumentParser(
        description=info.program_info
    )

    # First images for input.

    parser.add_argument(
       "images", metavar="<image>", help=info.images_info, nargs="+", type=argparse.FileType(mode='rb')
    )
    
    # css control
    parser.add_argument(
        "--no-css", action="store_true", default=False, help=info.no_css_info
    )

    parser.add_argument(
        "--full-document", action='store_true', default=False, help=info.full_document_info
    )

    output_group = parser.add_mutually_exclusive_group()  # Currently no support for descriptions. TODO: When argparse adds support 
    # add it too.

    # a opens the file for writing without erasing its contents. If we are in append mode, this means we can skip to the end without 
    # destroying the file on open.
    # Combined output
    output_group.add_argument('--combined', help=info.combined_output_info, default=None, type=FileTypeWithAppendMode(mode='a'))

    # Seperated output
    output_group.add_argument('--seperate', help=info.separate_output_info, 
            default=None, type=FileTypeWithAppendMode(mode='a'), nargs=2, metavar=("HTML_FILE", "CSS_FILE"))

    parser.add_argument(
        "--append", action='store_true', default=False, help=info.append_info
    )

    parser.add_argument(
        "--pixel-size", type=int, default=3, help=info.pixel_size_info
    )

    # Background colour
    parser.add_argument(
            "--background-colour", 
            type=lambda x: min(255, max(0, int(x))), 
            default=(255, 255, 255), 
            help=info.background_colour_info,
            nargs=3,
            metavar=("R", "G", "B",)
    )
    
    return parser

def combine_html_css(html_template_chunk: str, css_template_chunk: str) -> str:
    """
    Take a generated HTML chunk and glue it on to a generated css chunk, returning another HTML chunk, using <style> tags.
    """
    html_out = html_template_chunk
    if len(css_template_chunk.strip()) > 0:
        html_out += '\n<style>\n' + css_template_chunk + '\n</style>\n'
    return html_out


def to_full_html_document(html_template_chunk: str) -> str:
    """
    Convert a HTML chunk into a full, valid html document.
    """
    result = ""
    result += "<!DOCTYPE html>\n"
    result += "<html>\n"
    result += "<body>\n"
    result += html_template_chunk + '\n'
    result += "</body>\n"
    result += "</html>\n"

    return result

def to_write_mode(file_in_read_plus_mode):
    """
    Wipe a r+/a file and seek to the beginning as if you just it in write mode.
    Checks for stdout/stderr and does not perform an operation.
    """
    if file_in_read_plus_mode not in [sys.stdout, sys.stderr]:
        file_in_read_plus_mode.seek(0, 0)
        file_in_read_plus_mode.truncate(0)


def main():
    parsed_args: argparse.Namespace = make_parser().parse_args()
    
    # Read all the images.
    images_and_fnames = []
    for image_file in parsed_args.images:
        images_and_fnames.append((Image.open(image_file), image_file.name))
    
    # Now we can perform processes on them.
    html_and_css = {
        filename: rowlist_to_html_css(
            data.PixelAccessPillow(image, background=parsed_args.background_colour).getcontiguousrows(),
            parsed_args.no_css, parsed_args.pixel_size
            ) for (image, filename) in images_and_fnames
    }

    # Combine all the html if we want a coherent document output.
    if parsed_args.combined is not None or parsed_args.seperate is not None:
        # If append-mode not specified, truncate the file(s) and jump to beginning.
        if not parsed_args.append:
            if parsed_args.combined is not None:
                to_write_mode(parsed_args.combined)
            elif parsed_args.seperate is not None:
                for f in parsed_args.seperate:
                    to_write_mode(f)
        html_only_component = '\n'.join(x[1][0] for x in html_and_css.items())
        css_only_component = '\n'.join(x[1][1] for x in html_and_css.items())
        # If combined, glue them together, write, then close. Else, leave them separate, write to each file, then close.
        # If full document, combine regardless.
        if parsed_args.full_document:
            html_only_component = to_full_html_document(combine_html_css(html_only_component, css_only_component))
            css_only_component = ""
        if parsed_args.combined is not None:
            parsed_args.combined.write(combine_html_css(html_only_component, css_only_component))
            parsed_args.combined.close()
        elif parsed_args.seperate is not None:
            parsed_args.seperate[0].write(html_only_component)
            if len(css_only_component.strip()) > 0: 
                parsed_args.seperate[1].write(css_only_component)
            for f in parsed_args.seperate:
                f.close()

    else:  # Now we can generate documents for each picture.
        for basename, html_css_pair in html_and_css.items():
            html_component = html_css_pair[0]
            css_component = html_css_pair[1]
            if parsed_args.full_document:
                html_component = to_full_html_document(combine_html_css(html_component, css_component))
                css_component = ""

            with open(basename + ".html", 'a') as htmlfile:
                if not parsed_args.append:
                    to_write_mode(htmlfile)
                htmlfile.write(html_component)

            if len(css_component.strip()) > 0:
                with open(basename + ".css", 'a') as cssfile:
                    if not parsed_args.append:
                        to_write_mode(cssfile)
                    cssfile.write(css_component)
            


"""
Module for converting images into HTML tables with (or without) CSS. Because why not?
"""
from . import data
from ._typing import *
import string
import random


class _Node:
    def __init__(self, contents: Union[List["_Node"], Any], branch_prefix: str):
        """
        branch_prefix is the prefix to this node on the tree.
        contents is either a list of subnodes or a value.
        Note that branch_prefix is used to update the prefixes of subnodes.
        """
        self._prefix = branch_prefix
        self._contents = contents

    def _sub_prepend_prefix(self, prefix: str):
        """
        Tell all the subnodes to add a prefix onto their current prefix.
        """
        if isinstance(self._contents, list):
            for c in self._contents:
                if isinstance(c, _Node):
                    c.prepend_prefix(prefix)

    def prepend_prefix(self, prefix: str):
        """
        Tell this to prepend a prefix to its prefix, and tell this to tell its children nodes to do the same.
        """
        self._prefix = prefix + self._prefix
        self._sub_prepend_prefix(prefix)

    def get_prefix(self) -> str:
        return self._prefix

    def get_contents_or_subnodes(self) -> Union[List["_Node"], Any]:
        """
        Get either the node's contents or the subnodes associated with it.
        """
        return self._contents


def _encoding(count: Dict[T, int], alphabet: str="01") -> Dict[T, str]:
    """
    Use the Huffman tree algorithm to generate an encoding from a set of counts.
    Duplicate characters in the alphabet are removed.
    """
    # Remove duplicates
    alphabet = "".join(set(a for a in alphabet)) 
    
    # Generate nodes for the actual encoded colours in a tuple with their weight.
    queue = list((_Node(contents=item[0], branch_prefix=""), item[1]) for item in count.items())

    # Extract them so we do not have to search later
    leaf_nodes = list(item[0] for item in queue)

    while len(queue) > 1:
        queue = queue.sort(key=lambda item: item[1], reverse=True)  # End bits have lowest weights.
        # Remove the end parts of the queue so each part can be assigned a letter in the alphabet.
        if len(queue) > len(alphabet):
            # Split 'n pop
            queue, assigning_nodes = queue[:-len(alphabet)], queue[-len(alphabet):]
        else: # make q empty
            queue, assigning_nodes = [], queue
        new_weight = sum(item[1] for item in assigning_nodes)
        
        # Now to give all the assigned nodes prefixes, associated with the provided alphabet:
        for i in range(len(assigning_nodes)):
            assigning_nodes[i][0].prepend_prefix(alphabet[i])

        # Create a new node on the queue with the cumulative weight.
        queue.append((_Node(list(item[0] for item in assigning_nodes), ""), new_weight))
    
    # Go through the initial nodes and combine their contents with prefixes to create a mapping.
    mapping = {}
    for node in leaf_nodes:
        mapping[node.get_contents_or_subnodes()] = node.get_prefix()
    return mapping


def _to_palette(rowlist: List[Union[Tuple[int, data.RGB], data.RowDivider]]) -> Dict[RGB, str]:
    """
    Turn an image specified by rowlist format into a string based palette of colours.
    """
    count = {}
    for item in rowlist:
        if not isinstance(item, data.RowDivider):
            if not item[1] in count.keys():
                count[item[1]]=0
            count[item[1]] += item[0]

    # Huffman tree based mapping over the upper and lowercase characters...
    return _encoding(count, string.ascii_letters)


def rgb_to_html(colour: data.RGB) -> str:
    """
    Convert an RGB triplet into a HTML colour of the form "#ff0054" (or the 3-digit version if it can be shortened)

    Out of range numbers will be clamped.
    """
    colour = tuple(min(max(0, a), 255) for a in colour)
    htmlcolour = "#" + "".join(hex(component)[2:] for component in colour)
    if all(htmlcolour[2*i + 1] == htmlcolour[2*i+2] for i in range(3)):
        htmlcolour = "#" + htmlcolour[1] + htmlcolour[3] + htmlcolour[5]
    return htmlcolour


def rowlist_to_html_css(rowlist: List[Union[Tuple[int, data.RGB], data.RowDivider]], no_css: bool=False, 
        pixel_size: int=3) -> Tuple[str, str]:
    """
    Turn a list of colour rows as specified by data.PixelAccess.getcontiguousrows into a pair of strings which 
    contain html and css code, respectively.

    pixel_size is how many html pixels each image pixel takes up in the x and y axis.

    If no_css is set to True, NO css will be used (probably inflating the size massively), and the border/styling/colour/etc will be 
    directly injected into the HTML with style="...". This will most likely produce a MUCH bigger file. Also, CSS is 
    more compatible when using HTML5.
    """
    # Get a mapping/stringpalette:
    palette = _to_palette(rowlist)

    # Turn the linear rowlist into a 2d set of rows.
    page_rows = []
    for subrow in rowlist:
        currow = []
        # We know rowlists always have data where a RowDivider is at the end.
        if subrow == data.RowDivider():
            page_rows.append(currow)
            currow = []
        else:
            currow.append(subrow)

    html = ""
    css = ""

    # No CSS means Loads'a HTML. Good Luck...
    if no_css:
        html += '<table style="table-layout:fixed;border:0;border-spacing:0;">\n'
        
        for row in page_rows:
            html += '<tr style="line-height:{!s}px;">\n'.format(pixel_size)
            for colour_row in row:
                count, colour = colour_row
                if count <= 1:
                    html += '<td style="background:{};width:{!s}px;"/>\n'.format(rgb_to_html(colour), count*pixel_size)
                else:  # We need colspan
                    html += '<td style="background:{};width:{!s}px;" colspan="{!s}"/>\n'.format(
                            rgb_to_html(colour), 
                            count*pixel_size,
                            count
                    )
                 
            html += '</tr>\n'
        html += '</table>\n'
    else:  # Generate CSS and HTML. Should be fun!
        table_unique_id = "".join([random.choice(string.ascii_letters) for _ in range(16)])

        # First create a table with the random ID, so we can use targeted CSS rather than wrecking a page.
        html += '<table style="table-layout:fixed;border:0;border-spacing:0;" id="{}">\n'.format(table_unique_id)

        # Then we can just make tr's with no style property - height can be managed later in CSS.
        for row in page_rows:
            html += '<tr>\n'
            for count, colour in row:
                # Time to use that mapping we made...
                clazz = palette[colour]
                if count <= 1:
                    html += '<td style="width:{!s}px;" class="{}"/>\n'.format(count*pixel_size, clazz)
                else:
                    html += '<td style="width:{!s}px;" class="{}" colspan="{!s}"/>\n'.format(
                            count*pixel_size,
                            clazz,
                            count
                    )
            html += '</tr>\n'
        html += '</table>\n'

        # Now to generate CSS

        # First, apply the height to all tr children of the table
        css += 'table#{} tr{{line-height:{!s}px;}}\n'.format(table_unique_id, pixel_size)

        # Now we generate CSS for the mappings.
        for colour, cssclass in palette.items():
            css += 'table#{} td.{} {{background:{}; }}\n'.format(table_unique_id, cssclass, rgb_to_html(colour))

    return html, css


if __name__ == "__main__":
    from ._exec import main
    main()

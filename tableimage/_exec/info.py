"""
Contains help and info strings for the command.
"""

no_css_info="""
This option causes the image to be turned into a pure HTML table. There is no css used apart from element styles inline. This will 
create a very large file.

Any css normally generated would not be.
"""


full_document_info="""
This option overrides the normal behaviour of outputting template chunks of css and html that can be inserted into a document, instead 
producing a full, standalone html document (with <style> tags if css is produced) that can be loaded into a web-browser.

This means that any css files normally generated would not be because the CSS would be included in the HTML. So a --seperate argument 
becomes the same as a --combined argument (if present).
"""


output_group_info="""
Options in this group, when used, cause all the images to be glued together vertically in a single document.
"""


combined_output_info="""
This option allows the output of the command to be specified. Providing - as a value causes all output to be put on stdout (with the css 
inside <style> tags)

Providing a value causes all the images to be glued together vertically in a document with <style> tags for css, 
and then placed in the output.
"""

separate_output_info="""
This argument allows output to two seperate documents. The first is the html output, and the second is the css output.

This option is mutually exclusive with the combined output option.
"""

append_info="""
Using this switch causes the output of the command, if it is going to files, to be appended if the file already exists rather 
than overwriting it.
"""

pixel_size_info="""
This argument controls how many html pixels each image pixel is (default: %(default)s).
"""

background_colour_info="""
This argument allows specification of a background colour to blend with images which contain transparency. Arguments outside the 
0-255 range are clamped to that range. The default colour is white (255, 255, 255)
"""

images_info="""
Images to convert into HTML/CSS tables.
"""

program_info="""
This program converts a set of images into HTML tables.
"""

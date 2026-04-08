#!/usr/bin/env python3
#
# Adobe Photoshop "*.act" palette file conversion to GIMP "*.gpl" palette
# format (which is also recognized by many other tools).
#
# How to use:
#   ./act_to_gpl.py some_palette.act > some_palette.gpl
#
# Code based on swatchbook/codecs/adobe_act.py from:
# http://www.selapa.net/swatchbooker/


import os.path
import struct
import sys


def parse_adobe_act(filename):
    filesize = os.path.getsize(filename)
    with open(filename, 'rb') as file:
        if filesize == 772:  # CS2
            file.seek(768, 0)
            nbcolors = struct.unpack('>H', file.read(2))[0]
            file.seek(0, 0)
        else:
            nbcolors = filesize // 3

        # List of (R, G, B) tuples.
        return [struct.unpack('3B', file.read(3)) for i in range(nbcolors)]


def return_gimp_palette(colors, name, columns=16):
    # We use enumerate(colors) to get both the index (i) and the (R, G, B) tuple
    formatted_colors = '\n'.join(
        '{0} {1} {2}\tIndex {3}'.format(color[0], color[1], color[2], i)
        for i, color in enumerate(colors)
    )

    return 'GIMP Palette\nName: {name}\nColumns: {columns}\n#\n{colors}\n'.format(
        name=name,
        columns=columns,
        colors=formatted_colors,
    )


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ./act_to_gpl.py some_palette.act > some_palette.gpl")
        sys.exit(1)

    sys.stdout.write(
        return_gimp_palette(parse_adobe_act(sys.argv[1]), sys.argv[1])
    )

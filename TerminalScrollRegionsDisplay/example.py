#!/usr/bin/env python3
# requires Python 3.6+ 

# pdanford - January 2021
# MIT License

"""
Example use of ScrollRegion to display 3 regions.
"""

import random
from ScrollRegion import ScrollRegion

region_width=40
ansi_green_bg = "\x1b[42m"
ansi_reset = "\x1b[0m"

# create 3 scroll regions
region_list = []
for i in range(1,4):
    # create a highlighted title
    name = f"Region {i}"
    title = f"{ansi_green_bg}{name:^{region_width}}{ansi_reset}"

    # append a pair made up of a created region coupled with a counter
    region_list.append( [ScrollRegion(title), 1] )

try:
    # add a bunch of lines to the 3 regions
    for i in range(10000):
        # select a random region to add a line to (by weight so speeds vary)
        region = random.choices(region_list, weights=(0.30,0.10,0.60))[0]
 
        # increment this region's line count
        region_line_count = region[1]
        region[1] = region[1] + 1
 
        # add actual line to selected region
        line = f"{region_line_count:-^{region_width}}"
        region[0].AddLine(line)

except KeyboardInterrupt:
    # Suppress python error when <ctrl><c> is used to exit
    pass

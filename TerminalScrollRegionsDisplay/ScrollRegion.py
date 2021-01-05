from time import sleep
from shutil import get_terminal_size
from collections import deque

# version 1.0.0
# requires Python 3.6+ 
# pdanford - January 2021
# MIT License

class ScrollRegion:
    """
    Establish and print lines in a terminal scroll region.
    Each region location is based on the number of rows in the region and 
    how many regions have already been created.

    Note: requires VT100 escape compatibility
    """

    # where scroll region is located in terminal window (1st instance)
    __scroll_region_start_row = 1
    __scroll_region_end_row = 2

    # keeps track of the last row printed to this scroll region
    __last_printed_row = 0

    # storage for scroll region title line 
    # note this should only be updated through SetTitle() because it modifies
    # the scroll region start location
    __title = ""

    # used to detect terminal window size changes
    __prev_terminal_columns, __prev_terminal_rows = get_terminal_size()

    # small cache for the lines added to the region
    __line_cache = deque()
 
    # a list of all ScrollRegion instances
    __scroll_regions_list = []

    # class global flag at that some scroll region(s) didn't have enough room
    # on terminal screen
    __more_below_message = " "

    def __init__(self,
                 title = "",
                 scroll_region_height = 8):
        """
        scroll_region_height - total height of region (including any title line)
        """
        if scroll_region_height < 1:
            raise ValueError("ScrollRegion: scroll_region_height must be >= 1")
            # technically, VT100 compatibility requires at a scroll height of
            # at least 2 lines, but modern terminal emulators seem to be fine
            # with 1 (which might be useful to some)

        # instance member initializations
        self.__line_cache = deque() 
        self.__scroll_region_height = scroll_region_height
        self.__scroll_region_start_row = ScrollRegion.__scroll_region_start_row
        self.__scroll_region_end_row   = (self.__scroll_region_start_row
                                        + scroll_region_height
                                        - 1)
        self.__last_printed_row = self.__scroll_region_end_row

        # update class global for next new ScrollRegion instantiated
        ScrollRegion.__scroll_region_start_row = self.__scroll_region_end_row + 1

        # prep terminal window on first use for clean display of ScrollRegion(s)
        if len(ScrollRegion.__scroll_regions_list) == 0:
            # clear terminal window scroll-back buffer, otherwise it will
            # interfere with display when terminal window is resized or
            # scrolled back:
            print("\x1bc", end="")   # clear screen
            print("\x1b[3J", end="") # erase scroll-back buffer (Linux)

        ScrollRegion.__scroll_regions_list.append(self)

        self.ClearScrollRegion("-")

        self.SetTitle(title)


    def __del__(self):
        # print done/exit message (once using __scroll_region_start_row to
        # detect when the oldest ScrollRegion is garbage collected)
        if self.__scroll_region_start_row <= 2:
            print(f"\x1b[r", end="")         # reset term to default scrolling region
            columns, rows = get_terminal_size()
            print(f"\x1b[{rows};1H", end="") # position cursor to window bottom
            print("\n-- done --")


    def SetTitle(self, title):
        """
        Sets scroll region title and adjusts start/end rows and prints based on
        whether a title exists or not. If "", then, scroll regions will butt up
        against each other. So use a " " if no title is wanted but still a line
        between regions is desired.
        """
        if self.__title == "":
            if title != "":
                # don't include title in scrolling region
                self.__scroll_region_start_row += 1
        else:
            if title == "":
                # reclaim row previously used for title in scrolling region
                self.__scroll_region_start_row -= 1

        self.__title = title

        # print title for this scrolling region
        if self.__title != "":
            # make sure that this scroll region start is actually on screen
            # and print title at top of scroll region if so
            title_row = self.__scroll_region_start_row - 1
            terminal_columns, terminal_rows = get_terminal_size()
            if (title_row <= terminal_rows and
               title_row > 0):
                print(f"\x1b[{title_row};1H", end="")
                print(self.__title, end="")
                print("\x1b[K", end="") # clear rest of line


    def AddLine(self, line, scroll_delay = 0.125):
        """
        Add line string to this scroll region.

        scroll_delay - scroll delay each line print for readability
        """
        # Add this line to the cache in case its needed for a refresh trigger
        self.__line_cache.append(line)

        if len(self.__line_cache) > self.__scroll_region_height:
            # keep __line_cache length the same as the scroll region height
            self.__line_cache.popleft()

        # Print newly added line to this scroll region according 3 cases:
        trigger = self.__CheckScreenRefreshTrigger()
        if trigger == "REPRINT_ALL_SCROLL_REGIONS":
            # 1. entire terminal window needs updating
            print("\x1b[3J", end="") # erase scroll-back buffer (Linux)

            # clear any previous class global flag that there was not
            # enough room to print region
            ScrollRegion.__more_below_message = " "

            # reprint all regions' cache
            for r in reversed(ScrollRegion.__scroll_regions_list):
                r.__ReprintScrollRegion()
        elif trigger == "REPRINT_SCROLL_REGION":
            # 2. this whole scroll region (only) needs updating
            print("\x1b[3J", end="") # erase scroll-back buffer (Linux)

            # clear any previous class global flag that there was not
            # enough room to print region
            ScrollRegion.__more_below_message = " "

            self.__ReprintScrollRegion()
        else:
            # 3. print/add this single line (only) at this scroll region end
            self.__Print(line, scroll_delay)


    def ClearScrollRegion(self, blanking_string = ""):
        """
        Blanks the entire scroll region and line cache (including title
        area) with blanking_string.
        """
        # remove any title so entire scroll region is cleared
        self.SetTitle("")

        for i in range(self.__scroll_region_height):
            self.AddLine(blanking_string, 0)


    def __Print(self, line, scroll_delay):
        """
        Internal function to print line string  at the last line of this
        instance's scroll region in the terminal window and scroll up one line.

        scroll_delay - scroll delay each line print for readability
        """
        # make sure that this scroll region start is actually on screen
        terminal_columns, terminal_rows = get_terminal_size()

        # don't print line if none of scroll region is within terminal window
        if self.__scroll_region_start_row > terminal_rows:            
            self.__last_printed_row = 0
            # set class global flag there was not enough room to print region
            ScrollRegion.__more_below_message = "\x1b[0;43m↓\x1b[0m"
            return

        # ensure area where line data is to be printed is in terminal window
        if self.__scroll_region_end_row <= terminal_rows:
            self.__last_printed_row = self.__scroll_region_end_row
        else:
            # limit if there's not enough room (scroll region is truncated)
            self.__last_printed_row = terminal_rows
            # set class global flag there was not enough room to print region
            ScrollRegion.__more_below_message = "\x1b[0;43m↓\x1b[0m"

        # set scrolling region for this ScrollRegion instance
        print(f"\x1b[{self.__scroll_region_start_row};{self.__last_printed_row}r", end="")
        # position to end of scroll region before printing line data
        print(f"\x1b[{self.__last_printed_row};1H", end="")

        # prepend a newline to cause previous line to scroll up
        print(f"\n{ScrollRegion.__more_below_message}{line}", end="")

        # scroll delay each line for readability
        sleep(scroll_delay)


    def __ReprintScrollRegion(self):
        """
        Internal function used to cause a reprint of this ScrollRegion
        instance's entire line cache and title (if any).
        """
        # reprint title (if any)
        self.SetTitle(self.__title)

        # reprint entire line cache to refresh whole scroll region
        for line in self.__line_cache:
            self.__Print(line, 0)


    def __CheckScreenRefreshTrigger(self):
        """
        Internal function to check if a window resize event happened that
        results in the currently displayed scroll regions being corrupted.
        Some resizes change where the scroll regions are displayed on the
        new window coordinates which don't match previously displayed scroll
        region location because of scroll back. 

        Return flag strings:
        REPRINT_ALL_SCROLL_REGIONS - window height has changed in such a way
                                     that its scroll back buffer should be
                                     cleared and all scroll regions should be
                                     reprinted entirely to fix coordinates
        REPRINT_SCROLL_REGION - window height has increased over this scroll
                                region by 1 or more lines since last print
                                which means (only) this scroll region should
                                be reprinted entirely to fill in the gap rows
                                (also true for a region that was previously
                                entirely off screen)
        """
        # note previous terminal window dimensions
        prev_terminal_rows = ScrollRegion.__prev_terminal_rows
        # get current terminal window dimensions
        terminal_columns, terminal_rows = get_terminal_size()
        # update for next trigger check
        ScrollRegion.__prev_terminal_columns, ScrollRegion.__prev_terminal_rows =\
                                                 terminal_columns, terminal_rows

        if (terminal_rows < prev_terminal_rows and
            terminal_rows < ScrollRegion.__scroll_regions_list[
            len(ScrollRegion.__scroll_regions_list) -1]
            .__scroll_region_end_row):
            # terminal_rows shrank and is less than the last scroll region
            # which causes the terminal's scroll back buffer to activate
            # which causes the scroll region coordinates to change

            # indicate a terminal window reset and reprint of all regions'
            # cache is necessary so scroll region coordinates are correct for
            # this new terminal window size
            return "REPRINT_ALL_SCROLL_REGIONS"
        elif (self.__last_printed_row < self.__scroll_region_end_row and
              terminal_rows >= self.__scroll_region_start_row and
              terminal_rows > self.__last_printed_row):
            # the last time this scroll region was printed, it was within the
            # terminal window but didn't have enough room for the entire
            # region (i.e. it was truncated) or it was entirely off screen

            # but the terminal window height has increased rows since last
            # print, so the whole scroll region should be reprinted
            # to fill the gaps
            return "REPRINT_SCROLL_REGION"
        else:
            # indicate a scroll region reprint trigger did not happen
            return ""



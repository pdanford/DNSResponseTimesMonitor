from time import sleep
from shutil import get_terminal_size
from collections import deque

# version 1.1.3
# requires Python 3.6+ 
# pdanford - January 2021
# MIT License

# ANSI terminal escape sequences
ANSI_yellow_bg = "\x1b[0;43m"
ANSI_color_reset = "\x1b[0m"
ANSI_clear_screen = "\x1bc"
ANSI_clear_rest_of_line = "\x1b[K"
ANSI_erase_scrollback_buffer = "\x1b[3J"

class ScrollRegion:
    """
    Establish and print lines in a terminal scroll region.
    Each region location is based on the number of rows in the region and 
    how many regions have already been created.

    Note: requires VT100 escape compatibility
    """

    ## ----- class values -----

    # where 1st instance scroll region is located in terminal window
    __scroll_region_start_row = 1

    # used to detect terminal window size changes
    __prev_terminal_columns, __prev_terminal_rows = get_terminal_size()

    # a list of all ScrollRegion instances
    __scroll_regions_list = []

    # Class global flags to indicate a scroll region didn't have enough room
    # for all its rows to print for the current terminal window height
    __more_below_flag = False
    __prev_more_below_flag = False

    # message to display at bottom of terminal window when window height isn't
    # enough for all scroll region(s) rows
    __more_below_message =\
      f"{ANSI_yellow_bg} ↓↓ more below ↓↓ {ANSI_color_reset}{ANSI_clear_rest_of_line}"

    ## ----- instance variables -----

    # storage for scroll region title line 
    # note this should only be updated after creation through SetTitle()
    # because it modifies the scroll region start location
    # (takes up 1 row of scroll_region_height)
    __title = ""

    # storage for last row number of terminal scroll region
    __scroll_region_end_row = 0

    # small cache for the lines added to the region
    __line_cache = deque()


    def __init__(self,
                 title = "",
                 scroll_region_height = 8):
        """
                       title - if not "", takes up 1 row of scroll_region_height
        scroll_region_height - total height of region (including any title line)
        """
        if scroll_region_height < 2 and title != "":
            raise ValueError\
              ("ScrollRegion: with title, scroll_region_height must be >= 2")
            # technically, VT100 compatibility requires at a scroll height of
            # at least 2 lines, but modern terminal emulators seem to be fine
            # with 1 (which might be useful to some)
        elif scroll_region_height < 1:
            raise ValueError\
              ("ScrollRegion: without title, scroll_region_height must be >= 1")
            # technically, VT100 compatibility requires at a scroll height of
            # at least 2 lines, but modern terminal emulators seem to be fine
            # with 1 (which might be useful to some)

        # instance member initializations
        self.__scroll_region_height = scroll_region_height
        self.__scroll_region_start_row = ScrollRegion.__scroll_region_start_row
        self.__scroll_region_end_row   = (self.__scroll_region_start_row
                                          + scroll_region_height
                                          - 1)
        self.__line_cache = deque()

        # update class global for next new ScrollRegion instantiated
        ScrollRegion.__scroll_region_start_row = self.__scroll_region_end_row + 1

        # prep terminal window on first use for clean display of ScrollRegion(s)
        if len(ScrollRegion.__scroll_regions_list) == 0:
            # clear terminal window and scroll-back buffer, otherwise it will
            # interfere with display when terminal window is resized or
            # scrolled back:
            print(f"{ANSI_clear_screen}", end="")
            print(f"{ANSI_erase_scrollback_buffer}", end="")

        ScrollRegion.__scroll_regions_list.append(self)

        self.ClearScrollRegion("-")

        self.SetTitle(title)


    def __del__(self):
        # print done/exit message (once using __scroll_region_start_row to
        # detect when the oldest ScrollRegion is garbage collected)
        if self.__scroll_region_start_row <= 2:
            # reset term to default scrolling region
            ANSI_set_scroll_region ="\x1b[r"
            print(f"{ANSI_set_scroll_region}", end="")

            # position cursor to window bottom
            columns, rows = get_terminal_size()
            ANSI_postion_to_row = f"\x1b[{rows};1H"
            print(f"{ANSI_postion_to_row}", end="")
            print("\n-- done --")


    def ClearScrollRegion(self, blanking_string = ""):
        """
        Clears the entire scroll region and line cache (including title
        area) with blanking_string.
        """
        # remove any title so entire scroll region is cleared
        self.SetTitle("")

        # flush line cache with blanking_string
        self.__line_cache.clear()
        for i in range(self.__scroll_region_height):
            self.__line_cache.append(blanking_string)
            self.__Print(blanking_string, 0)

        # clear class global "more below" flag (to be reset during next
        # __Print() if needed
        ScrollRegion.__more_below_flag = False

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
                # position to title row
                ANSI_postion_to_row = f"\x1b[{title_row};1H"
                print(f"{ANSI_postion_to_row}", end="")
                # print title
                print(f"{self.__title}", end="")
                print(f"{ANSI_clear_rest_of_line}\r", end="")

                ## ---------------------------------

                if ScrollRegion.__more_below_flag:
                    # display "more below" message at last row of terminal window
                    terminal_columns, terminal_rows = get_terminal_size()
                    ANSI_postion_to_row = f"\x1b[{terminal_rows};1H"
                    print(f"{ANSI_postion_to_row}{ScrollRegion.__more_below_message}", end="")


    def AddLine(self, line, scroll_delay_s = 0.125):
        """
        Add line string to this scroll region.

        scroll_delay_s - scroll delay each line print for readability
        """
        # Add this line to the cache
        # (in case it's needed for a refresh trigger later)
        self.__line_cache.append(line)

        if len(self.__line_cache) > self.__scroll_region_height:
            # keep __line_cache length the same as the scroll region height
            self.__line_cache.popleft()

        # Print newly added line to this scroll region end row
        self.__Print(line, scroll_delay_s)

        reprint_trigger = self.__CheckScreenRefreshTrigger()
        if reprint_trigger == "REPRINT_ALL_SCROLL_REGIONS":
            # clear class global "more below" flag (to be reset during next
            # __Print() if needed
            ScrollRegion.__more_below_flag = False

            # erase terminal's scrollback buffer
            print(f"{ANSI_erase_scrollback_buffer}", end="")

            # reprint all regions' cache
            # (do in reverse so __more_below_flag is updated for higher
            # regions that it may encroach on) 
            for r in reversed(ScrollRegion.__scroll_regions_list):
                r.__ReprintScrollRegion()

            ## ---------------------------------

            if ScrollRegion.__more_below_flag:
                # display "more below" message at last row of terminal window
                terminal_columns, terminal_rows = get_terminal_size()
                ANSI_postion_to_row = f"\x1b[{terminal_rows};1H"
                print(f"{ANSI_postion_to_row}{ScrollRegion.__more_below_message}", end="")


    def __Print(self, line, scroll_delay_s):
        """
        Internal function to print line string  at the last line of this
        instance's scroll region in the terminal window and scroll up one line.

                  line - string to print at bottom of this scroll region
        scroll_delay_s - scroll delay each line print for readability
        """
        # make sure that this scroll region start is actually on screen
        terminal_columns, terminal_rows = get_terminal_size()

        if ScrollRegion.__more_below_flag:
            # since this or some other ScrollRegion flagged it was truncated,
            # leave room to for "more below" message at bottom of window when
            # line data is printed below (matters when this region is at the
            # bottom of the terminal window)
            terminal_rows = terminal_rows - 1 # leave 1 row for "more below"
                                              # message

        # don't print line if none of scroll region is within terminal window
        if self.__scroll_region_start_row > terminal_rows:
            # there was no room to print any of this region's rows
            ScrollRegion.__more_below_flag = True
            return

        # ensure area where line data is to be printed is in terminal window
        if self.__scroll_region_end_row > terminal_rows:
            # limit if there's only enough room for partial scroll region
            # (scroll region is truncated) but enough to print line
            print_row_num = terminal_rows
            ScrollRegion.__more_below_flag = True
        else:
            print_row_num = self.__scroll_region_end_row

        # set scrolling region for this ScrollRegion instance
        ANSI_set_scroll_region = f"\x1b[{self.__scroll_region_start_row};{print_row_num}r"
        print(f"{ANSI_set_scroll_region}", end="")
        # position to end of scroll region before printing line data
        ANSI_postion_to_row = f"\x1b[{print_row_num};1H"
        print(f"{ANSI_postion_to_row}", end="")

        if print_row_num - self.__scroll_region_start_row >= 1:
            # prepend a newline to cause previous lines to scroll up in region
            print(f"\n{line}\r", end="")

            # ** fix for macOS terminal edge case **
            if (self.__title == "" and
                self.__scroll_region_start_row == 1):
                # when the first scroll region doesn't have a title, macOS's
                # terminal will still fill the scroll-back buffer, so this
                # keeps it clear to avoid confusion if the window scroll-bar
                # is accidentally used - iterm2 doesn't have this issue
                print(f"{ANSI_erase_scrollback_buffer}", end="")
        else:
            # don't do the prepend \n for scroll regions of 1 row because some
            # terminals will scroll any title line too in certain edge cases
            print(f"{line}{ANSI_clear_rest_of_line}\r", end="")

        # scroll delay each line for readability
        sleep(scroll_delay_s)

        return


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
        Some resize changes result in the scroll regions being displayed on
        new window coordinates which don't match previously displayed scroll
        region location because of scroll-back.

        If so, indicate a terminal window buffer reset and reprint of all
        regions' cache is necessary so scroll region coordinates are correct
        for this new terminal window size

        return flag strings:
                        empty string - no reprint necessary
          REPRINT_ALL_SCROLL_REGIONS - window height has changed in such a way
                                       that its scroll-back buffer should be
                                       cleared and all scroll regions should be
                                       reprinted entirely to fix coordinates
        """
        # get current terminal window dimensions
        terminal_columns, terminal_rows = get_terminal_size()

        # assume a scroll region reprint trigger did not happen
        return_flag = ""

        if terminal_rows != ScrollRegion.__prev_terminal_rows:
            # terminal_rows changed which may cause the terminal's scroll-back
            # buffer to activate which causes the scroll region coordinates to
            # change
            return_flag = "REPRINT_ALL_SCROLL_REGIONS"
        elif terminal_columns != ScrollRegion.__prev_terminal_columns:
            # terminal_columns changed which may cause the terminal's
            # scroll-back buffer to activate because of line wrapping
            # which causes the scroll region coordinates to change
            return_flag = "REPRINT_ALL_SCROLL_REGIONS"
        elif (ScrollRegion.__more_below_flag == True and
              ScrollRegion.__prev_more_below_flag == False):
            # this case is for when a region is instantiated and is partially 
            # truncated at terminal window bottom or entirely after end of
            # terminal window bottom
            #
            # visible ones may need to redraw too accommodate the "more below"
            # message (and the "more below" message needs to be displayed)
            return_flag = "REPRINT_ALL_SCROLL_REGIONS"

        # update for next trigger check
        ScrollRegion.__prev_more_below_flag = ScrollRegion.__more_below_flag

        ScrollRegion.__prev_terminal_columns,\
        ScrollRegion.__prev_terminal_rows =\
          terminal_columns, terminal_rows

        return return_flag


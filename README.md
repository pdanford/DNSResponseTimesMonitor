
DNS Response Times Monitor
--------------------------------------------------------------------------------
This script parses output in real-time from tcpdump (as a continuous stream or as a set amount by adding `-c` to the tcpdump arguments) to show individual DNS request response times in milliseconds grouped by DNS server and IP version (with server stats).

##### Usage
```
(tcpdump DNS capture output) | DNS_times_parser.py [--print_requester]
```
Including `--print_requester` on the command line causes requester's address to be appended to Request Datum Row output.

##### Example use (continuous stream):
```
ssh r7800 'tcpdump -K -l -i eth0.2 udp port 53 2>/dev/null' | ./DNS_times_parser.py
```

In this example, the interface used in tcpdump is the WAN interface of a Netgear router so dnsmasq cache lookups and any adblock DNS black-holing is bypassed.

##### Test with:
```
cat assets/tcpdump_test.out | ./DNS_times_parser.py
```

### Output
Output is done using terminal scroll regions provided by TerminalScrollRegionsDisplay - one for each DNS server. Terminal scroll regions are lightweight and cannot be scrolled back to show history. Thus, the main purpose of these regions is to give a feel for what's being looked up in real-time, not provide a log of DNS requests.

Example output:

![](assets/example.gif)

##### Output Columns for each DNS server scroll region
###### Title Row
| DNS Server | IP Version | Total Requests on this Server | Simple Moving Average of Request Durations (ms) |
|:----------:|:----------:|:-----------------------------:|:-----------------------------------------------:|

The SMA has a period of 10 (the number of individual DNS request rows in a region). The fastest DNS server will have its SMA highlighted in green. Servers that are between 35% and 100% slower will be highlighted in yellow. Greater than 100% slower will be highlighted in red.

###### Request Datum Rows
| Request Duration ms (and time of response) | DNS Request Type | Address Looked Up | [Requester Address] |
|:------------------------------------------:|:----------------:|:-----------------:|:-------------------:|

`NoRecord` and `NXDomain` are appended to Request Datum Rows that didn't have a successful lookup.

### Regarding Terminal Window Size and Scroll Regions
Terminal scroll regions are supplied by TerminalScrollRegionsDisplay. From its readme:

> This is a python 3.6+ class to present output on a terminal window in the form of one or more scroll regions using the ANSI escape control sequences supported by the terminal emulator. This means the scroll regions are very light weight (e.g. cannot be scrolled back to see history that has been scrolled off).

and

> Each new instance will establish and print lines in a terminal scroll region whose position starts immediately after any previously instantiated scroll regions. That is, each region location is based on the number of rows in the region and how many regions have already been created.
>
>In the case of multiple scroll regions, the number of regions is limited by the height of the terminal window (i.e. the window cannot be scrolled up and down to see scroll regions off-screen. As an example work around on macOS, <kbd>command</kbd>+<kbd>-</kbd> can be used to shrink the terminal window and fonts so more scroll regions will fit on-screen.

and

>If the terminal window height is not enough to display a complete scroll region for all scroll region instances, a highlighted "↓↓ more below ↓↓" message will appear at the last row of the terminal window which means more scroll region rows are hidden below.
>
>Note that when terminal window height is increased, any more below state is updated during the next AddLine() call (since there is no terminal window size change callback).

### Requirements
- Python 3.6+ 
- TerminalScrollRegionsDisplay

### Notes
- 1st parser version by Tom D. Aug 2020
- revised by pdanford - Oct 2020
- terminal window scroll regions added by pdanford - Jan 2021

---
:scroll: [MIT License](README.license)

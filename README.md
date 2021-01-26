DNS Response Times Monitor
--------------------------------------------------------------------------------
This script parses output from tcpdump (as a continuous stream or as a set amount by adding `-c` to the tcpdump arguments) to show DNS response times in milliseconds for each DNS request grouped by DNS server and IP version.

##### Example use (continuous stream):
```
ssh r7800 'tcpdump -K -U -i eth0.2 udp port 53 2>/dev/null' | ./DNS_times_parser.py
```

In this example, the interface used in tcpdump is the WAN interface of a Netgear router so dnsmasq cache lookups and any adblock DNS black-holing is bypassed.

##### Test with:
```
cat assets/tcpdump_test.out | ./DNS_times_parser.py
```

##### Output
Output is done using terminal scroll regions provided by TerminalScrollRegionsDisplay - one for each DNS server:

![](assets/example.png)

### Regarding Terminal Window Size and Scroll Regions
Terminal scroll regions are supplied by TerminalScrollRegionsDisplay. From its readme:

> Each new instance will establish and print lines in a terminal scroll region whose position starts immediately after any previously instantiated scroll regions. That is, each region location is based on the number of rows in the region and how many regions have already been created.
>
>In the case of multiple scroll regions, the number of regions is limited by the height of the terminal window (i.e. the window cannot be scrolled up and down to see scroll regions off-screen. As an example work around on macOS, <kbd>command</kbd>+<kbd>-</kbd> can be used to shrink the terminal window and fonts so more scroll regions will fit on-screen.

and

>If the terminal window height is not enough to display a complete scroll region for all scroll region instances, a highlighted "↓↓ more below ↓↓" message will appear at the last row of the terminal window which means more scroll region rows are hidden below.
>
>Note that when terminal window height is increased, any more below state is updated during the next AddLine() call (since there is no terminal window size change callback).

##### Output Columns for each DNS server scroll region:
###### Title Row
| DNS Host | IP Version | Total Requests | Request Duration Average (ms) |
|:--------:|:----------:|:--------------:|:-----------------------------:|

###### Request Datum Rows
| Individual Request Duration (ms) | DNS Request type | Address Looked Up |
|:--------------------------------:|:----------------:|:-----------------:|

### Requirements
- Python 3.6+ 
- TerminalScrollRegionsDisplay

### Notes
- 1st parser version by Tom D. Aug 2020
- revised by pdanford - Oct 2020
- terminal window scroll regions added by pdanford - Jan 2021

---
:scroll: [MIT License](README.license)

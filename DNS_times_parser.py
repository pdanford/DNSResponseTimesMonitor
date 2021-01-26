#!/usr/bin/env python3
# requires Python 3.6+ 

import sys
import datetime
import itertools
from collections import namedtuple
from TerminalScrollRegionsDisplay.ScrollRegion import ScrollRegion

ANSI_cyan_bg = "\x1b[46m"
ANSI_color_reset = "\x1b[0m"

def time2float(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def parse_gen(f):
    """
    Parses tcpdump lines supplied by f into a DNS_packet named tuple
    """
    for line in f:
        parts = line.strip().split(" ")
        if len(parts) > 5:
            time, reqid = parts[0], parts[5]

            t = datetime.datetime.strptime(time, '%H:%M:%S.%f').time()

            is_req = reqid.endswith('+')
            if is_req:
                reqid = reqid[:-1]

            dst_address = parts[4][:-1] # strip trailing ':' tcpdump adds

            DNS_packet = namedtuple('DNS_packet_type',['t',
                                                       'reqid',
                                                       'is_req',
                                                       'proto',
                                                       'src_address',
                                                       'dst_address',
                                                       'query_address',
                                                       'type'])

            # yield makes this a generator function so this will produce results
            # as long as the piped tcpdump output supplies DNS lookup packets
            yield DNS_packet(t,
                             reqid,
                             is_req,
                             parts[1],
                             parts[2],
                             dst_address,
                             parts[7],
                             parts[6])


def process(packets_gen):
    """
    processes the packet generator stream packets_gen from tcpdump produced by
    parse_gen
    """
    scroll_regions = {}
    scroll_regions_stats = {}
    request_cache = {}
    for p in packets_gen:
        if p.is_req:
            # ** new DNS request **
            # make note of new DNS request
            request_cache[p.dst_address+'-'+p.proto+'-'+p.reqid] =\
                                      (time2float(p.t), p.query_address, p.type)
        elif p.src_address+'-'+p.proto+'-'+p.reqid in request_cache:
            #   ^^^^^ note address swap in key so responses match key
            #         made with original request's dst_address
            # ** DNS response **
            # calculate time this request took
            request = request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]
            del request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]

            # add DNS response data to its scroll region for display
            # the [:-3] trims the port number
            scroll_region_name = f"{p.src_address[:-3]+' ('+p.proto+')'}"

            if scroll_region_name not in scroll_regions:
                # create scroll region for this new DNS server
                scroll_regions[scroll_region_name] =\
                                                ScrollRegion(scroll_region_name)
                scroll_regions_stats[scroll_region_name] = {}
                scroll_regions_stats[scroll_region_name]["total_requests"] = 0
                scroll_regions_stats[scroll_region_name]["accumulated_time_ms"] = 0

            # add this DNS request/response datum to its ScrollRegion instance
            # for display
            dt_s = time2float(p.t) - request[0]
            # datum columns:
            # | lookup time delta (ms) | DNS request type | address looked up |
            line = f" {dt_s*1000:>7.3f}ms {request[2]:^8} {request[1]}"
            scroll_regions[scroll_region_name].AddLine(line)

            # update stats for this scroll regions
            scroll_regions_stats[scroll_region_name]["total_requests"] += 1
            scroll_regions_stats[scroll_region_name]["accumulated_time_ms"] += dt_s*1000

            # update the scroll region title with these stats
            total_requests = scroll_regions_stats[scroll_region_name]["total_requests"]
            ave_ms = (scroll_regions_stats[scroll_region_name]["accumulated_time_ms"] /
                      scroll_regions_stats[scroll_region_name]["total_requests"])

            left =   f"{scroll_region_name}"
            right1 = f"{'reqs:' + str(total_requests)} "
            right2 = f"{'ave:' + f'{ave_ms:>.0f}' + 'ms  '}"

            title =  f"{ANSI_cyan_bg}  {left:<40} {right1 + right2:>20}{ANSI_color_reset}"
            scroll_regions[scroll_region_name].SetTitle(title)
        else:
            # ** DNS response without a matching request in request_cache **
            # ignore this response - no matching request in request_cache
            pass


def main():
    print("\n-- waiting for tcpdump DNS packets stream --")
    # get tcpdump output stream from stdin
    process(parse_gen(sys.stdin))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Suppress python exception when <ctrl><c> is used to exit
        pass
    except ValueError as e:
        # catch errors thrown by ScrollRegion
        print("\n>>>> ", e, "\n")

        ## ---------------------------------------------------------------------
        # send pseudo <ctrl><c> (i.e. SIGINT) to shut down the indefinite STDIN
        # pipe feeding main() since some programs upstream of the pipe may be
        # ignoring SIGPIPE (e.g. macOS's ssh client)
        try:
            import os
            import signal
            pgid = os.getpgid(os.getpid())
            if pgid == 1:
                os.kill(os.getpid(), signal.SIGINT)
            else:
                os.killpg(os.getpgid(os.getpid()), signal.SIGINT) 
        except ImportError:
            pass
        except KeyboardInterrupt:
            # ignore python exception when pseudo SIGINT <ctrl><c> is sent above
            pass
        ## ---------------------------------------------------------------------

    sys.exit(0)


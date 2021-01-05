#!/usr/bin/env python3
# requires Python 3.6+ 

import sys
import datetime
import itertools
from collections import namedtuple
from TerminalScrollRegionsDisplay.ScrollRegion import ScrollRegion


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
    ave_response_time = []
    scroll_regions = {}
    request_cache = {}
    for p in packets_gen:
        if p.is_req:
            # make note of new DNS request time
            request_cache[p.dst_address+'-'+p.proto+'-'+p.reqid] =\
                                      (time2float(p.t), p.query_address, p.type)
        elif p.src_address+'-'+p.proto+'-'+p.reqid in request_cache:
            #   ^^^^^ note address swap in key so responses match key
            #         made with original request's dst_address

            # calculate time this request took
            request = request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]
            del request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]

            # add DNS response data to its scroll region for display
            # scroll_region_name = f"{p.src_address[:-3]+'-'+p.proto:^40}"
            scroll_region_name =\
                     f"\x1b[46m{p.src_address[:-3]+' ('+p.proto+')':^65}\x1b[0m"

            if scroll_region_name not in scroll_regions:
                # create region for this new DNS server
                scroll_regions[scroll_region_name] =\
                                                ScrollRegion(scroll_region_name)

            # add this DNS request/response datum to its ScrollRegion
            # instance for display - columns:
            # | lookup time delta (ms) | DNS request type | address looked up |
            dt_s = time2float(p.t) - request[0]
            scroll_regions[scroll_region_name].AddLine(\
                                       f"{dt_s*1000:<7.3f}{request[2]:^8}{request[1]}")
        else:
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
        # Suppress python error when <ctrl><c> is used to exit
        pass
    except ValueError as e:
        # catch errors thrown by ScrollRegion
        print("\n>>>> ", e, "\n")

    sys.exit(0)


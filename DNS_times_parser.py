#!/usr/bin/env python3
# requires Python 3.6+ 

import sys
import datetime
import itertools
from collections import namedtuple
from SimpleMovingAverage.SMA import SMA
from TerminalScrollRegionsDisplay.ScrollRegion import ScrollRegion

# size of each scroll region in rows
scroll_region_size = 11

ANSI_cyan_bg = "\x1b[46m"
ANSI_color_reset = "\x1b[0m"

DNS_packet = namedtuple('DNS_packet_type',['t',
                                           'reqid',
                                           'is_req',
                                           'proto',
                                           'src_address',
                                           'dst_address',
                                           'query_address',
                                           'type'])

DNS_Server = namedtuple('scroll_region_type',['scroll_region',
                                              'stats'])


def time2float(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def parse_gen(f):
    """
    parses tcpdump lines supplied by f into a DNS_packet named tuple
    """
    for line in f:
        parts = line.strip().split(" ")
        if len(parts) > 5:
            time, reqid = parts[0], parts[5]

            t = datetime.datetime.strptime(time, '%H:%M:%S.%f').time()

            is_req = reqid.endswith('+')
            if is_req:
                reqid = reqid[:-1]

            # strip port numbers from source and destination addresses
            src_address = parts[2].rsplit(".", 1)[0]
            dst_address = parts[4].rsplit(".", 1)[0]

            # yield makes this a generator function so this will produce results
            # as long as the piped tcpdump output supplies DNS lookup packets
            yield DNS_packet(t,
                             reqid,
                             is_req,
                             parts[1],
                             src_address,
                             dst_address,
                             parts[7],
                             parts[6])


def process(packets_gen):
    """
    processes the packet generator stream packets_gen from tcpdump produced by
    parse_gen
    """
    dns_servers = {}
    request_cache = {}
    for p in packets_gen:
        if p.is_req:
            # ** new DNS request **
            # make note of new DNS request
            request_cache[p.dst_address+'-'+p.proto+'-'+p.reqid] =\
                       (time2float(p.t), p.query_address, p.type, p.src_address)
        elif p.src_address+'-'+p.proto+'-'+p.reqid in request_cache:
            #   ^^^^^ note address swap in key so responses match key
            #         made with original request's dst_address
            # ** DNS response **
            # calculate time this request took
            request = request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]
            del request_cache[p.src_address+'-'+p.proto+'-'+p.reqid]

            # add DNS response data to its scroll region for display
            dns_server_name = f"{p.src_address+' ('+p.proto+')'}"
            # calculate time request took in seconds
            dt_s = time2float(p.t) - request[0]

            if dns_server_name not in dns_servers:
                # create scroll region and statistics dict for this DNS server
                dns_server =\
                   DNS_Server(ScrollRegion(dns_server_name, scroll_region_size),
                             {"total_requests" : 0,
                              "sma_ms": SMA(scroll_region_size - 1)})
                # use the number of rows in the scroll region (less the title
                # row) for the SMA period

                dns_servers[dns_server_name] = dns_server
            else:
                # find previously created scroll region and statistics dict
                dns_server = dns_servers[dns_server_name]

            # add this DNS request/response datum to its ScrollRegion
            # instance for display - request datum columns:
            # | lookup time delta (ms) | DNS request type | address looked up |
            line = f" {dt_s*1000:>7.3f}ms {request[2]:^8} {request[1][:-1]}"
            # (the [:-1] trims the trailing period from the address looked up)
            dns_server.scroll_region.AddLine(line)

            # update this scroll region's stats
            dns_server.stats["total_requests"] += 1
            dns_server.stats["sma_ms"].CalculateNextSMA(dt_s*1000)

            # update the scroll region title with these stats
            name = f" {dns_server_name} "
            reqs = f"reqs:{dns_server.stats['total_requests']} "
            sma  = f"sma({dns_server.stats['sma_ms'].GetPeriod()}):"
            sma += f"{dns_server.stats['sma_ms'].GetCurrentSMA():>.1f}ms "
            title =  f"{ANSI_cyan_bg}"
            title += f"{name:<45}{reqs:>20}{sma:>16}"
            title += f"{ANSI_color_reset}"

            dns_server.scroll_region.SetTitle(title)
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


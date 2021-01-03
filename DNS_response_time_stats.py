#!/usr/bin/env python3


import sys
import datetime
import itertools
from collections import namedtuple


DNS_packet = namedtuple('DNS_packet_type',['t','reqid','is_req'])  


# yield makes this a generator function. Contrast this with a
# generator expression like e.g.
# filtered_gen = (item for item in my_list if item > 3)
def parse_gen(f):
    for line in f:
        parts = line.strip().split(" ")
        if len(parts) > 5:
            time, reqid = parts[0], parts[5]
            t = datetime.datetime.strptime(time, "%H:%M:%S.%f").time()

            is_req = reqid.endswith("+")
            if is_req:
                reqid = reqid[:-1]

            yield DNS_packet(t, reqid, is_req)


def t2f(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def process(packets_gen):
    # 'not' the x.is_req tuple member (the is_req) because that's used as a
    # secondary sort field when the first member of a tuple is the same (and
    # we want is_req True to be the first before the other packets with the
    # same ID - i.e. the responses).
    packets = sorted(packets_gen, key=lambda x: (x.reqid, not x.is_req, x.t))

    # Get an iterator to each ID group in the sorted packets.
    groups = itertools.groupby(packets, lambda x: x.reqid)

    ave_response_time = []
    print(f"{'id':^7}{'t0':^14}{'t1_ave':^14}{'t1_ave-t0':^10}")
    print("---------------------------------------------")
    for id, g in groups:
        items = list(g)

        assert items[0].is_req  # first item must be request
        t0 = t2f(items[0].t)

        response_times = [r.t for r in items if not r.is_req]

        if len(response_times) > 0: # make sure there was a response in sample
            t1 = [t2f(t) for t in response_times]
            t1_ave = sum(t1) / len(t1)
            print(f"{id:<7}{t0:<14.6f}{t1_ave:<14.6f}{t1_ave - t0:<10.6f}")
            ave_response_time.append(t1_ave - t0)

    print(f"\noverall average response time = {sum(ave_response_time) / len(ave_response_time):.6f}\n")


def main():
    print("\n-- waiting for enough tcpdump -c DNS packets --")
    process(parse_gen(sys.stdin))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Suppress python error when <ctrl><c> is used to exit
        pass

    print("-- exit -- ")

    sys.exit(0)


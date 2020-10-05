#!/usr/bin/env python3


import sys
import datetime
import itertools


# yield makes this a generator function. Contrast this with a
# generator expression like e.g.
# filtered_gen = (item for item in my_list if item > 3)
def parse_gen(f):
    # ret = []
    for line in f:
        parts = line.strip().split(" ")
        if len(parts) > 5:
            time, reqid = parts[0], parts[5]
            t = datetime.datetime.strptime(time, "%H:%M:%S.%f").time()

            is_req = reqid.endswith("+")
            if is_req:
                reqid = reqid[:-1]

            yield (t, reqid, is_req) # maybe return named tuple
                                     # instead of [0] [1] [2]
                                     # indexes
            # ret.append((t, reqid, is_req))
    # return ret
    # ^^ can do 'return ret' instead also - and then this would not be a
    # generator.


def t2f(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def process(packets_gen):
    # 'not' the x.is_req tuple member (the is_req) because that's used as a
    # secondary sort field when the first member of a tuple is the same (and
    # we want is_req True to be the first before the other packets with the
    # same ID - i.e. the responses).
    packets = sorted(packets_gen, key=lambda x: (x[1], not x[2], x[0]))

    # Get an iterator to each ID group in the sorted packets.
    groups = itertools.groupby(packets, lambda x: x[1])

    ave_response_time = []
    print(f"{'id':^7}{'t0':^14}{'t1_ave':^14}{'t1_ave-t0':^10}")
    print("---------------------------------------------")
    for id, g in groups:
        items = list(g)

        assert items[0][2]  # first item must be request
        t0 = t2f(items[0][0])

        response_times = [r[0] for r in items if not r[2]]

        if len(response_times) > 0: # make sure there was a response in sample
            t1 = [t2f(t) for t in response_times]
            t1_ave = sum(t1) / len(t1)
            print(f"{id:<7}{t0:<14.6f}{t1_ave:<14.6f}{t1_ave - t0:<10.6f}")
            ave_response_time.append(t1_ave - t0)

    print(f"\naverage response time = {sum(ave_response_time) / len(ave_response_time):.6f}\n")


def main():
    process(parse_gen(sys.stdin))


if __name__ == "__main__":
    main()

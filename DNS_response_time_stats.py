#!/usr/bin/env python3

import sys
import datetime
import itertools


def parse(f):
    # ret = []
    for line in f:
        parts = line.strip().split(" ")
        if len(parts) > 5:
            time, reqid = parts[0], parts[5]
            t = datetime.datetime.strptime(time, "%H:%M:%S.%f").time()
            is_req = reqid.endswith("+")
            if is_req:
                reqid = reqid[:-1]
            # ret.append((t, reqid, is_req))
            yield (t, reqid, is_req)
    # return ret

    # also can use named tuple instead of [0] [1] [2] indexes

def t2f(t):
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6


def process(recs):
    recs = sorted(recs, key=lambda x: (x[1], not x[2], x[0]))
    groups = itertools.groupby(recs, lambda x: x[1])
    for k, g in groups:
        items = list(g)
        assert items[0][2]  # first item must be request
        t0 = t2f(items[0][0])

        restimes = [r[0] for r in items if not r[2]]
        if len(restimes) > 0: # make sure there was a response in sample
            t1 = [t2f(t) for t in restimes]
            t1 = sum(t1) / len(t1)
            print(k, t0, t1, t1 - t0)


def main():
    process(parse(sys.stdin))


if __name__ == "__main__":
    main()

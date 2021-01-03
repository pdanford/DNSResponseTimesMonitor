DNS response statistics parser
------------------------------

This script parses output from a block of tcpdump output lines (the -c tcpdump argument) configured to capture DNS requests and responses to calculate ave DNS response times for each DNS request ID as well as an overall average of the responses.

Note each request ID may be used on multiple DNS servers at the same time. Hence the average column t1_ave-t0.

Example use:

    ssh r7800 'tcpdump -K -c 20 -i eth0.2 udp port 53' | ./DNS_response_time_stats.py

In this case, r7800 is a router and eth0.2 is its WAN NIC.

Test with:

    cat tcpdump.out | ./DNS_response_time_stats.py

Note: 1st version by Tom D. Aug 2020
      revised by Peter D. Oct 2020

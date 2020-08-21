DNS response statistics parser
------------------------------

This script parses output from tcpdump to calculate ave DNS response times for each DNS request ID.

Example use:

    ssh r7800 'tcpdump -K -c 20 -i eth0.2 udp port 53' | ./DNS_response_time_stats.py

Test with:

    cat tcpdump.out | ./DNS_response_time_stats.py

Note: by Tom D. Aug 2020

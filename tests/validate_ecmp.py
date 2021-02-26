#!/usr/bin/python3

import os
import sys
import time
import math

print("Test ECMP")
print("Running iperf")

# running a scripts to send iperf traffic for each host pair (hx->hy for any x and y from 1 to 16)
os.system("sudo bash tests/iperf_send.sh")

fail = False
# check each pod in the fattree
for pod in range(1, 5):
    # s1 and s2 are the id for the two aggregate swicthes in the pod
    s1 = (pod - 1) * 2 + 1
    s2 = (pod - 1) * 2 + 2
    d1 = 0
    d2 = 0
    d3 = 0
    d4 = 0
    # d1, d2, d3, d4 are the number of packets in the 4 links connected from the two aggregated switches to the core switches
    # those 4 numbers should be balanced if the ECMP works
    with open("tcpdump_logs/log{}_1.output".format(s1), "r") as f:
        contents = f.read()
        d1 = len(contents)
    with open("tcpdump_logs/log{}_2.output".format(s1), "r") as f:
        contents = f.read()
        d2 = len(contents)
    with open("tcpdump_logs/log{}_1.output".format(s2), "r") as f:
        contents = f.read()
        d3 = len(contents)
    with open("tcpdump_logs/log{}_2.output".format(s2), "r") as f:
        contents = f.read()
        d4 = len(contents)
    # check whether the 4 numbers are balanced
    # using the deviation
    avg = (d1 + d2 + d3 + d4) / 4.0
    dev = ((d1 - avg) * (d1 - avg) + (d2 - avg) * (d2 - avg) + (d3 - avg) * (d3 - avg) + (d4 - avg) * (d4 - avg)) / 4.0
    dev = math.sqrt(dev)
    dev = dev / avg
    print(dev)
    if abs(dev) > 0.25:
        fail = True

if not fail:
    print("Test pass")
else:
    print("Test fail")
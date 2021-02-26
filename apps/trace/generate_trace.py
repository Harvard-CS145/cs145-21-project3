import numpy as np
import random as rdm
import string
import sys
import argparse

# Global Modes
mode = "mix" # "mix" / "iperf"
flow_size_dist = "uniform" # "uniform" / "long"
flow_size_min = 1000 # ms
flow_size_max = 8000 # ms
flow_gen_mode = "global" # "global" / "perflow"
per_flow_mode = "random" # "random" / "tiled"
num_flows = 16
gap_dist = "poisson" # "poisson" / "uniform" / "persist"
gap_min = 1000 # ms
gap_max = 2000 # ms
mc_hosts_string = "1-16"
iperf_hosts_string = "1-16"
length = 60000
trace_file_name = "test.trace"

memcached_traces = []
iperf_traces = []

memcached_keys = []

def get_random_string(size):
    return ''.join(rdm.choice(string.ascii_letters + string.digits) for x in range(size))

def gen_memcached_trace():
    p = rdm.uniform(0, 1)
    if p <= 0.5 or len(memcached_keys) == 0:
        if p <= 0.25 or len(memcached_keys) == 0:
            key = get_random_string(8)
            memcached_keys.append(key)
            value = rdm.randint(0, 65535)
            return key, value
        else:
            idx = rdm.randint(0, len(memcached_keys) - 1)
            key = memcached_keys[idx]
            value = rdm.randint(0, 65535)
            return key, value
    else:
        idx = rdm.randint(0, len(memcached_keys) - 1)
        key = memcached_keys[idx]
        value = -1
        return key, value

def gen_memcached(host_list, length):
    if len(host_list) == 0:
        return
    next_req = 0
    
    next_req = next_req + np.random.poisson(100)
    while next_req < length:
        host = host_list[rdm.randint(0, len(host_list) - 1)]
        burst = np.random.zipf(1.5)
        if burst > 1000:
            burst = 1000
        for i in range(1000):
            key, value = gen_memcached_trace()
            memcached_traces.append((next_req + i, host, key, value))
        next_req = next_req + np.random.poisson(100)

def gen_iperf(host_list, length):
    if len(host_list) == 0:
        return
    if flow_gen_mode == 'global':
        next_req = 0
        while next_req < length:
            src = host_list[rdm.randint(0, len(host_list) - 1)]
            dst = host_list[rdm.randint(0, len(host_list) - 1)]
            while dst == src:
                dst = host_list[rdm.randint(0, len(host_list) - 1)]
            if flow_size_dist == 'uniform':
                burst = rdm.randint(flow_size_min, flow_size_max)
            else:
                burst = flow_size_max
            iperf_traces.append((next_req, src, "10.0.0.%d" % dst, burst))
            if gap_dist == 'poisson':
                next_req = next_req + np.random.poisson(gap_max)
            elif gap_dist == 'uniform':
                next_req = next_req + rdm.randint(gap_min, gap_max)
            else:
                next_req = next_req + gap_max
    else:
        flows = []
        if per_flow_mode == 'random':
            for i in range(num_flows):
                src = host_list[rdm.randint(0, len(host_list) - 1)]
                dst = host_list[rdm.randint(0, len(host_list) - 1)]
                while dst == src:
                    dst = host_list[rdm.randint(0, len(host_list) - 1)]
                flows.append((src, dst))
        else:
            src_idx = 0
            dst_idx = len(host_list) / 2
            for i in range(num_flows):
                src = host_list[src_idx]
                dst = host_list[dst_idx]
                flows.append((src, dst))
                src_idx += 1
                if src_idx == len(host_list) / 2:
                    src_idx = 0
                dst_idx += 1
                if dst_idx == len(host_list):
                    dst_idx = len(host_list) / 2
        for flow in flows:
            next_req = 0
            while next_req < length:
                if flow_size_dist == 'uniform':
                    burst = rdm.randint(flow_size_min, flow_size_max)
                else:
                    burst = flow_size_max
                iperf_traces.append((next_req, flow[0], "10.0.0.%d" % flow[1], burst))
                if gap_dist == 'poisson':
                    next_req = next_req + np.random.poisson(gap_max)
                elif gap_dist == 'uniform':
                    next_req = next_req + rdm.randint(gap_min, gap_max)
                else:
                    next_req = next_req + gap_max

def parse_hosts(hosts_string):
    host_list = []
    if hosts_string == "0":
        return host_list
    hosts = hosts_string.split(',')
    for host_set in hosts:
        if '-' in host_set:
            hlist = host_set.split('-')
            h_start = int(hlist[0])
            h_end = int(hlist[1])
            for host in range(h_start, h_end + 1):
                host_list.append(host)
        else:
            host_list.append(int(host_set))
    return host_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A trace generator')
    parser.add_argument('--mode', help='Mode', default='mix', choices=['mix', 'iperf'])
    parser.add_argument('--fsdist', help='Flow size distribution', default='uniform', choices=['uniform', 'long'])
    parser.add_argument('--fsmin', help='Minimum flow size (sec)', default="1", type=float)
    parser.add_argument('--fsmax', help='Maximum flow size (sec)', default="8", type=float)
    parser.add_argument('--fgmode', help='Flow generation mode', default="global", choices=['global', 'perflow'])
    parser.add_argument('--pfmode', help='Per-flow mode', default="random", choices=['random', 'tiled'])
    parser.add_argument('--numflow', help='Number of flows in per-flow mode', default="16", type=int)
    parser.add_argument('--gapdist', help='Inter-flow gap distribution', default="poisson", choices=['poisson', 'uniform', 'persist'])
    parser.add_argument('--gapmin', help='Minimum inter-flow gap', default="1", type=float)
    parser.add_argument('--gapmax', help='Maximum inter-flow gap', default="2", type=float)
    parser.add_argument('--mchost', help='Hosts running memcached', default="0")
    parser.add_argument('--iperfhost', help='Hosts running iperf', default="0")
    parser.add_argument('--length', help='Trace length (sec)', default="60", type=float)
    parser.add_argument('--file', help='Trace file name', required=True)
    parser.add_argument('--simple', help='Simple point-to-point sending mode', action='store_const', const=True, default=False)
    args = parser.parse_args()

    mode = args.mode
    flow_size_dist = args.fsdist
    if args.fsmin <= 0 or args.fsmax <= 0:
        print("Flow size must be larger than 0!")
        exit()
    flow_size_min = int(args.fsmin * 1000)
    flow_size_max = int(args.fsmax * 1000)
    flow_gen_mode = args.fgmode
    per_flow_mode = args.pfmode
    if args.numflow <= 0:
        print("Number of flows must be larger than 0!")
        exit()
    num_flows = args.numflow
    gap_dist = args.gapdist
    if args.gapmin < 0 or args.gapmax < 0:
        print("Inter-flow gap must be no less than 0!")
        exit()
    gap_min = int(args.gapmin * 1000)
    gap_max = int(args.gapmax * 1000)
    mc_host_list = parse_hosts(args.mchost)
    iperf_host_list = parse_hosts(args.iperfhost)
    if args.length <= 0:
        print("Trace length must be larger than 0!")
        exit()
    length = int(args.length * 1000)
    out_file = args.file

    if args.simple:
        flow_size_dist = 'long'
        flow_size_max = length
        flow_gen_mode = 'perflow'
        per_flow_mode = 'tiled'
        num_flows = len(iperf_host_list) / 2
        gap_dist = 'persist'
        gap_max = length + 1000
        

    # if len(sys.argv) != 5:
    #     print("usage: python generate_trace.py [hosts running memcached] [hosts running iperf] [trace length (sec)] [trace file name]")
    #     print("\thosts running memcached: the list of hosts running memcached. If you want to run memcached on h1, h2, h3, h5, h7, h8, type 1-3,5,7-8 here. No space allowed.")
    #     print("\thosts running iperf: the format is the same as above.")
    #     print("\ttrace length (sec): how long do you want to generate this trace.")
    #     print("\ttrace file name: the output trace file name.")
    #     exit()

    # mc_hosts_string = sys.argv[1]  
    # iperf_hosts_string = sys.argv[2]     
    # length = int(sys.argv[3]) * 1000

    # mc_host_list = parse_hosts(mc_hosts_string)
    # iperf_host_list = parse_hosts(iperf_hosts_string)

    #if len(mc_host_list) < 2 or len(iperf_host_list) < 2:
    #    exit("Number of hosts must be larger than 1!")

    if mode == "mix":
        gen_memcached(mc_host_list, length)
    gen_iperf(iperf_host_list, length)

    traces = memcached_traces + iperf_traces
    traces.sort()

    f = open(out_file, "w")
    for i in mc_host_list:
        f.write("10.0.0.%d " % i)
    f.write("\n")

    for trace in traces:
        f.write("h%d " % trace[1])
        f.write("%f " % (trace[0] / 1000.0))
        if "." in trace[2]:
            f.write("2 %s %f\n" % (trace[2], trace[3] / 1000.0))
        else:
            if trace[3] == -1:
                f.write("1 %s\n" % trace[2])
            else:
                f.write("0 %s %d\n" % (trace[2], trace[3]))


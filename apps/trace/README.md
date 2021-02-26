# Trace Generator Documentation

## Introduction

The trace generator generates a traffic trace, which describes how to send traffic within the Mininet. The outputed trace file, will be read by the traffic generator, and the traffic generator will send the traffic based on the description of the trace file.

Now the traffic generator supports iperf traffic and memcached traffic. We could extend the traffic type to more in the future.

## Iperf Flow Generation Thread

An iperf flow generation thread is responsible to generate a series of iperf flows. The thread will specify timepoints in the timeline for generate a new flow, and the timepoints are determined by **inter-flow gaps**. For each timepoint to generate a new flow, the new generated flow will be configured with a **flow size**.

## Usage

To see how to use the trace generator, you could use `-h` option to see the arguments

```
usage: generate_trace.py [-h] [--mode {mix,iperf}] [--fsdist {uniform,long}]
                         [--fsmin FSMIN] [--fsmax FSMAX]
                         [--fgmode {global,perflow}] [--pfmode {random,tiled}]
                         [--numflow NUMFLOW]
                         [--gapdist {poisson,uniform,persist}]
                         [--gapmin GAPMIN] [--gapmax GAPMAX] [--mchost MCHOST]
                         [--iperfhost IPERFHOST] [--length LENGTH] --file FILE
                         [--simple]

A trace generator

optional arguments:
  -h, --help            show this help message and exit
  --mode {mix,iperf}    Mode
  --fsdist {uniform,long}
                        Flow size distribution
  --fsmin FSMIN         Minimum flow size (sec)
  --fsmax FSMAX         Maximum flow size (sec)
  --fgmode {global,perflow}
                        Flow generation mode
  --pfmode {random,tiled}
                        Per-flow mode
  --numflow NUMFLOW     Number of flows in per-flow mode
  --gapdist {poisson,uniform,persist}
                        Inter-flow gap distribution
  --gapmin GAPMIN       Minimum inter-flow gap
  --gapmax GAPMAX       Maximum inter-flow gap
  --mchost MCHOST       Hosts running memcached
  --iperfhost IPERFHOST
                        Hosts running iperf
  --length LENGTH       Trace length (sec)
  --file FILE           Trace file name
  --simple              Simple point-to-point sending mode
```

- `mode`. The `mode` option specifies whether to send both iperf and memcached traffic (option `mix`) or send iperf traffic only (option `iperf`). Default is `mix`.
- `fsdist`. This option specifies the flow size distribution for iperf flows. It could be `uniform` distribution (bounded by `fsmin` and `fsmax` options), or `long` flows (all flow has the same size, specified by `fsmax`). Default is `uniform`.
- `fgmode`. This option specifies the iperf flow generation mode. It could be `global` mode (using a single thread to generate iperf flows), or `perflow` mode (specify flows beforehand, and use one thread to generate a certain flow). Default is `global`.
- `pfmode`. This option specifies how to choose iperf flows for per-flow mode. It could be `random` (randomly choose a flow for each flow slot), or `tiled` (if the hosts running iperf are `1-16`, then the flows will be `1->9`, `2->10`, `3->11`, ...). Default is `random`.
- `numflow`. This option specifies the number of flows in the per-flow mode. Default is `16`.
- `gapdist`. This option specifies the inter-flow gap distribution. It could be `poisson` distribution (the mean is determined by `gapmax`), `uniform` distribution (bounded by `gapmin` and `gapmax`), or `persist` (fixed gap determined by `gapmax`). Default is `poisson`.
- `mchost`. This option specifies the hosts running memcached (`1-16` means running on hosts from 1 to 16, `1,5,7,9-11` means running on host 1, 5, 7, 9, 10, and 11). Default is `0` (means no host).
- `iperfhost`. This option specifies the hosts running iperf. Default is `0`.
- `length`. This option specifies the time running the traffic. Default is `60` seconds.
- `file`. This option specifies the output trace file. It is required.
- `simple`. This is a shortcut to generate a simple trace, where you can generate persistent flows.

Normally, everything is by default. You can generate a trace for 60 seconds by

```
python generate_trace.py --file=test.trace --iperfhost=1-16 --mchost=1-16
```

If you want to send iperf trace from host 2 to host 11, from host 7 to host 1, and from host 9 to host 16, for 60 seconds, then you can simply run

```
python generate_trace.py --file=test.trace --simple --iperfhost=2,7,9,11,1,16
```
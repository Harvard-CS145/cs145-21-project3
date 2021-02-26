# Project 3: ECMP and Application Placement

## Objectives

* Implement ECMP and understand its benefits. 
* Understand the benefit of FatTree on application placement. 

**Note:** In this project and following ones, we only focus on the Fattree topology with k=4 (*i.e.,* 16 hosts) and Binary Tree with 16 hosts. 

## Getting Started

This project inherits your Fattree topology and application settings in project 1. Copy `topology/p4app_fat.json` from your project 1 directory to this directory.

In project 1, we distributed traffic across two separated core switches for different application (`controller_fat_twocore.py`). But this is not efficient enough. For instance, if one application stops working, then its corresponding core switch is wasted. 
Thus, we need a more advanced routing strategy -- ECMP. At the end of ECMP experiment, you are expected to see even higher throughput of iperf and lower latency of Memcached, and better video quality, compared with `controller_fat_twocore.py`. 

In this project, you will implement Layer-3 routing and ECMP.
by modifying the following files for the dataplane:
- `p4src/l3fwd.p4`

and the following files for the control plane:
- `controller_fat_l3.py`

We provide a [detailed explaination on P4](p4_explanation.md) which include most useful concepts and primitives about P4 in this project and future projects. 

## Your task: Switching To Layer-3 Routing
Your first task is to switch layer-2 routing based on MAC addresses (in `l2fwd.p4`) to layer-3 routing based on IP addresses. 
Layer 3 routing (also called Network layer routing or IP routing) uses IP addresses to compute routes and configure forwarding tables. 
Put simply, instead of looking at the MAC address, the match action tables on the switch use the IP addresses as their key.

### Steps: Handling Layer 3 Packets

- In `p4src/l3fwd.p4`, define a parser for `tcp` packets. Next, define the deparser (by calling `emit` on all headers). Finally, define the ingress processing logic, including defining a table with destination IP address as the key, defining corresponding actions. 
The default IP addresses for the 16 hosts are from 10.0.0.1 to 10.0.0.16. 
You can use lpm (longest prefix matching) matching rather than exact matching mechanism to reduce the number of table entries. lpm means longest prefix matching, which enables you to use subnet as the matching key. For example, subnet 10.0.1.0/24 represents all IP addresses matching the first 24 bits of 10.0.1.0, i.e., IP addresses from 10.0.1.0 to 10.0.1.255. Note that if you want to set a single IP address, e.g., 10.0.1.1 as the key of a lpm table key, please use 10.0.1.1/32 rather than 10.0.1.1 as the key.
- In `controller/controller_fat_l3.py`, fill in the rules in the forwarding table.

### Test your code

In `topology/p4app_fat.json`, change the `program` field to `p4src/l3fwd.p4`.

Start mininet and the controller:
```
sudo p4run --conf topology/p4app_fat.json
python controller/controller_fat_l3.py
```

Run our testing script:
```
sudo python3 tests/validate_l3_fwd.py
```

## Your task: Switching to ECMP

### Implementing ECMP

ECMP can be implemented in multiple ways using P4 and the control plane leaving you with a lot of freedom in terms of implementing this part of the project. Any implementation that meets the following requirements will be considered acceptable. Note that you are responsible for providing us both the data plane implementation and the control plane rules along with an explanation for how your implementation works. 

**Requirement 1** The flow 5-tuple (source IP address, destination IP address, source port, destination port, protocol) needs to be hashed *in the data plane*. We will not accept solutions that try to circumvent this through control plane rules or by using the controller to do hash computation.

**Requirement 2** The implementation has to be topology independent. It should not make any assumptions regarding the number of switches present, the IP addresses of the underlying hosts or the paths in the topology. While we will only be testing your solution on a Fat Tree, we may not be using the same number of hosts or the same host to IP address mapping as the one you are provided.

### Files that need changes

- In `topology/p4app_fat.json`, change the `program` field to `p4src/ecmp.p4`.
- In `p4src/l3fwd.p4`, implement the ECMP algorithm in the ingress part and define necessary metadata fields. This is in addition to the l3 forwarding logic you added earlier.
- In `controller/controller_fat_l3.py`, fill in the table fields if needed. This is in addition to the l3 routing logic you added earlier.

### Test your code

We have a testing script `tests/validate_ecmp.py`, which will monitor the traffic in your network, to validate whether the ecmp works. It will generate iperf traffic randomly, and test whether the load is balanced across different hops.
To test your network, run

	sudo python3 tests/validate_ecmp.py

The script will output the testing results.

## Compare ECMP with Binary Tree and two-core splitting 

Use *Application setting A* as described in Project 1, but now run it with ECMP. 
 
* **(Expr 2.1)** running application setting A on Fattree (k=4) topology using ECMP

You should answer the following questions in your `report.md`: 
* What is the avg throughput of iperf and avg latency of memcached you observe? How do you compare with Expr 1.1 and 1.2 in Project 1? Explain why you see the differences.

## Bisection Bandwidth

In this experiments, you will compare the bisection bandwidth of Binary tree topology and Fattree topology. You need to let 8 `iperfs` send traffic the other 8 in a one-to-one mapping manner. 
You can use the following commands to run `iperf`. We provide you with two different mapping between `iperf` servers and iperf clients. Run `sudo apt-get install iperf3` to install necessary dependency. 

```
# h1 <-> h9, h2 <-> h10, h3 <-> h11, ..., h8 <-> h16
sudo python apps/send_traffic.py apps/trace/bisec1.txt 1-16 60

# h1 <-> h5, h2 <-> h6, h3 <-> h7, h4 <-> h8, 
# h9 <-> h13, h10 <-> h14, h11 <-> h15, h12 <-> h16
sudo python apps/send_traffic.py apps/trace/bisec2.txt 1-16 60
```

Each command will start one `iperf` on each host, and let 8 of them send traffic to the remaining 8 in a one-to-one mapping manner. 
The output of those iperf servers and clients will be stored in the log directory, and you can also see the average throughput of iperf once the `send_traffic.py` script completes. 

You should answer the following questions in your report.md: 
* What is the bisection bandwidth in theory for Fattree? What number do you get from the two mappings under Fattree?
* Is there any difference between the two real numbers from the two mappings? Why?

## Application placement in FatTree

In this experiment, you will place the iperf and Memcached applications in different hosts and see how placement affects their performance under different topologies. 

You will test application placements as follows: 
* Placement setting 1: iperf on h1,2,3,4 + Memcached on h5,6,7,8
* Placement setting 2: iperf on h1,3,5,7 + Memcached on h2,4,6,8

The above application placements are just a suggestion. The application placement that helps your particular ECMP implementation depends on the way you hash your flows. You need to find an application placement that makes sense for your implementation and impacts its performance. Mention your chosen application placement in your report.

**Note:** Different placement forwards iperf flows and Memcached flows in different paths. If different flow paths overlap a lot, then the performance should be poorer. Instead, if those paths do not overlap a lot, then the performance should be better. Therefore, you can find two different placements based on the flow paths with different performance.

You will run your chosen placement(s) on the Fattree topology.
You should answer the following question in your `report.md`: 
* Does the avg throughput of iperf change under Fattree with different placement schemes? Why?

## Extra Credit 

Can you try to design a different topology other than Binary Tree and FatTree by following two constraints: 1) the total bandwidth of links for one switch do not exceed the switch capacity, 2) the number of links for one switch cannot exceed four? But you can use any number of switches. You should also define your own routing schemes on your topology. How do you compare its performance with Binary Tree and FatTree? Please describe your design in your `report.md`.

## Submission and Grading

### What to submit
You are expected to submit the following documents:

1. Code: The P4 programs that you write to implement L3 routing and ECMP in the dataplane (`p4src/l3fwd.p4`). The controller programs that fill in the forwarding rules for Fattree topologies with L3 routing and ECMP (`controller/controller_fat_l3.py`). We will use scripts to automatically test them. 

2. `report/report.md`: In this report, you should describe how you implement L3 routing, ECMP, and fill in rules with the controller. You also need to answer the questions above. You might put some figures in the `report/` folder, and embed them in your `report.md`. 

Please make sure all files are in the project3 folder of your master branch.

### Grading 

The total grades is 100:

- 20: For your description of how you implement L3 routing and ECMP and fill in rules with the controller in `report.md`.
- 20: For your answers to the questions in `report.md` (you may include some figures).
- 60: We will use scripts to automatically check the correctness of your solutions for L3 routing and ECMP forwarding schemes.
- **20**: Extra credit for designing a different topology.
- Deductions based on late policies

### Survey

Please fill up the survey when you finish your project.

[Survey link](https://docs.google.com/forms/d/e/1FAIpQLSewCzEORStq-6wpSVh6gLLUd8wjLX5McY9yojTyfy1CAFyYYQ/viewform?usp=sf_link)

# Project 3: ECMP and Application Placement

## Objectives

* Implement ECMP and understand its benefits. 
* Understand the benefit of FatTree on application placement. 
* This project also gives you basic 

**Note:** In this project and following ones, we only focus on the Fattree topology with k=4 (*i.e.,* 16 hosts) and Binary Tree with 16 hosts. 

## Getting Started

This project inherits the application setting in project 1. We provide the Fattree topology file `topology/fat_tree_app.json` that couples with our testing scripts. Note that the switch port mapping in `topology/fat_tree_app.json` might be different with your mapping in project 1. 

In project 1, we distributed traffic across two separated core switches for different application (`controller_fat_twocore.py`). But this is not efficient enough. For instance, if one application stops working, then its corresponding core switch is wasted. 
Thus, we need a more advanced routing strategy -- ECMP. At the end of ECMP experiment, you are expected to see even higher throughput of iperf and lower latency of Memcached, and better video quality, compared with `controller_fat_twocore.py`. 

In this project, you will implement Layer-3 routing and ECMP.
by modifying the following files for the data plane:
- `p4src/l3fwd.p4`

and the following files for the control plane:
- `controller_fat_l3.py`

We provide a [detailed explanation on P4](p4_explanation.md) which include most useful concepts and primitives about P4 in this project and future projects. 

## Task 1: Switching To Layer-3 Routing
Your first task is to switch layer-2 routing based on MAC addresses (in `l2fwd.p4`) to layer-3 routing based on IP addresses. 
Layer 3 routing (also called Network layer routing or IP routing) uses IP addresses to compute routes and configure forwarding tables. 
Instead of looking at the MAC address, the match action tables on the switch use the IP addresses as their key.
Note that the default IP addresses for the 16 hosts are from 10.0.0.1 to 10.0.0.16. 

### Step 1: Handling Layer 3 Packets

In `p4src/l3fwd.p4`:
  - Define a parser for `tcp` packets.
  - Define the deparser (by calling `emit` on all headers). - - Define the ingress processing logic, including a table with destination IP address as the key, and corresponding actions. 

**Hint 1:** To correctly setup a parser for TCP packets, you will first need to extract the headers for Ethernet and IP, because TCP is a protocol that is layered within the data of the Ethernet and IP protocols.

**Hint 2:** You might use lpm (longest prefix matching) matching rather than exact matching mechanism to reduce the number of table entries. lpm enables you to use subnet as the matching key. For example, subnet 10.0.1.0/24 represents all IP addresses matching the first 24 bits of 10.0.1.0, i.e., IP addresses from 10.0.1.0 to 10.0.1.255. Note that if you want to set a single IP address, e.g., 10.0.1.1 as the key of a lpm table key, please use 10.0.1.1/32 rather than 10.0.1.1 as the key. lpm means that when there are multiple rules that matches the incoming packet, we follow the rule with the longest prefixes (i.e., the subnet with the longest length. e.g., /32 > /24).

### Step 2: Set up the forwarding table
In `controller/controller_fat_l3.py`, fill up the rules in the forwarding table.
In project 1, we had 
```
controller.table_add("dmac", "forward", ["00:00:0a:00:00:%02x" % (host_id + 1,)], ["%d" % (out_port,)])
```
in the controller for l2 forwarding; now, we would have 
```
controller.table_add("ipv4_lpm", "set_nhop", ["10.0.0.%d/32" % (host_id + 1,)], ["%d" % (out_port,)])
```
in the controller for l3 forwarding. 

### Test your code

Start Mininet and the controller:
```
sudo p4run --conf topology/fat_tree_app.json
python controller/controller_fat_l3.py
```

Run our testing script:
```
sudo python3 tests/validate_l3_fwd.py
```

## Task 2: Implement ECMP

To implement ECMP, we need to first write P4 code in the data plane and then write a controller which installs forwarding rules. Here are a few high-level guidelines:

### Step 1: Implement the data plane
In `p4src/l3fwd.p4`, implement the ECMP tables in the ingress part of the switch and define necessary metadata fields. This is in addition to the l3 forwarding logic you added in Task 1. At a high level, instead of specifying the output port for each flow, we now specify the output port groups for a group of flows. 
There are two types of flows at a switch: (1) Downward flows: For those flows that go downward in the FatTree, there is only one downward path. That is, there is one output port for these flows. (2) Upward flows: For those flows that go to the upper layers of the FatTree, there are multiple equal-cost paths. So we create an ECMP group for these output ports, and uses a hash function to decide which output port to send each flow based on its five tuples (i.e., source IP address, destination IP address, source port, destination port, protocol). 

In `l3fwd.p4`, you need to define two tables: `ipv4_lpm` and `ecmp_group_to_nhop`. 
First, the `ipv4_lpm` table is similar to Task 1 that selects output ports for downward flows, but trigger the action `ecmp_group` for upward flows to calculate hash value. We can calculate the hash function based on the five tuples of a flow, and store the hash value in the metadata for the next table to use.

Second, the `ecmp_group_to_nhop` table maps on the hash value to decide which egress port to send the packet.

Note that we need two tables here because we only need the hash calculation for packets that go upper layers. Therefore, we need the first table to match on packet IP addresses and the second table to match on hash values.
One problem is that since both ToR and Aggregate switches hash on the same five tuples, they may make the same decision on which output port number to take. This causes a collision problem: If two flows get the same hash values on the ToR switch, they will also get the same hash values on the aggregate switch. (*Question: why is this a problem?*) 
To solve this problem, one idea is to use different hash seeds for the ToR and aggregate switches. However, we would like the P4 code in the data plane to be **topology independent**. That is, we cannot allocate hash seeds based on the switch locations, host IP addresses or the paths in the topology. 
<!-- It should not make any assumptions regarding the number of switches present, the IP addresses of the underlying hosts or the paths in the topology.  -->
Instead, our solution is to use the `ecmp_group_to_nhop` table to map on both the hash value and a `ecmp_group_id`.

We use the `ecmp_group_id` to help choose different egress ports on ToR and Aggregate switches for the same five tuples and specify different rules for `ecmp_group_to_nhop` table. In other words, all ToR switches are in one ECMP group, while all aggregated switches are in another group; different ECMP group IDs let ToR and Aggregated switches most likely make different decisions on the same flow. 

### Step 2: Implement the controller
In `controller/controller_fat_l3.py`, you need to generate rules for the tables. This is in addition to the l3 routing logic you added in Task 1.

The controller pre-installs rules in the switches' forwarding tables that forward packets based on the hash values and `ecmp_group_id`'s. The controller should set different `ecmp_group_id`'s for ToR and Aggregate switches. You may check [P4_explanation](p4_explanation.md) on how to write match-action rules in controller. 

The controller can assume the default IP addresses for the 16 hosts are from 10.0.0.1 to 10.0.0.16. The controller can also differentiate ToR, Core, Aggregate switches by their names, and install different rules for each type of switches. 
The rules for each type of switches should be independent, but the rules together should deliver the packets via all the available shortest paths. 

### Test your code

We have a testing script `tests/validate_ecmp.py`, which monitors the traffic in your network, to validate whether ECMP works. It generates iperf traffic randomly, and tests whether the load is balanced across different hops.
To test your network, run

	sudo python3 tests/validate_ecmp.py

The script outputs the testing results. `Test passes` means traffic is evenly distributed; `Test fails` means traffic is not evenly distributed. 

## Compare ECMP with Binary Tree and two-core splitting 

Use the *application setting* as described in Project 1, but now run it with ECMP. 
 
* **(Expr 2.1)** running the application setting on Fattree (k=4) topology using ECMP

You should answer the following questions in your `report.md`: 
* What is the avg throughput of iperf and avg latency of memcached you observe? How do you compare with Expr 1.1 and 1.2 in Project 1? 
* Explain why you see the differences. Use measurement results to demonstrate your points.

**Hint 1:** To understand the performance difference, the first step is to verify that you are using all four cores. The next step is to track the paths the memcached and iperf traffic take. If they collide on the same path, it will cause congestion and affect performance. 
**Hint 2:** The paths taken by the traffic may be related to the hash values. If the paths collide, try changing the hash seeds and see if the paths change.
<!-- If your code is implemented correctly, one reason for such collision could be hash collision. You may try different hash seeds and report the results. -->
**Hint 3:** To get the correct result, you are highly encouraged to run the experiment on Amazon EC2. See how to set it up in `infra.md`. The key problem of running at your local machine is that ECMP introduces more packet processing and takes more CPU resources in the simulation, which may affect the ECMP performance. 


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
* Does the average throughput of iperf change under Fattree with different placement schemes? Why?

## Extra Credits 

### Optional Task 1 (20 credits)
Can you try to design a different topology other than Binary Tree and FatTree by following two constraints: 1) the total bandwidth of links for one switch do not exceed the switch capacity, 2) the number of links for one switch cannot exceed four? But you can use any number of switches. You should also define your own routing schemes on your topology. How do you compare its performance with Binary Tree and FatTree? Please describe your design in your `report.md`.

### Optional Task 2 (20 credits)
Can you try to extend the ECMP implementation to WCMP? We will discuss WCMP in class later. You can look up the key idea in [this Eurosys'14 paper](https://research.google/pubs/pub49093/). 
The key difference between WCMP and ECMP is that it sets up weights for each outgoing ports rather than equally splitting packets across paths. There are three subtasks:
- Implement WCMP (10 credits)
- Generate testing cases that demonstrate the weighted splitting (5 credits) 
- Design and implement scenarios to show the benefits of weighted splitting over ECMP (10 credits). 

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
- **20** extra credits for each TODO task. You get **40** if you finish both. 
- Deductions based on late policies

### Survey

Please fill up the survey when you finish your project.

[Survey link](https://docs.google.com/forms/d/e/1FAIpQLSewCzEORStq-6wpSVh6gLLUd8wjLX5McY9yojTyfy1CAFyYYQ/viewform?usp=sf_link)

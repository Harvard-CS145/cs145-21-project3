/*

Summary: this module does L3 forwarding. For more info on this module, read the project README.

*/

/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*

Summary: The following section defines the protocol headers used by packets. These include the IPv4, TCP, and Ethernet headers. A header declaration in P4 includes all the field names (in order) together with the size (in bits) of each field. Metadata is similar to a header but only holds meaning during switch processing. It is only part of the packet while the packet is in the switch pipeline and is removed when the packet exits the switch.

*/


/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

const bit<16> TYPE_IPV4 = 0x800;

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;


header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp;
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<1>  cwr;
    bit<1>  ece;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t        tcp;
}

struct metadata {}

/*

Summary: the following section defines logic required to parse a packet's headers. Packets need to be parsed in the same order they are added to a packet. See headers.p4 to see header declarations. Deparsing can be thought of as stitching the headers back into the packet before it leaves the switch. Headers need to be deparsed in the same order they were parsed.

*/

/*************************************************************************
*********************** P A R S E R  *******************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    // TODO: Define a parser for ethernet, ipv4 and tcp
    state start {

    }

    
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        // TODO: Deparse the ethernet, ipv4 and tcp headers
        
    }
}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    // This table maps dstAddr to ecmp_group_id and num_nhops (the number of total output ports). The action ecmp_group is actually calculating the hash value.
    table ipv4_lpm {
        //TODO: define the ip forwarding table
        
    }

    // ECMP Only
    // ecmp_group_id: ecmp group ID for this switch, specified by constroller
    // num_nhops: the number of total output ports, specified by controller
    action ecmp_group(bit<14> ecmp_group_id, bit<16> num_nhops){
        //TODO: define the ecmp_group action, where you need to hash the 5-tuple mod num_ports and save it in metadata
        
    }

    // dropped packets will not get forwarded
    action drop() {
        mark_to_drop(standard_metadata);
    }
    
    // The second table maps the hash value you get (you probably need to think of how to store the hash value calculated in the ecmp_group) and the ecmp_group_id to the egress port. The action set_nhop sets the egress port. 
    table ecmp_group_to_nhop {
        //TODO: define the ecmp table, this table is only called when multiple egress ports are available 
    }

    // set next hop
    // port: the egress port for this packet
    action set_nhop(egressSpec_t port) {
        //TODO: Define the set_nhop action. You can copy it from the previous exercise, they are the same.
        
    }

    apply {
        //TODO: implement the ingress logic.
        //ECMP Only Hint: check validities, apply first table (ie, ipv4_lpm), and if multiple possible egress ports exist (ie, ecmp_group action triggered), then apply the second table (ie, ecmp_group_to_nhop).
        
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
    update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	          hdr.ipv4.ihl,
              hdr.ipv4.dscp,
              hdr.ipv4.ecn,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
              hdr.ipv4.hdrChecksum,
              HashAlgorithm.csum16);    
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;

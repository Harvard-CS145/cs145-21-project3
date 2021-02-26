#! /bin/bash

rm -rf iperf_logs
mkdir iperf_logs

for server in {1..8}
do
    port=$((5000+$server))
    ~/mininet/util/m h$server iperf3 -s --port $port 2> /dev/null > iperf_logs/log_h$server.txt &
done

sleep 5

for client in {9..16}
do
    server=$(($client-8))
    port=$((5000+$server))
    ~/mininet/util/m h$client iperf3 -c 10.0.0.$server -t 60 --port $port 2> /dev/null > iperf_logs/log_h$client.txt &
done

sleep 60

pkill iperf3

echo finished
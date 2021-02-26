#! /bin/bash

rm -rf iperf_logs
mkdir iperf_logs

for server in 1 2 3 4 9 10 11 12
do
    port=$((6000+$server))
    ~/mininet/util/m h$server iperf3 -s --port $port  > iperf_logs/log_h$server.txt &
done

sleep 5

for client in 5 6 7 8 13 14 15 16
do
    server=$(($client-4))
    port=$((6000+$server))
    ~/mininet/util/m h$client iperf3 -c 10.0.0.$server -t 60 --port $port  > iperf_logs/log_h$client.txt &
done

sleep 60

pkill iperf3

echo finished

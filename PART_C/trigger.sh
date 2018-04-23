netcat 172.0.1.2 9001 &
sleep 0.1
netcat 172.0.1.1 9001 &
sleep 0.2
netcat 172.0.2.1 9001 &
sleep 0.3
netcat 172.0.3.1 9001 &
sleep 0.1
netcat 172.0.4.2 9001 &
sleep 0.2
netcat 172.0.4.1 9001 &

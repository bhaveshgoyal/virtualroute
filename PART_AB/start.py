#!/usr/bin/python

"""
Example network of Quagga routers
(QuaggaTopo + QuaggaService)
"""

import sys
import atexit
from datetime import datetime
# patch isShellBuiltin
import mininet.util
import mininext.util
mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

from mininet.util import dumpNodeConnections
from mininet.node import OVSController
from mininet.log import setLogLevel, info

from mininext.cli import CLI
from mininext.net import MiniNExT

from topo import QuaggaTopo

net = None


def startNetwork(static_routes):
    "instantiates a topo, then starts the network and prints debug information"

    info('** Creating Quagga network topology\n')
    topo = QuaggaTopo()

    info('** Starting the network\n')
    global net
    net = MiniNExT(topo, controller=OVSController)
    net.start()
    t_start = datetime.now()
    info('** Dumping host connections\n')
    dumpNodeConnections(net.hosts)

    net.get('H1').cmd('sysctl -w net.ipv4.ip_forward=1')
    net.get('H2').cmd('sysctl -w net.ipv4.ip_forward=1')
    net.get("R1").cmd("sysctl -w net.ipv4.ip_forward=1")
    net.get("R2").cmd("sysctl -w net.ipv4.ip_forward=1")
    net.get("R3").cmd("sysctl -w net.ipv4.ip_forward=1")
    net.get("R4").cmd("sysctl -w net.ipv4.ip_forward=1")

    net.get("R1").cmd("ifconfig R1-eth1 172.0.2.2/24")
    net.get("R1").cmd("ifconfig R1-eth2 172.0.3.2/24")
    net.get("R2").cmd("ifconfig R2-eth0 172.0.2.1/24")
    net.get("R2").cmd("ifconfig R2-eth1 172.0.5.1/24")
    net.get("R3").cmd("ifconfig R3-eth0 172.0.3.1/24")
    net.get("R3").cmd("ifconfig R3-eth1 172.0.6.1/24")
    net.get("R4").cmd("ifconfig R4-eth0 172.0.4.1/24")
    net.get("R4").cmd("ifconfig R4-eth1 172.0.5.2/24")
    net.get("R4").cmd("ifconfig R4-eth2 172.0.6.2/24")
    net.get("H2").cmd("ifconfig H2-eth0 172.0.4.2/24")

    if static_routes:
        net.get("R1").cmd("ip route add 172.0.5.0/24 via 172.0.2.1 dev R1-eth1")
        net.get("R1").cmd("ip route add 172.0.4.0/24 via 172.0.2.1 dev R1-eth1")
        net.get("R1").cmd("ip route add 172.0.4.0/24 via 172.0.3.1 dev R1-eth2")
        net.get("R1").cmd("ip route add 172.0.6.0/24 via 172.0.3.1 dev R1-eth2")
        net.get("R2").cmd("ip route add 172.0.1.0/24 via 172.0.2.2 dev R2-eth0")
        net.get("R2").cmd("ip route add 172.0.4.0/24 via 172.0.5.2 dev R2-eth1")
        net.get("R2").cmd("ip route add 172.0.3.0/24 via 172.0.2.2 dev R2-eth0")
        net.get("R3").cmd("ip route add 172.0.1.0/24 via 172.0.3.2 dev R3-eth0")
        net.get("R3").cmd("ip route add 172.0.2.0/24 via 172.0.3.2 dev R3-eth0")
        net.get("R3").cmd("ip route add 172.0.4.0/24 via 172.0.6.2 dev R3-eth1")
        net.get("R4").cmd("ip route add 172.0.2.0/24 via 172.0.5.1 dev R4-eth1")
        net.get("R4").cmd("ip route add 172.0.3.0/24 via 172.0.6.1 dev R4-eth2")
        net.get("R4").cmd("ip route add 172.0.1.0/24 via 172.0.5.1 dev R4-eth1")
        net.get("R4").cmd("ip route add 172.0.1.0/24 via 172.0.6.1 dev R4-eth2")
    
    net.get("R1").cmd("iptables -t nat -A POSTROUTING -o R1-eth0 -j MASQUERADE")
    net.get("R1").cmd("iptables -A FORWARD -i R1-eth0 -o R1-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT")
    net.get("R1").cmd("iptables -A FORWARD -i R1-eth1 -o R1-eth0 -j ACCEPT")
    
    net.get("R2").cmd("iptables -t nat -A POSTROUTING -o R2-eth0 -j MASQUERADE")
    net.get("R2").cmd("iptables -A FORWARD -i R2-eth0 -o R2-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT")
    net.get("R2").cmd("iptables -A FORWARD -i R2-eth1 -o R2-eth0 -j ACCEPT")
    
    net.get("R3").cmd("iptables -t nat -A POSTROUTING -o R3-eth1 -j MASQUERADE")
    net.get("R3").cmd("iptables -A FORWARD -i R3-eth1 -o R3-eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT")
    net.get("R3").cmd("iptables -A FORWARD -i R3-eth0 -o R3-eth1 -j ACCEPT")
    
    net.get("R4").cmd("iptables -t nat -A POSTROUTING -o R4-eth0 -j MASQUERADE")
    net.get("R4").cmd("iptables -A FORWARD -i R4-eth0 -o R4-eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT")
    net.get("R4").cmd("iptables -A FORWARD -i R4-eth1 -o R4-eth0 -j ACCEPT")
    net.get("R4").cmd("iptables -A FORWARD -i R4-eth2 -o R4-eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT")
    net.get("R4").cmd("iptables -A FORWARD -i R4-eth0 -o R4-eth2 -j ACCEPT")
    
    info('** Testing network connectivity\n')

    info('** Dumping host processes\n')
    for host in net.hosts:
        host.cmdPrint("ps aux")

    info('** Running CLI\n')
    loss = 100
    while (loss > 0):
        loss = net.pingAll()
    t_end = datetime.now() - t_start
    print "Percentage Loss: " + str(loss)
    print "Route Convergence Time: " + str(t_end.total_seconds()) + "seconds"
    
    if static_routes:
        print ("[MESSAGE:] Enabling Static Routes...")
    else:
        print ("[MESSAGE:] Disabling Static Routes...")
    
    CLI(net)


def stopNetwork():
    "stops a network (only called on a forced cleanup)"

    if net is not None:
        info('** Tearing down Quagga network\n')
        net.stop()

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    static_routes = True
    if len(sys.argv) == 2:
        if sys.argv[1] == "-d":
            static_routes = False
        elif sys.argv[1] != "-s":
            print "Invalid option: " + sys.argv[1] + ". Please use [-d/-s]."
	    exit(0)
    startNetwork(static_routes)

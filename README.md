# virtualRoute
virtualRoute is an application level implementation of RIP routing protocol. The program also contains configurations scripts for Quagga and mininext virtual networks to setup L4 level network connectivity for a given network topology.

### To run:
```
Ensure you have a virtualization software such as a Virtual box or VMWare (it is recommended that you download this virtualization software even if you are using Ubuntu). Mininet works directly on the virtual box.
Once you have this, proceed with mininet installation is as follows:
Download mininet version 2.1.0 from https://github.com/mininet/mininet/wiki/Mininet- VM-Images. [Only use 2.1.0 version]
Next you need to download and install the MiniNExT extension. This extension lets you virtualize file system and allows you to build complex networks over Mininet.

Install Quaga using
$>sudo apt-get install quagga. 

git clone https://github.com/bhaveshgoyal/virtualroute.git
cd virtualroute/PART\ A/

To run quagga scripts with static routes:
sudo python start.py [-s]

To run quagga scripts [with ripd enabled] and disabling static routes:
sudo python start.py -d

Find more details on configuring ripd and zebra daemons in the Report.


After you have the mininext CLI and quagga hosts up and running, you could proceed with running RIP over all the hosts.
To operate RIP, open xterm for each of the hosts:
mininext$> xterm H1 [Extra Host Window to trigger RIP]
mininext$> xterm H1
mininext$> xterm H2
mininext$> xterm R1
mininext$> xterm R2
mininext$> xterm R3
mininext$> xterm R4

Note: If xterm doesn't work over SSH forwarding, first install GUI for mininet,
sudo apt-get install lxde xinit open-vm-tools(If using vmware or install other virtualization extras if not)
cd <path-to>/PART\ C/

Now, on each host run the rip client:
python client.py <Host-label> <IPs to neighbours>

For the given topology, the commands would look like:
python client.py H1 172.0.1.1
python client.py R1 172.0.1.2 172.0.2.1 172.0.3.1
python client.py R2 172.0.1.1 172.0.3.1
python client.py R3 172.0.4.1 172.0.2.1 172.0.3.1
python client.py R4 172.0.4.2

After all servers are up, trigger rip using the provided trigger script.

On the Extra host window, perform:
chmod +x ./trigger.sh
./trigger.sh

The Final routing table of each Host would be created in [Host-label]_routes file.
```

Note: The Program needs access to two utility files. 'weights', 'nodes'. The weights would contain the global link information for the nodes,
from which each node would extract its neighbour link costs and initiate bellman-ford. The nodes would contain the list of all nodes in the network.
In the implementation, the code checks the 'weights' file periodically after every 7 seconds(Configurable) for any link updates, if yes then
automatically sends the updates to neighbours and outputs the new routes in its corresponding routing file.
Thus, if you want to observe dynamic route updates, jusdt change any link value in weights file, and new routes should automatically get established.
(For instance changing R1-R2 from 10 to 1 would update R1/H1's route file to make a route till H2, through R1-R2 instead).

----------------------------------

**Testing Environment**

```
python specifications: v2.7.6

System Specifications:
Linux mininet-vm 3.13.0-24-generic #46-Ubuntu SMP
Target: x86_64 x86_64 x86_64 GNU/Linux

Virtualization Software:
VMware Fusion (Licensed)

```

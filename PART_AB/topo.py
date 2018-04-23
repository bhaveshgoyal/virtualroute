"""
Example topology of Quagga routers
"""

import inspect
import os
from mininext.topo import Topo
from mininext.services.quagga import QuaggaService

from collections import namedtuple

QuaggaHost = namedtuple("QuaggaHost", "name ip DG loIP")
net = None


class QuaggaTopo(Topo):

    "Creates a topology of Quagga routers"

    def __init__(self):
        """Initialize a Quagga topology with 5 routers, configure their IP
           addresses, loop back interfaces, and paths to their private
           configuration directories."""
        Topo.__init__(self)

        # Directory where this file / script is located"
        selfPath = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))  # script directory

        # Initialize a service helper for Quagga with default options
        quaggaSvc = QuaggaService(autoStop=False)

        # Path configurations for mounts
        quaggaBaseConfigPath = selfPath + '/configs/'

        # List of Quagga host configs
        quaggaHosts = []
        quaggaHosts.append(QuaggaHost(name='H1', ip='172.0.1.2/24',DG='via 172.0.1.1',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='R1', ip='172.0.1.1/24',DG='',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='R2', ip='172.0.2.1/24',DG='',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='R3', ip='172.0.3.1/24',DG='',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='R4', ip='172.0.4.1/24',DG='',
                                      loIP=None))
        quaggaHosts.append(QuaggaHost(name='H2', ip='172.0.4.2/24',DG='via 172.0.4.1',
                                      loIP=None))
        # Add switch for IXP fabric
        #ixpfabric = self.addSwitch('fabric-sw1')

        # Setup each Quagga router, add a link between it and the IXP fabric
        containers = []
        for host in quaggaHosts:

            # Create an instance of a host, called a quaggaContainer
            quaggaContainer = self.addHost(name=host.name,
                                           ip=host.ip,
                                           hostname=host.name,
                                           defaultRoute=host.DG,
                                           privateLogDir=True,
                                           privateRunDir=True,
                                           inMountNamespace=True,
                                           inPIDNamespace=True,
                                           inUTSNamespace=True)
            containers.append(quaggaContainer)
            # Add a loopback interface with an IP in router's announced range
            self.addNodeLoopbackIntf(node=host.name, ip=host.loIP)

            # Configure and setup the Quagga service for this node
            quaggaSvcConfig = \
                {'quaggaConfigPath': quaggaBaseConfigPath + host.name}
            self.addNodeService(node=host.name, service=quaggaSvc,
                                nodeConfig=quaggaSvcConfig)

            # Attach the quaggaContainer to the IXP Fabric Switch
            #self.addLink(quaggaContainer, ixpfabric)
        self.addLink(containers[0], containers[1])
        self.addLink(containers[4], containers[5])
        self.addLink(containers[1], containers[2])
        self.addLink(containers[1], containers[3])
        self.addLink(containers[2], containers[4])
        self.addLink(containers[3], containers[4])

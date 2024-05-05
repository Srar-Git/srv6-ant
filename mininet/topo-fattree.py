#!/usr/bin/python

#  Copyright 2019-present Open Networking Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import argparse
import os
import subprocess
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Host
from mininet.topo import Topo
from stratum import StratumBmv2Switch

CPU_PORT = 255


class IPv6Host(Host):
    """Host that can be configured with an IPv6 gateway (default route).
    """

    def config(self, ipv6, ipv6_gw=None, **params):
        super(IPv6Host, self).config(**params)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip -6 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip -6 addr add %s dev %s' % (ipv6, self.defaultIntf()))
        if ipv6_gw:
            self.cmd('ip -6 route add default via %s' % ipv6_gw)
        # Disable offload
        for attr in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload %s %s off" % (self.defaultIntf(), attr)
            self.cmd(cmd)

        def updateIP():
            return ipv6.split('/')[0]

        self.defaultIntf().updateIP = updateIP

    def terminate(self):
        super(IPv6Host, self).terminate()


class FatTreeTopo(Topo):
    """k=4 fattree topology with IPv6 hosts"""

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)

        # switches
        cores = {}
        aggs = {}
        edges = {}
        for i in range(1, 21):
            if i <= 4:
                core = self.addSwitch('s%s_core%s' % (i, i), cls=StratumBmv2Switch, cpuport=CPU_PORT)
                cores[i] = core
            if i > 4 and i <= 12:
                agg = self.addSwitch('s%s_agg%s' % (i, i-4), cls=StratumBmv2Switch, cpuport=CPU_PORT)
                aggs[i-4] = agg
            if i > 12:
                edge = self.addSwitch('s%s_edge%s' % (i, i-12), cls=StratumBmv2Switch, cpuport=CPU_PORT)
                edges[i-12] = edge
        # hosts
        # pod 1
        h1a = self.addHost('h1a', cls=IPv6Host, mac="00:00:00:00:00:1A",
                    ipv6='2001:1:1::a/64', ipv6_gw='2001:1:A::ff')
        h1b = self.addHost('h1b', cls=IPv6Host, mac="00:00:00:00:00:1B",
                    ipv6='2001:1:1::b/64', ipv6_gw='2001:1:B::ff')
        h1c = self.addHost('h1c', cls=IPv6Host, mac="00:00:00:00:00:1C",
                    ipv6='2001:1:1::c/64', ipv6_gw='2001:1:C::ff')
        h1d = self.addHost('h1d', cls=IPv6Host, mac="00:00:00:00:00:1D",
                    ipv6='2001:1:1::d/64', ipv6_gw='2001:1:D::ff')

        # pod 2
        h2a = self.addHost('h2a', cls=IPv6Host, mac="00:00:00:00:00:2A",
                    ipv6='2002:1:1::a/64', ipv6_gw='2002:1:A::ff')
        h2b = self.addHost('h2b', cls=IPv6Host, mac="00:00:00:00:00:2B",
                    ipv6='2002:1:1::b/64', ipv6_gw='2002:1:B::ff')
        h2c = self.addHost('h2c', cls=IPv6Host, mac="00:00:00:00:00:2C",
                    ipv6='2002:1:1::c/64', ipv6_gw='2002:1:C::ff')
        h2d = self.addHost('h2d', cls=IPv6Host, mac="00:00:00:00:00:2D",
                    ipv6='2002:1:1::d/64', ipv6_gw='2002:1:D::ff')

        # pod 3
        h3a = self.addHost('h3a', cls=IPv6Host, mac="00:00:00:00:00:3A",
                    ipv6='2003:1:1::a/64', ipv6_gw='2003:1:A::ff')
        h3b = self.addHost('h3b', cls=IPv6Host, mac="00:00:00:00:00:3B",
                    ipv6='2003:1:1::b/64', ipv6_gw='2003:1:B::ff')
        h3c = self.addHost('h3c', cls=IPv6Host, mac="00:00:00:00:00:3C",
                    ipv6='2003:1:1::c/64', ipv6_gw='2003:1:C::ff')
        h3d = self.addHost('h3d', cls=IPv6Host, mac="00:00:00:00:00:3D",
                    ipv6='2003:1:1::d/64', ipv6_gw='2003:1:D::ff')

        # pod 4
        h4a = self.addHost('h4a', cls=IPv6Host, mac="00:00:00:00:00:4A",
                    ipv6='2004:1:1::a/64', ipv6_gw='2004:1:A::ff')
        h4b = self.addHost('h4b', cls=IPv6Host, mac="00:00:00:00:00:4B",
                    ipv6='2004:1:1::b/64', ipv6_gw='2004:1:B::ff')
        h4c = self.addHost('h4c', cls=IPv6Host, mac="00:00:00:00:00:4C",
                    ipv6='2004:1:1::c/64', ipv6_gw='2004:1:C::ff')
        h4d = self.addHost('h4d', cls=IPv6Host, mac="00:00:00:00:00:4D",
                    ipv6='2004:1:1::d/64', ipv6_gw='2004:1:D::ff')


        # Links
        # core1 
        self.addLink(cores[1], aggs[1])
        self.addLink(cores[1], aggs[3])
        self.addLink(cores[1], aggs[5])
        self.addLink(cores[1], aggs[7])

        # core2 
        self.addLink(cores[2], aggs[1])
        self.addLink(cores[2], aggs[3])
        self.addLink(cores[2], aggs[5])
        self.addLink(cores[2], aggs[7])

        # core3
        self.addLink(cores[3], aggs[2])
        self.addLink(cores[3], aggs[4])
        self.addLink(cores[3], aggs[6])
        self.addLink(cores[3], aggs[8])

        # core4
        self.addLink(cores[4], aggs[2])
        self.addLink(cores[4], aggs[4])
        self.addLink(cores[4], aggs[6])
        self.addLink(cores[4], aggs[8])
      
        # agg1
        self.addLink(aggs[1], edges[1])
        self.addLink(aggs[1], edges[2])
        # agg2
        self.addLink(aggs[2], edges[1])
        self.addLink(aggs[2], edges[2])

        # agg3
        self.addLink(aggs[3], edges[3])
        self.addLink(aggs[3], edges[4])
        # agg4
        self.addLink(aggs[4], edges[3])
        self.addLink(aggs[4], edges[4]) 

        # agg5
        self.addLink(aggs[5], edges[5])
        self.addLink(aggs[5], edges[6])
        # agg6
        self.addLink(aggs[6], edges[5])
        self.addLink(aggs[6], edges[6]) 

        # agg7
        self.addLink(aggs[7], edges[7])
        self.addLink(aggs[7], edges[8])
        # agg8
        self.addLink(aggs[8], edges[7])
        self.addLink(aggs[8], edges[8]) 

        # edge1
        self.addLink(edges[1], h1a)
        self.addLink(edges[1], h1b)
        # edge2
        self.addLink(edges[2], h1c)
        self.addLink(edges[2], h1d)

        # edge3
        self.addLink(edges[3], h2a)
        self.addLink(edges[3], h2b)
        # edge4
        self.addLink(edges[4], h2c)
        self.addLink(edges[4], h2d)

        # edge5
        self.addLink(edges[5], h3a)
        self.addLink(edges[5], h3b)
        # edge6
        self.addLink(edges[6], h3c)
        self.addLink(edges[6], h3d)

        # edge7
        self.addLink(edges[7], h4a)
        self.addLink(edges[7], h4b)
        # edge8
        self.addLink(edges[8], h4c)
        self.addLink(edges[8], h4d)

        
def getControllerIP():
    result = os.popen("sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' onos")  
    res = result.read()  
    for line in res.splitlines():  
        return line
    

def main():
    # controller_ip = str(getControllerIP())
    # controller = RemoteController('c0', ip=controller_ip)
    # controller = RemoteController('c0', ip="10.37.86.141")
    # controller ip: sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' onos
    net = Mininet(topo=FatTreeTopo(), controller=None)
    # net.addController(controller)
    net.start()
    CLI(net)
    net.stop()
    print '#' * 80
    print 'ATTENTION: Mininet was stopped! Perhaps accidentally?'
    print 'No worries, it will restart automatically in a few seconds...'
    print 'To access again the Mininet CLI, use `make mn-cli`'
    print 'To detach from the CLI (without stopping), press Ctrl-D'
    print 'To permanently quit Mininet, use `make stop`'
    print '#' * 80


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mininet topology script for 2x2 fabric with stratum_bmv2 and IPv6 hosts')
    args = parser.parse_args()
    setLogLevel('info')

    main()

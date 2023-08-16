#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

# Forwarding table class, glorified list of entry dicts
# has additional helper functions
class Table:
    
    tbl = []
    
    # return table as string
    def __str__(self):
        return str(self.tbl)
    
    # return table
    def get_tbl(self):
        return self.tbl
    
    # append routing entry dict to tbl
    def append(self, msg):
        self.tbl.append(msg)
        
    # remove dead entries from table
    def withdraw(self, withdraw_list):
        pass
    
        # go through withdraw_list and remove from tbl
        # todo 
#        for to_remove in withdraw_list:
#            network = to_remove['network']
#            netmask = to_remove['netmask']
#            for entry in self.tbl:
#                if entry['network'] == network and entry['netmask'] == netmask:
#                    self.tbl.remove(entry)
#                    break

    # finds best route to forward data to
    def best_route(self, dst):
        possible_routes = []
        
        for entry in self.tbl:
            network = entry['network']
            netmask = entry['netmask']
            print('entry', network, netmask)
            # mask both addresses to see if equal
            if self.mask(network, netmask) == self.mask(dst, netmask):
                possible_routes.append(entry)
        
        # return None if no routes found
        if len(possible_routes) == 0:
            fwding_address = None
        else:
            # select best route
            # todo...
            
            # get peer address from first entry
            fwding_address = possible_routes[0]['peer']
        return fwding_address
    
    # performs mask operation by converting to binary and using bitwise 'and'
    def mask(self, network, netmask):
        network = network.split('.')
        netmask = netmask.split('.')
        bnet = []
        bmask = []
        bmasked = []
        masked = []
        for i in range(4):
            # convert to binary
            bnet.append(bin(int(network[i])))
            bmask.append(bin(int(netmask[i])))
#            print(bnet[i],bmask[i])

            # bitwise 'and'
            bmasked.append(int(bnet[i],2) & int(bmask[i],2))
            # convert back to decimal int string
            masked.append(str(int(bmasked[i])))
#            print(bmasked[i], masked[i])

        # rejoin as string
        return '.'.join(masked)

class Router:

    relations = {}
    sockets = {}
    ports = {}

    # Additional data not from starter code
    tbl = Table() # forwarding table
    neighbors = [] # list of router neighbors
    announcements = [] # list of announcements
    revocations = [] # list of revocations
    
    def __init__(self, asn, connections):
        print("Router at AS %s starting up" % asn)
        self.asn = asn
        for relationship in connections:
            port, neighbor, relation = relationship.split("-")
            self.sockets[neighbor] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sockets[neighbor].bind(('localhost', 0))
            self.ports[neighbor] = int(port)
            self.relations[neighbor] = relation
            self.send(neighbor, json.dumps({ "type": "handshake", "src": self.our_addr(neighbor), "dst": neighbor, "msg": {}  }))
            self.neighbors.append(neighbor)

    def our_addr(self, dst):
        quads = list(int(qdn) for qdn in dst.split('.'))
        quads[3] = 1
        return "%d.%d.%d.%d" % (quads[0], quads[1], quads[2], quads[3])

    def send(self, network, message):
        self.sockets[network].sendto(message.encode('utf-8'), ('localhost', self.ports[network]))

    def run(self):
        while True:
            socks = select.select(self.sockets.values(), [], [], 0.1)[0]
            for conn in socks:
                k, addr = conn.recvfrom(65535)
                srcif = None
                for sock in self.sockets:
                    if self.sockets[sock] == conn:
                        srcif = sock
                        break
                msg = k.decode('utf-8')
                
                print("Received message '%s' from %s" % (msg, srcif))
                
                # load msg to dict
                packet = json.loads(msg)
                p_type = packet['type']
                
                # process packets by type
                if p_type == 'update':
                    self.update(packet)
#                    print(self.tbl.mask(packet['msg']['network'],packet['msg']['netmask']))
                elif p_type == 'withdraw':
                    self.withdraw(packet)
                elif p_type == 'data':
#                    print('src:{},dest:{},addr,{},sock:{}'.format(packet['src'],packet['dst'], addr,srcif)) 
                    self.data(packet, srcif)
                elif p_type == 'dump':
                    self.dump(packet)
                
        return
    
    # respond to 'update' type packets
    def update(self, packet):
        
        # add msg to announcements
        self.announcements.append(packet)
        
        # add entry to forwarding table
        entry = packet['msg']
        entry['peer'] = packet['src']
        self.tbl.append(entry)
        
        # build subset msg to be forwarded
        fwd_msg = {}
        fwd_msg['netmask'] = packet['msg']['netmask']
        # add asn to ASPath
        aspath = [self.asn,]
        aspath.extend(packet['msg']['ASPath'])
        fwd_msg['ASPath'] = aspath
        fwd_msg['network'] = packet['msg']['network']
        
        # forward packet if necessary
        relationship = self.relations[packet['src']]
        
        # select neighbors to forward to based on relationship
        if relationship == 'cust':
            forwarding_list = self.neighbors
        else:
            forwarding_list = self.customers()
            
        # forward update
        for neighbor in forwarding_list:
            if neighbor != packet['src']:
                self.send(neighbor, json.dumps({ 'msg': fwd_msg, 'src': self.our_addr(neighbor), 'dst': neighbor, 'type': 'update' }))
        
        
    # respond to 'withdraw' type packets
    def withdraw(self, packet):
        
        # add msg to revocations
        self.revocations.append(packet)
        
        # remove dead entry from fwding tbl
        self.tbl.withdraw(packet['msg'])
        
        # forward packet if necessary
        relationship = self.relations[packet['src']]
        
        # select neighbors to forward to based on relationship
        if relationship == 'cust':
            forwarding_list = self.neighbors
        else:
            forwarding_list = self.customers()
            
        # forward withdraw
        for neighbor in forwarding_list:
            if neighbor != packet['src']:
                self.send(neighbor, json.dumps({ 'msg': packet['msg'], 'src': self.our_addr(neighbor), 'dst': neighbor, 'type': 'withdraw' }))
                
    # forward 'data' type packets
    def data(self, packet, srcif):
        fwding_address = self.tbl.best_route(packet['dst'])
        if fwding_address == None:
            self.send(srcif, json.dumps({ 'msg': {}, 'src': self.our_addr(srcif), 'dst': packet['src'], 'type': 'no route' }))
        else:
            self.send(fwding_address, json.dumps(packet))
        
    # return current table to source
    def dump(self, packet):
#        print(packet[msg])
        # send current table
        neighbor = packet['src']
        self.send(neighbor, json.dumps({ 'msg': self.tbl.get_tbl(), 'src': self.our_addr(neighbor), 'dst': neighbor, 'type': 'table' }))
    
    # get list of customers from router neighbors
    def customers(self):
        custs = []
        for neighbor in self.neighbors:
            if self.relations[neighbor] == 'cust':
                custs.append(neighbor)
        return custs

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='route packets')
    parser.add_argument('asn', type=int, help="AS number of this router")
    parser.add_argument('connections', metavar='connections', type=str, nargs='+', help="connections")
    args = parser.parse_args()
    router = Router(args.asn, args.connections)
    router.run()

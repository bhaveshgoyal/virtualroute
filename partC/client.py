import socket
import util
from util import Graph, peerSock, PORT
import sys
import select
import json
import copy
import time, threading

lock = threading.Lock()
period = 7 # Checks for Updates Every 7 seconds

def set_init_graph(weight_file, topo_file):
	global curr_table
	global label

	path = './' + label + '/weights'
	g = Graph()
	g.init_config(label, weight_file, topo_file)
	g.bellman_on_src(label)
	curr_table = g
	print "Initial Table:\n" + str(curr_table.get_routes())

def send_to_nbrs(nbrs):
	global curr_table
	global label

	for each in nbrs:
		nbr = peerSock()
		print label + " Sending distance vector to " + each
		print curr_table.get_routes()
		nbr.connect(each)
#		nbr.sendmsg(curr_table.get_routes()[label], label, topoUpdate)
		nbr.sendmsg(curr_table.get_routes()[label], label)


def check_weight_update(weight_file, topo_file, nbrs):
	global curr_table
	global label

	print "Checking for Topology Changes"
	path = './' + label + '/weights'
	update = Graph()
	update.init_config(label, weight_file, topo_file)
	lock.acquire()
	if curr_table.serialize != update.serialize:
		curr_table.serialize = copy.deepcopy(update.serialize)
		print "Topology update detected. Rerouting..."
		update.bellman_on_src(label)
		curr_table.routes[label] = copy.deepcopy(update.routes[label])
		curr_table.set_routes(copy.deepcopy(update.get_routes()))
		curr_table.bellman_on_src(label)
		print curr_table.get_routes()
#		send_to_nbrs(nbrs, True)
		send_to_nbrs(nbrs)
	lock.release()
	threading.Timer(period, check_weight_update, [weight_file, topo_file, nbrs]).start() # Trigger Periodic Check
		

if __name__ == "__main__":
	global curr_table
	global label
	
	if len(sys.argv) < 3:
		print "Usage args: <Node-Label> [List of IPs of Neighbours]"
		sys.exit(0)
	label = sys.argv[1]
	
	set_init_graph('weights', 'nodes') # Get Initial Graph(only neighbours)
	timer_init = False
	server = socket.socket()
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind(('', PORT))
	print "Node bound to %s" % (PORT)
	server.listen(10) # Atmost 10 clients

	nbrs = sys.argv[2:]

	input = [sys.stdin, server]
	while True:
		print "Waiting on select"
		read, write, exceptr = select.select(input, [], [])
		for conn in read:
			if conn == sys.stdin:
				command = sys.stdin.readline()
#				send_to_nbrs(nbrs, False)
				send_to_nbrs(nbrs)
				if not timer_init:
					check_weight_update('weights', 'nodes', nbrs)
					timer_init = True
			elif conn == server:
				cli, addr = conn.accept()
				recv_data = cli.recv(1024)
				obj = json.loads(recv_data.decode('utf-8'))
				print obj
				rcvd_route = obj['data']
				unidict = {k.encode('utf8'): float(v) for k, v in rcvd_route.items()}
				rcvd_route = unidict
				rcvd_label = obj['from_label']
#				topo_update = obj['topoUpdate']
				lock.acquire()
				old_routes = copy.deepcopy(curr_table.get_routes())
				print rcvd_label
#				old_routes[rcvd_label] = rcvd_route[rcvd_label]
				curr_table.routes[rcvd_label] = rcvd_route
				curr_table.bellman_on_src(label) # Compute distance from itself to all
#				if topo_update:
#					print "Topology Update from neighbour"
#					set_init_graph('weights', 'nodes') # Get Initial Graph(only neighbours)
#				for src in rcvd_route:
#					for dst in rcvd_route[src]:
#						if topo_update or float(old_routes[src][dst]) > float(rcvd_route[src][dst]):
#							old_routes[src][dst] = rcvd_route[src][dst]
				if old_routes != curr_table.get_routes():
					print "Routing Table updated"
#					curr_table.set_routes(old_routes)
					print curr_table.get_routes() 
#					send_to_nbrs(nbrs, topo_update)
					send_to_nbrs(nbrs)
				else:
					print "No new update"
				lock.release()

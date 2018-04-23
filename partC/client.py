import socket
import util
from util import Graph, peerSock, PORT
import sys
import select
import json
import copy
import time, threading
from datetime import datetime

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
		nbr.sendmsg(curr_table.get_routes()[label], label)
		nbr.close()

def check_weight_update(weight_file, topo_file, nbrs):
	global curr_table
	global label
	global t_start

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
		curr_table.hops[label] = copy.deepcopy(update.hops[label])
		curr_table.set_hops(copy.deepcopy(update.get_hops()))
		curr_table.start = datetime.now()
		curr_table.bellman_on_src(label)
		print curr_table.get_routes()
		send_to_nbrs(nbrs)
	lock.release()
	threading.Timer(period, check_weight_update, [weight_file, topo_file, nbrs]).start() # Trigger Periodic Check
		

if __name__ == "__main__":
	global curr_table
	global label
	global t_start
	global t_end
	
	if len(sys.argv) < 3:
		print "Usage args: <Node-Label> [List of IPs of Neighbours]"
		sys.exit(0)
	label = sys.argv[1]
	
	set_init_graph('weights', 'nodes') # Get Initial Graph(only neighbours)
	timer_init = False
	
	trigger_port = 9001
	trigger_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	trigger_server.bind(('', 9001))
	print "Server waiting for trigger at %s" % (trigger_port)
	trigger_server.listen(10)

	server = socket.socket()
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind(('', PORT))
	print "Node bound to %s" % (PORT)
	server.listen(10) # Atmost 10 concurrent clients

	nbrs = sys.argv[2:]

	input = [trigger_server, server]
	
	print "Press [Enter] after all servers have been setup."

	while True:
		print "Waiting for available data to be read"
		read, write, exceptr = select.select(input, [], [])
		for conn in read:
			if conn == trigger_server:
				cli, addr = trigger_server.accept()
				curr_table.start = datetime.now()
				send_to_nbrs(nbrs)
				if not timer_init:
					check_weight_update('weights', 'nodes', nbrs)
					timer_init = True
			elif conn == server:
				cli, addr = conn.accept()
				recv_data = cli.recv(1024)
				obj = json.loads(recv_data.decode('utf-8'))
				rcvd_route = obj['data']
				unidict = {k.encode('utf8'): float(v) for k, v in rcvd_route.items()}
				rcvd_route = unidict
				rcvd_label = obj['from_label']
				
				print "Distance vector from: " + rcvd_label
				print str(rcvd_route)
				lock.acquire()
				old_routes = copy.deepcopy(curr_table.get_routes())
				curr_table.routes[rcvd_label] = rcvd_route
				curr_table.bellman_on_src(label) # Compute distance from itself to all
				
#				if tstart_init:
#					t_end = datetime.now()
#					convergence = (t_end - t_start)
#					convergence = float(convergence.total_seconds()*1000)
#					print "Current convergence time: " + str(convergence) + "ms"
#					tstart_init = True
				if old_routes != curr_table.get_routes():
					print "Routing Table updated"
					print curr_table.get_routes() 
					send_to_nbrs(nbrs)
				else:
					print "No new update"
				
				lock.release()

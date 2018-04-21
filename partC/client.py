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

def set_init_graph(label, weight_file, topo_file):
	global curr_table
	
	path = './' + label + '/weights'
	g = Graph()
	g.init_config(label, weight_file, topo_file)
	g.bellman_on_all()
	curr_table = g


def send_to_nbrs(nbrs, topoUpdate):
	global curr_table
	for each in nbrs:
		nbr = peerSock()
		print "Sending distance vector to " + each
		nbr.connect(each)
		nbr.sendmsg(curr_table.get_routes(), topoUpdate)


def check_weight_update(label, weight_file, topo_file, nbrs):
	global curr_table
	print "Checking for Topology Changes"
	path = './' + label + '/weights'
	update = Graph()
	update.init_config(label, weight_file, topo_file)
	lock.acquire()
	if curr_table.serialize != update.serialize:
		print "Topology update detected. Rerouting..."
		update.bellman_on_all()
		curr_table = copy.deepcopy(update)
		print curr_table.get_routes()
		send_to_nbrs(nbrs, True)
	lock.release()
	threading.Timer(period, check_weight_update, [label, weight_file, topo_file, nbrs]).start() # Trigger Periodic Check
		

if __name__ == "__main__":
	global curr_table

	if len(sys.argv) < 3:
		print "Usage args: <Node-Label> [List of IPs of Neighbours]"
		sys.exit(0)
	label = sys.argv[1]
	
	set_init_graph(label, 'weights', 'nodes') # Get Initial Graph(only neighbours)
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
				send_to_nbrs(nbrs, False)
				if not timer_init:
					check_weight_update(label, 'weights', 'nodes', nbrs)
					timer_init = True
			elif conn == server:
				cli, addr = conn.accept()
				obj =  json.loads(cli.recv(1024))
				rcvd_route = obj['data']
				topo_update = obj['topoUpdate']
				lock.acquire()
				old_routes = copy.deepcopy(curr_table.get_routes())
				print old_routes
				for src in rcvd_route:
					for dst in rcvd_route[src]:
						if topo_update or float(old_routes[src][dst]) > float(rcvd_route[src][dst]):
							old_routes[src][dst] = rcvd_route[src][dst]
				if old_routes != curr_table.get_routes():
					print "Routing Table updated"
					curr_table.set_routes(old_routes)
					curr_table.bellman_on_all()
					print curr_table.get_routes() 
					send_to_nbrs(nbrs, False)
				else:
					print "No new update"
				lock.release()

import os
import errno
import socket
import selectors2 as selectors
import json

PORT = 9020

class Edge:

        def __init__(self, src, dst, weight):
                self.src = src
                self.dst = dst
                self.w = weight


        def __repr__(self):
                return 'Edge(%s->%s, %s)' % (self.src, self.dst, self.w)


        def set_weight(self, w):
                self.w = w


        def get_weight(self, w):
                return self.w


class Graph:
	"""Only a Connected Graph at the moment"""

	def __init__(self):
		self.routes = {}
		self.serialize = ""
		self.edges = []


	def __repr__(self):

		buff = str(self.routes.keys())
		buff += "\n----\n"
		for each in self.routes:
			buff += str(each) + " -> " + str(self.routes[each]) + "\n"
		buff += "----"
		return buff


	def get_labels(self):
		return self.routes.keys()


	def add_route(self, src, dst, w):
		self.routes[src][dst] = float(w)
		return self.routes

	def update_edges_from_routes(self):
		self.edges = []
		for node in self.routes:
			for dst in self.routes[node]:
				self.edges.append(Edge(node, dst, float(self.routes[node][dst])))

	def read_graph_from_file(self, fname):	
		with open(fname, 'r') as fp:
			for each in fp.readlines():
				node = each.split(' ')
				node = map(lambda s: s.rstrip(), node)
				self.routes[node[0]][node[1]] = float(node[2])
				self.routes[node[1]][node[0]] = float(node[2])		

	def get_routes(self, path=None):
		return self.routes

	
	def set_routes(self, routes):
		self.routes = routes


	def bellman_on_src(self, src):
		self.update_edges_from_routes()
		print len(self.edges)
		if not len(self.v):
			return "Please initialize Graph lables"
		dist = {}
		dist = dist.fromkeys(self.v, float("Inf"))
		dist[src] = float(0)
		for i in range(len(self.v) - 1):
			for edge in self.edges:
				if dist[edge.src] != float("Inf") and dist[edge.src] + edge.w < dist[edge.dst]:
					dist[edge.dst] = float(dist[edge.src] + edge.w)
		self.routes[src] = dist
		return dist


	def bellman_on_all(self):
		dist = {}
		self.update_edges_from_routes()
		for each in self.v:
			dist[each] = self.bellman_on_src(each)

		self.routes = dist
		return dist
	
	# Helper Functions
	def create_config(self, src, edge, filename):
		if not os.path.exists(os.path.dirname(filename)):
			os.makedirs(os.path.dirname(filename))
		try:	
			with open(filename, "r") as f:
				if edge in f.readlines():
					return
		except IOError:
			print "Creating router config for %s..." % (src)
			pass
		with open(filename, "a") as f:
			f.write(edge)


	def init_config(self, label, fname, nname):
		filename = "./" + label + "/weights"
		direct_conn = [label]
		with open(fname, 'r') as fp:
			for each in fp.readlines():
				self.serialize += each
				edge = each.split(' ')
				if label == edge[0]:
					direct_conn.append(edge[1])
					self.create_config(label, each, filename)
				elif label == edge[1]:
					direct_conn.append(edge[0])
					self.create_config(label, each, filename)
		direct_conn = list(set(direct_conn))

		with open(nname, 'r') as fp:
			for each in fp.readlines():
				if each.rstrip() not in direct_conn:
					inf_route = label + " " + each.rstrip() + " Inf\n"
					self.create_config(label, inf_route, filename)
					direct_conn.append(each.rstrip())
		
		for node in direct_conn: #direct_conn now contains all nodes
			dist = {}
			self.routes[node] = dist.fromkeys(direct_conn, float("Inf")) # Initialize all distances to Inf
		self.v = direct_conn # All vertices in the topology
		self.read_graph_from_file(filename)

class peerSock:
	
	def __init__(self, sock=None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock
	
	def connect(self, host, port=None):
		if port is None:
			port = PORT
		self.sock.connect((host, port))
		print "Connected to %s:%s" % (host, port)
	
	def sendmsg(self, msg, topoUpdate):
		obj = json.dumps({'data': msg, 'topoUpdate': topoUpdate})
		sent = self.sock.send(obj.encode('utf-8'))
		if sent == 0:
			print "Connection Broken. Couldn't send"
		return sent
	
	def recvmsg(self):
		buff = self.sock.recv(1024)
		if buff == '':
			print "Connection Broken. Couldn't Recv"
		obj = json.loads(buff)
		return buff['data'], buff['topoUpdate']
	
	def close(self):
		return self.sock.close()


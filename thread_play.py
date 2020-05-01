from threading import Thread
import multiprocessing as mp

class TestServer:
	def __init__(self, conn):
		self.conn = conn
		self.stopped = False

	def run(self):
		# conn_a = self.pipe.a
		while not self.stopped:
			request = self.conn.recv()
			operation = request['operation']
			print('received request for %s' % operation)

			response = {
				'operation': operation,
			}

			# would execute operation here
			result = {}
			print('executing operation', operation)
			if operation == 'stop':
				self.stopped = True
				result = { 'status': True}

			else:
				# Dummy operation call
				print('executing', operation)
				result = {'status': True}

			response['status'] = result['status']
			print('sending operation result')

			self.conn.send(response)

class DoRequest(Thread):
	def __init__(self, connection, request):
		Thread.__init__(self)
		self.connection = connection
		self.request = request
		self.result = {}

	def run(self):
		print('DoRequest - conn %d:' % hash(self.connection), self.request, id(self.request))

		self.connection.send(self.request)
		response = self.connection.recv()
		print('DoRequest response', response)
		self.result['status'] = response['status']

	def get_result(self):
		return self.result

class TestPipe():
	def __init__(self):
		(self.client_side, self.server_side) = mp.Pipe()

	def close(self):
		self.client_side.close()
		self.server_side.close()

# class TestPipe():
#     def __init__(self, server_side, client_side):
#         self.server_side = server_side
#         self.client_side = client_side

#     def close(self):
#         self.server_side.close()
#         self.client_side.close()

def start_server(conn):
	server = TestServer(conn)
	try:
		server.run()
	except KeyboardInterrupt:
		print('server got keyboard interrupt')

if __name__ == '__main__':

	pipe = TestPipe()

	server = mp.Process(target = start_server, args=(pipe.server_side, ))
	server.start()

	request = {'operation': 'nothing'}
	thread = DoRequest(pipe.client_side, dict(request))
	thread.start()
	thread.join()
	result = thread.get_result()

	print('result:', result)

	request = {'operation': 'stop'}
	thread = DoRequest(pipe.client_side, dict(request))
	thread.start()
	thread.join()
	result = thread.get_result()

	pipe.close()

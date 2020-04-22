from threading import Thread
import multiprocessing as mp

class TestServer:
	def __init__(self, pipe):
		self.pipe = pipe
		self.stopped = False
	def run(self):
		# conn_a = self.pipe.a
		conn_b = self.pipe.b
		while not self.stopped:
			request = conn_b.recv()
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

			conn_b.send(response)

class DoRequest(Thread):
	def __init__(self, connection, request):
		Thread.__init__(self)
		self.connection = connection
		self.request = request
		self.result = None

	def run(self):
		print('DoRequest', self.connection, self.request)

		self.result = self.connection.send(self.request)

	def get_result(self):
		return self.result

class TestPipe():
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def close(self):
        self.a.close()
        self.b.close()

def start_server(pipe):
	server = TestServer(pipe)
	try:
		server.run()
	except KeyboardInterrupt:
		print('server got keyboard interrupt')

if __name__ == '__main__':

	(a, b) = mp.Pipe()
	pipe = TestPipe(a, b)
	conn = pipe.a

	server = mp.Process(target = start_server, args=(pipe, ))
	server.start()

	request = {'operation': 'nothing'}
	thread = DoRequest(conn, request)
	thread.start()
	thread.join()
	result = thread.get_result()

	print('result:', result)

	request = {'operation': 'stop'}
	thread = DoRequest(conn, request)
	thread.start()
	thread.join()
	result = thread.get_result()

	pipe.close()

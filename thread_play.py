from threading import Thread

class DoRequest(Thread):
	def __init__(self, target_id, connection, request):
		Thread.__init__(self)
		self.target_id = target_id
		self.connection = connection
		self.request = request
		self.result = None

	def run(self):
		print('DoRequest', self.target_id, self.connection, self.request)
		self.result = self.request

	def get_result(self):
		return self.result

if __name__ == '__main__':
	request = {'operation': 'nothing'}
	thread = DoRequest(1, 'conn', request)
	thread.start()
	thread.join()
	result = thread.get_result()

	print('result:', result)


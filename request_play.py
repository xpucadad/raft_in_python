import sys
import random
import queue
import time
import multiprocessing as mp

SERVER_COUNT = 2
MIN_TIMEOUT = 1
MAX_TIMEOUT = 2

class Server:
    def __init__(self, server_id, queues):
        self.server_id = server_id
        self.queues = queues
        self.input_queue = queues[server_id]

        self.stopped = False



    def run(self):
        response = {}
        while not self.stopped:
            timeout = random.randint(MIN_TIMEOUT, MAX_TIMEOUT)
            try:
                request = self.input_queue.get(True, timeout)
                print('server %d got request' % self.server_id, request)
            except queue.Empty:
                print('server_id %d timed out waiting for request' % self.server_id)
                continue

            if self.server_id != request['to']:
                raise IndexError
                continue

            operation = request['operation']
            reply_queue = self.queues[request['from']]

            response = {'from': self.server_id, 'to': request['from']}

            if operation == 'stop':
                self.stopped = True

            response['operation'] = request['operation']
            response['status'] = True

            reply_queue.put(response)

        print('server_id %d stopped' % self.server_id)

class Request:
    def __init__(self, queues):
        self.queues = queues

    def send(self, source_id, target_id, message):
        message['from'] = source_id
        message['to'] = target_id
        self.queues[target_id].put(message)
        response = None

        while response == None:
            try:
                response = self.queues[source_id].get(False)
            except queue.Empty:
                response = None

        return response

def start_server(server_id, queues):
        server = Server(server_id, queues)
        server.run()


if __name__ == '__main__':

    queues = []

    for i in range(SERVER_COUNT+1):
        queues.append(mp.Queue())


    processes = []
    for id in range(SERVER_COUNT):
        processes.append(
            mp.Process(target=start_server, args=(id, queues))
        )

    for p in processes:
        p.start()

    my_id = SERVER_COUNT
    r = Request(queues)
    for i in range(SERVER_COUNT):
        message = {'operation': 'operation %d'%i}
        response = r.send(my_id, i, message)
        print('response from %d' % i, response)

    time.sleep(3)

    message['operation'] = 'stop'
    for i in range(SERVER_COUNT):
        response = r.send(my_id, i, message)
        print('response from %d' % i, response)

    for q in queues:
        q.close()
        q.join_thread()

    for p in processes:
        p.join()

'''
Will implement the Raft protocol.
'''
import sys
import random
from xmlrpc.server import SimpleXMLRPCServer
#from xmlrpc.server import SimpleXMLRPCServerHandler
from server_state import *

class MyRPCServer(SimpleXMLRPCServer):

    def __init__(self, server_id):
        self.server_id = server_id
        self.port = server_id + 8000
        super().__init__(('localhost', self.port))
        self.server_role = FOLLOWER
        self.current_term = 0
        self.voted_for = 0
        self.next_index = 1

        self.commit_index = 0
        self.last_applied = 0


    def handle_timeout(self):
        # process depending on current state
        print('Got a timeout!')
        pass

    def run(self):
        while True:
            # self.timeout = random.randrange(.3, .6)
            self.timeout = 5
            self.handle_request()

class RemoteMethods:
    def dump(self, status):
        print('this is the dump method:', status)
        return status

def main(server_id):
    server = MyRPCServer(server_id)
    server.register_introspection_functions()
    server.register_instance(RemoteMethods())
#    server.register_function(AppendEntries)
#    server.register_function(RequestVote)
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nKeyboard interupt recieved; exitting")

# def RequestVote(term, candidate_id, last_log_index, last_log_term):
#     print("RequestVote")
#     return {self.current_term, true}

# def AppendEntries(term, leader_id, prev_log_index, prev_log_term,
#                     entries, leader_commit):
#     server_state = raft_server.server_state
#
#     print("Server state: " + server_names[server_state])
#     print("AppendEntries")
#     print('term: ' + str(term))
#     print('leader_id: ' + str(leader_id))
#     print('prev_log_index: ' + str(prev_log_index))
#     print('prev_log_term: ' + str(prev_log_term))
#     print('entries: ' + str(entries))
#     print('leaderCommit: ' + str(leader_commit))
#
#     if server_state != FOLLOWER:
#         status = False
#
#     if raft_server.server_stane == FOLLOWER:
#         raft_server.current_term = term
#         status = True
#
#     return (raft_server.current_term, status)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Must supply server id")
        exit()

    server_id = int(sys.argv[1])
    main(server_id)

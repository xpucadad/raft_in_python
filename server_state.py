from pymongo import MongoClient

FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

RoleNames = ['Follower', 'Candidate', 'Leader']

class PersistedState():

    def __init__(self, server_id):
        self.server_id = server_id
        self.mongo_client = MongoClient('localhost:27017')
        self.db = self.mongo_client.raft
        self.key = {'server_id': server_id}

    def get_state(self):
        state = self.db.ServerState.find_one(self.key)
        if state == None:
            state = {
                'server_id': self.server_id,
                'current_term': 0,
                'voted_for': 0
            }
            self.db.ServerState.insert_one(state)
        return state

    def set_state(self, p_state):
        result = self.db.ServerState.update_one(
            self.key,
            {'$set' : p_state},
            True
        )
        return p_state

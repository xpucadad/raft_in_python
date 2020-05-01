from pymongo import MongoClient

FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

RoleNames = ['Follower', 'Candidate', 'Leader']

class PersistedState():

    def __init__(self, node_id):
        self.node_id = node_id
        try:
            self.mongo_client = MongoClient('localhost:27017')
        except ServerSelectionTimeoutError as e:
            print('Failed to connect to MongoDb', e)
            raise

        if not self.mongo_client:
            print('Failed to mongo client')

        self.db = self.mongo_client.raft
        self.key = {'node_id': node_id}

    def get_voted_for(self):
        state = self.get_state()
        return state['voted_for']

    def get_current_term(self):
        state = self.get_state()
        return state['current_term']

    def get_state(self):
        state = self.db.NodeState.find_one(self.key)
        if state == None:
            state = {
                'node_id': self.node_id,
                'current_term': 0,
                'voted_for': None
            }
            self.db.NodeState.insert_one(state)
        return state

    def set_voted_for(self, id):
        update = {'voted_for': id}
        return self.set_state(update)

    def set_current_term(self, term):
        update = {'current_term': term}
        return self.set_state(update)

    def set_state(self, p_state):
        result = self.db.NodeState.update_one(
            self.key,
            {'$set' : p_state},
            True
        )
        return p_state

    def _reset(self):
        result = self.db.NodeState.delete_many(self.key)
        return self.get_state()

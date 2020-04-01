from pymongo import MongoClient



FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

StateNames = ['Follower', 'Candidate', 'Leader']

class ServerState():
    database_name = "Raft"
    collection_name = "ServerState"
    def __init__(self, server_id):
        self.server_id = server_id
        self.client = MongoClient('localhost:27017')
        self.db = self.client.RaftServer
        #self.collection = self.db.ServerState

    def persist_dict(self, dict):
        dict["serverId"] = self.server_id
        result = self.db.ServerState.replace_one(
            { "servelId": self.server_id},
            dict,
            True
        )

    

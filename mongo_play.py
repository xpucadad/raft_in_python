from pymongo import MongoClient

state = {}
state["current_term"] = 0
state["voted_for"] = 0
state["server_id"] = 1
state["next_index"] = 1

state["commit_index"] = 0
state["last_applied"] = 0

print(state)

mongo_client = MongoClient('localhost:27017')
db = mongo_client.Raft
key = {"server_id": state["server_id"]}
result = db.State.update_one(key, {'$set' : state }, True)

state = db.State.find(key)[0]
print(state)

state['next_index'] = 2
state['current_term'] = 1
result = db.State.update_one(key, {'$set' : state }, True)

state = db.State.find_one(key)
print(state)

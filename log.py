from pymongo import MongoClient

print("log: Hello, world!")

class Log():
    database_name="Raft"

    def __init__(self):
        self.client = MongoClient('localhost:27017')
        self.db = self.client.log

    def add_entry(serverId, term, nextIndex, newEntry):
        # Get any entry already at the nextIndex
        entry = self.b.Log.find_one(
            {"serverId": serverId,"slot": nextIndex})
        if entry == none:
            self.db.Log.insert_one(
                {
                    "serverId": serverId,
                    "slot": nextIndex,
                    "term": term,
                    "entry": newEntry
                }
            )
            return true
        else:
            return false

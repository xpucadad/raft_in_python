import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')
print(s.add(5, 6))

print(s.system.listMethods())

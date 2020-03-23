import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')
print(s.pow(2, 2))
print(s.add(5, 6))

print(s.system.listMethods())

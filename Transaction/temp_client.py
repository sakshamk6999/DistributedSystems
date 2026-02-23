# from zeep import Client

# client = Client('http://localhost:8000/?wsdl')
# result = client.service.say_hello('saksham')

# # assert result == 62.137
# print(result)

from suds.client import Client
c = Client('http://127.0.0.1:8000/?wsdl', cache=None)
print(c.service.say_hello('punk', 5))
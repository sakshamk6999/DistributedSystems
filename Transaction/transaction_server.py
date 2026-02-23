from spyne import Application, rpc, ServiceBase, Unicode, String
import random
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class BankTransactionService(ServiceBase):
    # We define the input parameters (e.g., card_number, amount) 
    # even if we just return a random result to make it feel like a real bank API.
    @rpc(Unicode, Unicode, _returns=Unicode)
    def process_payment(ctx, card_number, amount):
        """
        Emulates a bank transaction.
        Returns 'yes' or 'no' with a 90% probability of 'yes'.
        """
        result = random.choices(['yes', 'no'], weights=[0.9, 0.1], k=1)[0]
        return result

# Using a more descriptive namespace for the bank
application = Application(
    [BankTransactionService], 
    tns='bank.system.emulation',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

wsgi_application = WsgiApplication(application)

if __name__ == '__main__':
    import logging
    from wsgiref.simple_server import make_server

    logging.basicConfig(level=logging.INFO)
    
    # Listen on 0.0.0.0 so other VMs in your GCP network can reach it
    host = '0.0.0.0'
    port = 8000
    
    server = make_server(host, port, wsgi_application)
    logging.info(f"Bank SOAP service listening on http://{host}:{port}")
    logging.info(f"WSDL available at: http://<VM_EXTERNAL_IP>:{port}/?wsdl")
    server.serve_forever()
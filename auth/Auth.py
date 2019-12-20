from flask_restful import Resource, Api
from gevent.pywsgi import WSGIServer
from flask import Flask
import logging
from flask_mail import Mail

app = Flask(__name__)
api = Api(app)
Mail(app)

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s\t %(module)-s\t msg="%(message)s"',
                    datefmt='%a, %d %b %Y %H:%M:%S', filemode='w')

logger = logging.getLogger('REST API')

if __name__ == '__main__':
    logger.info('Auth REST-API')

    app.secret_key = '123'
    # Indexing
    from auth_logic import auth_logic

    app.register_blueprint(auth_logic)

    # Start server
    http_server = WSGIServer(('', 2000), app)
    http_server.serve_forever()

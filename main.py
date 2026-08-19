import falcon
from wsgiref.simple_server import make_server

from middleware.cors import CORSMiddleware
from routes import add_routes


def create_app():
    app = falcon.App(middleware=[CORSMiddleware()])
    add_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    with make_server("", 8000, app) as httpd:
        print("Backend jalan di http://localhost:8000 ...")
        httpd.serve_forever()
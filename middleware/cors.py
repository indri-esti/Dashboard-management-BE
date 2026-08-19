class CORSMiddleware:

    def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header(
            "Access-Control-Allow-Origin",
            "http://localhost:5173"
        )
        resp.set_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        resp.set_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        resp.set_header(
            "Access-Control-Allow-Credentials",
            "true"
        )
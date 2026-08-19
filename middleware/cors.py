class CORSMiddleware:

    def process_request(self, req, resp):
        # Menangani preflight request dari browser
        if req.method == "OPTIONS":
            resp.status = "204 No Content"

    def process_response(self, req, resp, resource, req_succeeded):
        origin = req.get_header("Origin")

        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://dashboard-management-tau.vercel.app"
        ]

        if origin in allowed_origins:
            resp.set_header(
                "Access-Control-Allow-Origin",
                origin
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
import falcon
from database import get_connection


class RoleResource:

    def on_get(self, req, resp):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    id_role,
                    nama_role,
                    deskripsi
                FROM role
                ORDER BY id_role
            """)

            roles = cursor.fetchall()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "data": roles
            }

        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "error",
                "message": str(e)
            }

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()
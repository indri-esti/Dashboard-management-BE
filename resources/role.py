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

    def on_post(self, req, resp):
        conn = None
        cursor = None

        try:
            data = req.media or {}

            nama_role = str(data.get("nama_role", "")).strip()
            deskripsi = str(data.get("deskripsi", "")).strip()

            if not nama_role:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama role wajib diisi."
                }
                return

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id_role
                FROM role
                WHERE LOWER(nama_role) = LOWER(%s)
                LIMIT 1
                """,
                (nama_role,)
            )

            if cursor.fetchone():
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Nama role sudah terdaftar."
                }
                return

            cursor.execute(
                """
                INSERT INTO role (nama_role, deskripsi)
                VALUES (%s, %s)
                """,
                (nama_role, deskripsi)
            )

            conn.commit()

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "message": "Role berhasil ditambahkan.",
                "data": {
                    "id_role": cursor.lastrowid,
                    "nama_role": nama_role,
                    "deskripsi": deskripsi
                }
            }

        except Exception as e:
            if conn:
                conn.rollback()

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

    def on_delete(self, req, resp, id_role):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id_role
                FROM role
                WHERE id_role = %s
                LIMIT 1
                """,
                (id_role,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "Role tidak ditemukan."
                }
                return

            cursor.execute(
                "DELETE FROM role WHERE id_role = %s",
                (id_role,)
            )

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "Role berhasil dihapus."
            }

        except Exception as e:
            if conn:
                conn.rollback()

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
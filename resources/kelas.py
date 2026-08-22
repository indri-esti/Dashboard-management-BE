import falcon
from database import get_connection


class KelasResource:

    def on_get(self, req, resp, kelas_id=None):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            if kelas_id is not None:
                cursor.execute("""
                    SELECT
                        k.id_kelas,
                        k.nama,
                        k.phone,
                        k.email,
                        k.role_id,
                        r.nama_role AS roles,
                        k.status,
                        k.created_at,
                        k.alasan_non_active
                    FROM kelas k
                    LEFT JOIN role r
                        ON r.id_role = k.role_id
                    WHERE k.id_kelas = %s
                """, (kelas_id,))

                data = cursor.fetchone()

                if not data:
                    resp.status = falcon.HTTP_404
                    resp.media = {
                        "status": "error",
                        "message": "Data kelas tidak ditemukan."
                    }
                    return
            else:
                cursor.execute("""
                    SELECT
                        k.id_kelas,
                        k.nama,
                        k.phone,
                        k.email,
                        k.role_id,
                        r.nama_role AS roles,
                        k.status,
                        k.created_at,
                        k.alasan_non_active
                    FROM kelas k
                    LEFT JOIN role r
                        ON r.id_role = k.role_id
                    ORDER BY k.created_at DESC, k.id_kelas DESC
                """)

                data = cursor.fetchall()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "data": data
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

            nama = str(data.get("nama", "")).strip()
            phone = str(data.get("phone", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            role_id = data.get("role_id")

            if not nama:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama wajib diisi."
                }
                return

            if not phone:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nomor handphone wajib diisi."
                }
                return

            if not email:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Email wajib diisi."
                }
                return

            if role_id in (None, ""):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role wajib dipilih."
                }
                return

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_role FROM role WHERE id_role = %s",
                (role_id,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role tidak ditemukan."
                }
                return

            cursor.execute(
                "SELECT id_kelas FROM kelas WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email anggota kelas sudah terdaftar."
                }
                return

            cursor.execute("""
                INSERT INTO kelas (
                    nama,
                    phone,
                    email,
                    role_id,
                    status,
                    alasan_non_active
                )
                VALUES (%s, %s, %s, %s, 'active', '')
            """, (
                nama,
                phone,
                email,
                role_id
            ))

            conn.commit()

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "message": "Data kelas berhasil ditambahkan.",
                "id_kelas": cursor.lastrowid
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

    def on_put(self, req, resp, kelas_id):
        conn = None
        cursor = None

        try:
            data = req.media or {}

            nama = str(data.get("nama", "")).strip()
            phone = str(data.get("phone", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            role_id = data.get("role_id")

            status = str(data.get("status", "active")).strip().lower()
            if status not in ("active", "non active"):
                status = "active"

            alasan = str(data.get("alasan_non_active", "")).strip()

            if not nama or not phone or not email:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama, nomor handphone, dan email wajib diisi."
                }
                return

            if role_id in (None, ""):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role wajib dipilih."
                }
                return

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT id_kelas FROM kelas WHERE id_kelas = %s",
                (kelas_id,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "Data kelas tidak ditemukan."
                }
                return

            cursor.execute(
                "SELECT id_role FROM role WHERE id_role = %s",
                (role_id,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role tidak ditemukan."
                }
                return

            cursor.execute(
                """
                SELECT id_kelas
                FROM kelas
                WHERE email = %s
                  AND id_kelas <> %s
                """,
                (email, kelas_id)
            )

            if cursor.fetchone():
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email anggota kelas sudah digunakan oleh data lain."
                }
                return

            cursor.execute("""
                UPDATE kelas
                SET
                    nama = %s,
                    phone = %s,
                    email = %s,
                    role_id = %s,
                    status = %s,
                    alasan_non_active = %s
                WHERE id_kelas = %s
            """, (
                nama,
                phone,
                email,
                role_id,
                status,
                alasan if status == "non active" else "",
                kelas_id
            ))

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "Data kelas berhasil diperbarui."
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

    def on_delete(self, req, resp, kelas_id):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id_kelas FROM kelas WHERE id_kelas = %s",
                (kelas_id,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "Data kelas tidak ditemukan."
                }
                return

            cursor.execute(
                "DELETE FROM kelas WHERE id_kelas = %s",
                (kelas_id,)
            )

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "Data kelas berhasil dihapus."
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


class ReactivateKelasResource:

    def on_put(self, req, resp, kelas_id):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id_kelas FROM kelas WHERE id_kelas = %s",
                (kelas_id,)
            )

            if not cursor.fetchone():
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "Data kelas tidak ditemukan."
                }
                return

            cursor.execute("""
                UPDATE kelas
                SET
                    status = 'active',
                    alasan_non_active = ''
                WHERE id_kelas = %s
            """, (kelas_id,))

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "Data kelas berhasil diaktifkan kembali."
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
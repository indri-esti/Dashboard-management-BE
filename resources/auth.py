import falcon
from database import get_connection


class LoginResource:

    def on_get(self, req, resp):
        resp.media = {
            "status": "success",
            "message": "Login API tersedia. Gunakan method POST untuk login."
        }

    def on_post(self, req, resp):
        conn = None
        cursor = None

        try:
            data = req.media or {}

            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Email dan password wajib diisi"
                }
                return

            email = email.strip().lower()
            password = str(password).strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =========================================================
            # 1. CEK USER YANG DIBUAT MELALUI USER MANAGEMENT
            # =========================================================
            cursor.execute("""
                SELECT
                    u.id_user,
                    u.title,
                    u.nama,
                    u.phone,
                    u.email,
                    u.password,
                    u.tanggal_lahir,
                    u.status,
                    u.alasan_non_active,
                    u.role_id,
                    r.nama_role AS role,
                    u.created_at
                FROM `user` u
                LEFT JOIN role r
                    ON u.role_id = r.id_role
                WHERE LOWER(u.email) = %s
                LIMIT 1
            """, (email,))

            user = cursor.fetchone()

            if user:

                # Cek password
                if str(user["password"]).strip() != password:
                    resp.status = falcon.HTTP_401
                    resp.media = {
                        "status": "error",
                        "message": "Email atau password salah"
                    }
                    return

                # Cek status
                if user["status"] and user["status"].lower() != "active":
                    resp.status = falcon.HTTP_403
                    resp.media = {
                        "status": "error",
                        "message": "Akun tidak aktif"
                    }
                    return

                # Password jangan dikirim ke frontend
                user.pop("password", None)

                if user.get("created_at"):
                    user["created_at"] = user["created_at"].isoformat()

                if user.get("tanggal_lahir"):
                    user["tanggal_lahir"] = user["tanggal_lahir"].isoformat()

                resp.status = falcon.HTTP_200
                resp.media = {
                    "status": "success",
                    "message": "Login berhasil",
                    "data": user
                }
                return

            # =========================================================
            # 2. KALAU TIDAK ADA DI USER, CEK AUTH_USER
            #    AUTH_USER = AKUN HASIL REGISTER
            # =========================================================
            cursor.execute("""
                SELECT
                    id_auth,
                    nama,
                    email,
                    password,
                    status,
                    created_at
                FROM auth_user
                WHERE LOWER(email) = %s
                LIMIT 1
            """, (email,))

            auth_user = cursor.fetchone()

            if not auth_user:
                resp.status = falcon.HTTP_401
                resp.media = {
                    "status": "error",
                    "message": "Email atau password salah"
                }
                return

            # Cek password
            if str(auth_user["password"]).strip() != password:
                resp.status = falcon.HTTP_401
                resp.media = {
                    "status": "error",
                    "message": "Email atau password salah"
                }
                return

            # Cek status
            if (
                auth_user["status"]
                and auth_user["status"].lower() != "active"
            ):
                resp.status = falcon.HTTP_403
                resp.media = {
                    "status": "error",
                    "message": "Akun tidak aktif"
                }
                return

            # =========================================================
            # AKUN REGISTER = MEMBER
            # =========================================================
            member_role_id = None
            member_role_name = "Member"

            cursor.execute("""
                SELECT
                    id_role,
                    nama_role
                FROM role
                WHERE LOWER(nama_role) = 'member'
                LIMIT 1
            """)

            member_role = cursor.fetchone()

            if member_role:
                member_role_id = member_role["id_role"]
                member_role_name = member_role["nama_role"]

            # Buat response yang bentuknya tetap mirip
            # dengan response login dari tabel user.
            login_data = {
                "id_auth": auth_user["id_auth"],
                "id_user": None,
                "title": None,
                "nama": auth_user["nama"],
                "phone": None,
                "email": auth_user["email"],
                "tanggal_lahir": None,
                "status": auth_user["status"],
                "alasan_non_active": None,
                "role_id": member_role_id,
                "role": member_role_name,
                "created_at": (
                    auth_user["created_at"].isoformat()
                    if auth_user.get("created_at")
                    else None
                )
            }

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "Login berhasil",
                "data": login_data
            }

        except Exception as e:
            print("ERROR LOGIN:", str(e))

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


class RegisterResource:

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "success",
            "message": "Register API tersedia. Gunakan method POST untuk membuat akun."
        }

    def on_post(self, req, resp):
        conn = None
        cursor = None

        try:
            data = req.media or {}

            nama = data.get("nama")
            email = data.get("email")
            password = data.get("password")

            if not nama or not email or not password:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama, email, dan password wajib diisi"
                }
                return

            nama = nama.strip()
            email = email.strip().lower()
            password = str(password).strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =========================================================
            # CEK EMAIL DI AUTH_USER
            # =========================================================
            cursor.execute("""
                SELECT
                    id_auth
                FROM auth_user
                WHERE LOWER(email) = %s
                LIMIT 1
            """, (email,))

            if cursor.fetchone():
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email sudah terdaftar"
                }
                return

            # =========================================================
            # CEK JUGA EMAIL DI USER
            #
            # Supaya akun Register tidak memakai email yang sudah
            # digunakan oleh Admin/User Management.
            # =========================================================
            cursor.execute("""
                SELECT
                    id_user
                FROM `user`
                WHERE LOWER(email) = %s
                LIMIT 1
            """, (email,))

            if cursor.fetchone():
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email sudah terdaftar"
                }
                return

            # =========================================================
            # REGISTER MASUK KE AUTH_USER
            #
            # TIDAK LAGI INSERT KE TABEL `user`
            # =========================================================
            cursor.execute("""
                INSERT INTO auth_user
                (
                    nama,
                    email,
                    password,
                    status,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'active',
                    NOW()
                )
            """, (
                nama,
                email,
                password
            ))

            conn.commit()

            auth_id = cursor.lastrowid

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "message": "Akun berhasil dibuat sebagai Member",
                "data": {
                    "id_auth": auth_id,
                    "nama": nama,
                    "email": email,
                    "status": "active",
                    "role": "Member"
                }
            }

        except Exception as e:
            if conn:
                conn.rollback()

            print("ERROR REGISTER:", str(e))

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
import falcon
from database import get_connection


class UserResource:

    def _format_tanggal_lahir(self, tanggal):
        """
        Format tanggal dari database:
        2026-08-18 -> 18/08/2026
        """
        if not tanggal:
            return None

        try:
            if hasattr(tanggal, "strftime"):
                return tanggal.strftime("%d/%m/%Y")

            tanggal = str(tanggal)

            if len(tanggal) >= 10:
                bagian = tanggal[:10].split("-")

                if len(bagian) == 3:
                    tahun, bulan, hari = bagian
                    return f"{hari}/{bulan}/{tahun}"

            return tanggal

        except Exception:
            return str(tanggal)

    def _get_user(self, user_id):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    u.id_user,
                    u.title,
                    u.nama,
                    u.phone,
                    u.email,
                    u.tanggal_lahir,
                    u.status,
                    u.alasan_non_active,
                    u.role_id,
                    r.nama_role AS role,
                    u.created_at
                FROM `user` u
                LEFT JOIN role r
                    ON u.role_id = r.id_role
                WHERE u.id_user = %s
                LIMIT 1
            """, (user_id,))

            user = cursor.fetchone()

            if user:
                if user.get("created_at"):
                    user["created_at"] = user["created_at"].isoformat()

                if user.get("tanggal_lahir"):
                    user["tanggal_lahir"] = self._format_tanggal_lahir(
                        user["tanggal_lahir"]
                    )

                if user.get("alasan_non_active") is None:
                    user["alasan_non_active"] = ""

            return user

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def on_get(self, req, resp, user_id=None):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =====================================================
            # GET DETAIL USER
            # GET /api/users/{id}
            # =====================================================

            if user_id is not None:

                cursor.execute("""
                    SELECT
                        u.id_user,
                        u.title,
                        u.nama,
                        u.phone,
                        u.email,
                        u.tanggal_lahir,
                        u.status,
                        u.alasan_non_active,
                        u.role_id,
                        r.nama_role AS role,
                        u.created_at
                    FROM `user` u
                    LEFT JOIN role r
                        ON u.role_id = r.id_role
                    WHERE u.id_user = %s
                    LIMIT 1
                """, (user_id,))

                user = cursor.fetchone()

                if not user:
                    resp.status = falcon.HTTP_404
                    resp.media = {
                        "status": "error",
                        "message": "User tidak ditemukan"
                    }
                    return

                if user.get("created_at"):
                    user["created_at"] = user["created_at"].isoformat()

                if user.get("tanggal_lahir"):
                    user["tanggal_lahir"] = self._format_tanggal_lahir(
                        user["tanggal_lahir"]
                    )

                if user.get("alasan_non_active") is None:
                    user["alasan_non_active"] = ""

                resp.status = falcon.HTTP_200
                resp.media = {
                    "status": "success",
                    "data": user
                }
                return

            # =====================================================
            # GET SEMUA USER
            # GET /api/users
            # =====================================================

            cursor.execute("""
                SELECT
                    u.id_user,
                    u.title,
                    u.nama,
                    u.phone,
                    u.email,
                    u.tanggal_lahir,
                    u.status,
                    u.alasan_non_active,
                    u.role_id,
                    r.nama_role AS role,
                    u.created_at
                FROM `user` u
                LEFT JOIN role r
                    ON u.role_id = r.id_role
                ORDER BY u.id_user DESC
            """)

            users = cursor.fetchall()

            for user in users:

                if user.get("created_at"):
                    user["created_at"] = user["created_at"].isoformat()

                if user.get("tanggal_lahir"):
                    user["tanggal_lahir"] = self._format_tanggal_lahir(
                        user["tanggal_lahir"]
                    )

                # Pastikan alasan selalu dikirim ke frontend
                if user.get("alasan_non_active") is None:
                    user["alasan_non_active"] = ""

                else:
                    user["alasan_non_active"] = str(
                        user["alasan_non_active"]
                    ).strip()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "data": users
            }

        except Exception as e:
            print("ERROR GET USERS:", str(e))

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

            title = data.get("title")
            nama = data.get("nama")
            phone = data.get("phone")
            email = data.get("email")
            tanggal_lahir = data.get("tanggal_lahir")
            password = data.get("password")
            role_id = data.get("role_id")

            if not nama or not email or not password:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama, email, dan password wajib diisi"
                }
                return

            nama = nama.strip()
            email = email.strip().lower()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =====================================================
            # CEK EMAIL
            # =====================================================

            cursor.execute("""
                SELECT id_user
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

            # =====================================================
            # DEFAULT ROLE
            # =====================================================

            if not role_id:
                cursor.execute("""
                    SELECT id_role
                    FROM role
                    ORDER BY id_role
                    LIMIT 1
                """)

                role = cursor.fetchone()

                if role:
                    role_id = role["id_role"]

            else:
                # =====================================================
                # VALIDASI ROLE_ID VALID
                # =====================================================

                cursor.execute("""
                    SELECT id_role
                    FROM role
                    WHERE id_role = %s
                    LIMIT 1
                """, (role_id,))

                if not cursor.fetchone():
                    resp.status = falcon.HTTP_400
                    resp.media = {
                        "status": "error",
                        "message": "Role tidak ditemukan/tidak valid"
                    }
                    return

            # =====================================================
            # INSERT USER
            # =====================================================

            cursor.execute("""
                INSERT INTO `user`
                (
                    title,
                    nama,
                    phone,
                    email,
                    tanggal_lahir,
                    password,
                    status,
                    role_id,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'active',
                    %s,
                    NOW()
                )
            """, (
                title,
                nama,
                phone,
                email,
                tanggal_lahir,
                password,
                role_id
            ))

            conn.commit()

            user_id = cursor.lastrowid

            user = self._get_user(user_id)

            resp.status = falcon.HTTP_201
            resp.media = {
                "status": "success",
                "message": "User berhasil dibuat",
                "data": user
            }

        except Exception as e:
            if conn:
                conn.rollback()

            print("ERROR CREATE USER:", str(e))

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

    def on_put(self, req, resp, user_id):
        conn = None
        cursor = None

        try:
            data = req.media or {}

            title = data.get("title")
            nama = data.get("nama")
            phone = data.get("phone")
            email = data.get("email")
            tanggal_lahir = data.get("tanggal_lahir")
            role_id = data.get("role_id")
            status = data.get("status")

            # =====================================================
            # VALIDASI DATA DASAR
            # =====================================================

            if nama is None or email is None:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama dan email wajib diisi"
                }
                return

            nama = str(nama).strip()
            email = str(email).strip().lower()

            if not nama:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Nama wajib diisi"
                }
                return

            if not email:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Email wajib diisi"
                }
                return

            # =====================================================
            # NORMALISASI STATUS
            # =====================================================

            status = str(status or "active").strip()

            # =====================================================
            # AMBIL ALASAN NON ACTIVE
            # =====================================================

            alasan_non_active = (
                data.get("alasan_non_active")
                if data.get("alasan_non_active") is not None
                else data.get("alasan_nonactive")
                if data.get("alasan_nonactive") is not None
                else data.get("alasanNonActive")
                if data.get("alasanNonActive") is not None
                else data.get("reason")
                if data.get("reason") is not None
                else ""
            )

            alasan_non_active = str(alasan_non_active).strip()

            # =====================================================
            # VALIDASI STATUS
            # =====================================================

            if status.lower() == "non active" and not alasan_non_active:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Alasan non active wajib diisi"
                }
                return

            # Kalau active, alasan dihapus
            if status.lower() == "active":
                alasan_non_active = None

            # =====================================================
            # NORMALISASI TANGGAL
            # =====================================================
            # Mendukung:
            # 18/08/2026
            # 2026-08-18
            # =====================================================

            if tanggal_lahir:
                tanggal_lahir = str(tanggal_lahir).strip()

                if "/" in tanggal_lahir:
                    bagian_tanggal = tanggal_lahir.split("/")

                    if len(bagian_tanggal) == 3:
                        hari = bagian_tanggal[0].zfill(2)
                        bulan = bagian_tanggal[1].zfill(2)
                        tahun = bagian_tanggal[2]

                        tanggal_lahir = f"{tahun}-{bulan}-{hari}"

            # =====================================================
            # KONEKSI DATABASE
            # =====================================================

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =====================================================
            # CEK USER
            # =====================================================

            cursor.execute("""
                SELECT
                    id_user,
                    email,
                    nama,
                    title,
                    phone,
                    tanggal_lahir,
                    role_id,
                    status,
                    alasan_non_active
                FROM `user`
                WHERE id_user = %s
                LIMIT 1
            """, (user_id,))

            existing_user = cursor.fetchone()

            if not existing_user:
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "User tidak ditemukan"
                }
                return

            # =====================================================
            # CEK EMAIL USER LAIN
            # =====================================================
            # Email user yang sedang diedit boleh tetap sama.
            # Email hanya ditolak jika dipakai user lain.
            # =====================================================

            cursor.execute("""
                SELECT id_user
                FROM `user`
                WHERE LOWER(TRIM(email)) = %s
                AND id_user <> %s
                LIMIT 1
            """, (email, user_id))

            email_user_lain = cursor.fetchone()

            if email_user_lain:
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email sudah digunakan user lain"
                }
                return

            # =====================================================
            # VALIDASI ROLE
            # =====================================================

            if role_id in (None, "", "null", "undefined"):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role wajib dipilih"
                }
                return

            # Konversi role_id string menjadi integer jika memungkinkan
            try:
                role_id = int(role_id)
            except (ValueError, TypeError):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": "Role yang dipilih tidak valid"
                }
                return

            cursor.execute("""
                SELECT id_role
                FROM role
                WHERE id_role = %s
                LIMIT 1
            """, (role_id,))

            role = cursor.fetchone()

            if not role:
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": (
                        "Role tidak ditemukan/tidak valid. "
                        "Silakan pilih ulang role."
                    )
                }
                return

            # =====================================================
            # UPDATE USER
            # =====================================================

            cursor.execute("""
                UPDATE `user`
                SET
                    title = %s,
                    nama = %s,
                    phone = %s,
                    email = %s,
                    tanggal_lahir = %s,
                    role_id = %s,
                    status = %s,
                    alasan_non_active = %s
                WHERE id_user = %s
            """, (
                title,
                nama,
                phone,
                email,
                tanggal_lahir,
                role_id,
                status,
                alasan_non_active,
                user_id
            ))

            # =====================================================
            # CEK APAKAH DATA BERHASIL DIUPDATE
            # =====================================================

            if cursor.rowcount == 0:
                # Bisa terjadi jika data yang dikirim sama persis.
                # Tetap lanjut karena user memang ada.
                pass

            conn.commit()

            # =====================================================
            # AMBIL DATA TERBARU SETELAH UPDATE
            # =====================================================

            cursor.execute("""
                SELECT
                    u.id_user,
                    u.title,
                    u.nama,
                    u.phone,
                    u.email,
                    u.tanggal_lahir,
                    u.status,
                    u.alasan_non_active,
                    u.role_id,
                    r.nama_role AS role,
                    u.created_at
                FROM `user` u
                LEFT JOIN role r
                    ON u.role_id = r.id_role
                WHERE u.id_user = %s
                LIMIT 1
            """, (user_id,))

            user = cursor.fetchone()

            if user:
                if user.get("created_at"):
                    user["created_at"] = user["created_at"].isoformat()

                if user.get("tanggal_lahir"):
                    user["tanggal_lahir"] = self._format_tanggal_lahir(
                        user["tanggal_lahir"]
                    )

                if user.get("alasan_non_active") is None:
                    user["alasan_non_active"] = ""
                else:
                    user["alasan_non_active"] = str(
                        user["alasan_non_active"]
                    ).strip()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "User berhasil diperbarui",
                "data": user
            }

        except Exception as e:
            if conn:
                conn.rollback()

            print("ERROR UPDATE USER:", str(e))

            error_text = str(e)

            # =====================================================
            # ERROR EMAIL DUPLIKAT
            # =====================================================

            if (
                "duplicate" in error_text.lower()
                and "email" in error_text.lower()
            ):
                resp.status = falcon.HTTP_409
                resp.media = {
                    "status": "error",
                    "message": "Email sudah digunakan user lain"
                }
                return

            # =====================================================
            # ERROR FOREIGN KEY ROLE
            # =====================================================

            if (
                "fk_user_role" in error_text
                or "foreign key constraint" in error_text.lower()
            ):
                resp.status = falcon.HTTP_400
                resp.media = {
                    "status": "error",
                    "message": (
                        "Role yang dipilih tidak valid/tidak ditemukan "
                        "di database. Silakan pilih role lain."
                    )
                }
                return

            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "error",
                "message": error_text
            }

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    def on_delete(self, req, resp, user_id):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =====================================================
            # CEK USER
            # =====================================================

            cursor.execute("""
                SELECT id_user
                FROM `user`
                WHERE id_user = %s
                LIMIT 1
            """, (user_id,))

            user_exists = cursor.fetchone()

            if not user_exists:
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "User tidak ditemukan"
                }
                return

            # =====================================================
            # HAPUS USER PERMANEN
            # =====================================================

            cursor.execute("""
                DELETE FROM `user`
                WHERE id_user = %s
            """, (user_id,))

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "User berhasil dihapus"
            }

        except Exception as e:
            if conn:
                conn.rollback()

            print("ERROR DELETE USER:", str(e))

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


class ReactivateUserResource:

    def on_put(self, req, resp, user_id):
        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # =====================================================
            # CEK USER
            # =====================================================

            cursor.execute("""
                SELECT id_user
                FROM `user`
                WHERE id_user = %s
                LIMIT 1
            """, (user_id,))

            user = cursor.fetchone()

            if not user:
                resp.status = falcon.HTTP_404
                resp.media = {
                    "status": "error",
                    "message": "User tidak ditemukan"
                }
                return

            # =====================================================
            # REACTIVATE
            # =====================================================

            cursor.execute("""
                UPDATE `user`
                SET
                    status = 'active',
                    alasan_non_active = NULL
                WHERE id_user = %s
            """, (user_id,))

            conn.commit()

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "message": "User berhasil diaktifkan kembali"
            }

        except Exception as e:
            if conn:
                conn.rollback()

            print("ERROR REACTIVATE USER:", str(e))

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
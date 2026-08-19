import falcon

from database import get_connection


class ProfileResource:

    # =========================================================
    # ALIAS NAMA KOLOM
    # (kalau nama kolom di database kamu beda, tambahkan di sini)
    # =========================================================

    PHONE_ALIASES = [
        "phone",
        "no_telp",
        "no_hp",
        "telepon",
        "no_telepon",
        "nomor_telepon",
        "nomor_hp",
        "hp",
    ]

    ALAMAT_ALIASES = [
        "alamat",
        "address",
        "alamat_lengkap",
    ]

    CREATED_AT_ALIASES = [
        "created_at",
        "createdAt",
        "tanggal_dibuat",
        "created",
    ]

    TANGGAL_LAHIR_ALIASES = [
        "tanggal_lahir",
        "tgl_lahir",
        "birth_date",
    ]

    # =========================================================
    # HELPER: AMBIL DAFTAR KOLOM YANG BENAR-BENAR ADA DI TABLE
    # (INI YANG MEMPERBAIKI ERROR 500 "Unknown column ...")
    # =========================================================

    def get_table_columns(self, cursor, table_name):
        try:
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            rows = cursor.fetchall()
            existing = {row["Field"] for row in rows}

            print(
                f"Kolom terdeteksi di tabel {table_name}:",
                existing,
                flush=True,
            )

            return existing
        except Exception as e:
            print(
                f"Gagal membaca kolom tabel {table_name}:",
                str(e),
                flush=True,
            )
            return set()

    # =========================================================
    # HELPER: CARI NAMA KOLOM ASLI DARI DAFTAR ALIAS
    # =========================================================

    def resolve_column(self, existing_cols, aliases):
        for name in aliases:
            if name in existing_cols:
                return name

        return None

    # =========================================================
    # HELPER FORMAT TANGGAL
    # =========================================================

    def format_datetime(self, value):
        if value is None:
            return None

        try:
            if hasattr(value, "isoformat"):
                return value.isoformat()

            return str(value)

        except Exception:
            return str(value)

    # =========================================================
    # FORMAT USER MANAGEMENT
    # =========================================================

    def format_user_profile(self, user):

        created_at = self.format_datetime(
            user.get("created_at")
        )

        tanggal_lahir = self.format_datetime(
            user.get("tanggal_lahir")
        )

        return {
            "account_type": "user",

            "id_user": user.get("id_user"),
            "id_auth": None,

            "title": user.get("title"),

            "nama": user.get("nama"),
            "phone": user.get("phone"),
            "email": user.get("email"),
            "alamat": user.get("alamat"),

            "tanggal_lahir": tanggal_lahir,

            "status": user.get("status"),

            "role_id": user.get("role_id"),

            "role": (
                user.get("nama_role")
                or "Administrator"
            ),

            "created_at": created_at,
            "joinDate": created_at,

            "foto": user.get("foto") or "",
        }

    # =========================================================
    # FORMAT AUTH USER
    # =========================================================

    def format_auth_profile(self, user):

        created_at = self.format_datetime(
            user.get("created_at")
        )

        return {
            "account_type": "auth_user",

            "id_user": None,
            "id_auth": user.get("id_auth"),

            "title": None,

            "nama": user.get("nama"),
            "phone": user.get("phone"),
            "email": user.get("email"),
            "alamat": user.get("alamat"),

            "tanggal_lahir": None,

            "status": user.get("status"),

            "role_id": user.get("role_id"),

            "role": (
                user.get("nama_role")
                or "Member"
            ),

            "created_at": created_at,
            "joinDate": created_at,

            "foto": user.get("foto") or "",
        }

    # =========================================================
    # HELPER: BANGUN QUERY SELECT YANG AMAN + ALIAS KOLOM
    # (hasil SELECT selalu dipetakan ke nama standar:
    #  phone, alamat, created_at, tanggal_lahir, dst.
    #  meskipun nama kolom asli di database berbeda)
    # =========================================================

    def build_safe_select(
        self,
        cursor,
        table_name,
        alias,
        id_column,
        fixed_columns,
        aliased_columns,
    ):
        existing_cols = self.get_table_columns(
            cursor, table_name
        )

        parts = []

        # -----------------------------------------------------
        # KOLOM ID (wajib ada)
        # -----------------------------------------------------

        parts.append(f"{alias}.{id_column}")

        # -----------------------------------------------------
        # KOLOM TETAP (nama pasti sama, cuma dicek keberadaannya)
        # -----------------------------------------------------

        for col in fixed_columns:
            if col in existing_cols:
                parts.append(f"{alias}.{col}")

        # -----------------------------------------------------
        # KOLOM DENGAN ALIAS (nama bisa beda-beda)
        # -----------------------------------------------------

        resolved_map = {}

        for output_name, alias_list in aliased_columns.items():
            real_col = self.resolve_column(
                existing_cols, alias_list
            )

            resolved_map[output_name] = real_col

            if real_col:
                parts.append(
                    f"{alias}.{real_col} AS {output_name}"
                )

        select_sql = ", ".join(parts)

        return select_sql, existing_cols, resolved_map

    # =========================================================
    # HELPER: AMBIL 1 ROW USER MANAGEMENT (BY id_user / email)
    # =========================================================

    def fetch_user_row(
        self, cursor, where_sql, where_value
    ):
        select_sql, existing_cols, resolved_map = (
            self.build_safe_select(
                cursor,
                "user",
                "u",
                "id_user",
                fixed_columns=[
                    "title",
                    "nama",
                    "email",
                    "status",
                    "role_id",
                ],
                aliased_columns={
                    "phone": self.PHONE_ALIASES,
                    "alamat": self.ALAMAT_ALIASES,
                    "tanggal_lahir": self.TANGGAL_LAHIR_ALIASES,
                    "created_at": self.CREATED_AT_ALIASES,
                },
            )
        )

        query = f"""
            SELECT {select_sql}, r.nama_role
            FROM `user` u
            LEFT JOIN `role` r
                ON u.role_id = r.id_role
            WHERE {where_sql}
            LIMIT 1
        """

        cursor.execute(query, (where_value,))

        row = cursor.fetchone()

        return row, existing_cols, resolved_map

    # =========================================================
    # HELPER: AMBIL 1 ROW AUTH USER (BY id_auth / email)
    # =========================================================

    def fetch_auth_row(
        self, cursor, where_sql, where_value
    ):
        select_sql, existing_cols, resolved_map = (
            self.build_safe_select(
                cursor,
                "auth_user",
                "a",
                "id_auth",
                fixed_columns=[
                    "nama",
                    "email",
                    "status",
                ],
                aliased_columns={
                    "phone": self.PHONE_ALIASES,
                    "alamat": self.ALAMAT_ALIASES,
                    "created_at": self.CREATED_AT_ALIASES,
                },
            )
        )

        query = f"""
            SELECT {select_sql}, r.id_role AS role_id, r.nama_role
            FROM auth_user a
            LEFT JOIN `role` r
                ON LOWER(r.nama_role) = 'member'
            WHERE {where_sql}
            LIMIT 1
        """

        cursor.execute(query, (where_value,))

        row = cursor.fetchone()

        return row, existing_cols, resolved_map

    # =========================================================
    # GET PROFILE
    # =========================================================

    def on_get(self, req, resp):

        id_user = req.get_param("id_user")
        id_auth = req.get_param("id_auth")
        email = req.get_param("email")

        if (
            not id_user
            and not id_auth
            and not email
        ):
            resp.status = falcon.HTTP_400

            resp.media = {
                "success": False,
                "message": (
                    "id_user, id_auth atau "
                    "email wajib dikirim"
                ),
            }

            return

        conn = None
        cursor = None

        try:

            conn = get_connection()

            cursor = conn.cursor(
                dictionary=True
            )

            user = None
            account_type = None

            # =================================================
            # 1. USER MANAGEMENT BERDASARKAN ID
            # =================================================

            if id_user:

                user, _, _ = self.fetch_user_row(
                    cursor,
                    "u.id_user = %s",
                    id_user,
                )

                if user:
                    account_type = "user"

            # =================================================
            # 2. AUTH USER BERDASARKAN ID_AUTH
            # =================================================

            elif id_auth:

                user, _, _ = self.fetch_auth_row(
                    cursor,
                    "a.id_auth = %s",
                    id_auth,
                )

                if user:
                    account_type = "auth_user"

            # =================================================
            # 3. BERDASARKAN EMAIL
            # =================================================

            elif email:

                email_clean = (
                    str(email)
                    .strip()
                    .lower()
                )

                # ---------------------------------------------
                # CEK USER MANAGEMENT
                # ---------------------------------------------

                user, _, _ = self.fetch_user_row(
                    cursor,
                    "LOWER(u.email) = %s",
                    email_clean,
                )

                if user:
                    account_type = "user"

                # ---------------------------------------------
                # CEK AUTH USER
                # ---------------------------------------------

                if not user:

                    user, _, _ = self.fetch_auth_row(
                        cursor,
                        "LOWER(a.email) = %s",
                        email_clean,
                    )

                    if user:
                        account_type = "auth_user"

            # =================================================
            # PROFILE TIDAK DITEMUKAN
            # =================================================

            if not user:

                resp.status = falcon.HTTP_404

                resp.media = {
                    "success": False,
                    "message": (
                        "Profile pengguna "
                        "tidak ditemukan"
                    ),
                }

                return

            # =================================================
            # FORMAT DATA
            # =================================================

            if account_type == "auth_user":

                profile = (
                    self.format_auth_profile(
                        user
                    )
                )

            else:

                profile = (
                    self.format_user_profile(
                        user
                    )
                )

            # =================================================
            # RESPONSE
            # =================================================

            resp.status = falcon.HTTP_200

            resp.media = {
                "success": True,
                "message": (
                    "Profile berhasil diambil"
                ),
                "data": profile,
            }

        except Exception as e:

            print(
                "PROFILE GET ERROR:",
                str(e),
                flush=True,
            )

            resp.status = falcon.HTTP_500

            resp.media = {
                "success": False,
                "message": (
                    "Gagal mengambil profile"
                ),
                "error": str(e),
            }

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    # =========================================================
    # UPDATE PROFILE
    # =========================================================

    def on_put(self, req, resp):

        try:
            data = req.media or {}

        except Exception:
            data = {}

        id_user = data.get("id_user")
        id_auth = data.get("id_auth")

        nama = data.get("nama")
        email = data.get("email")
        phone = data.get("phone")
        alamat = data.get("alamat")

        # =====================================================
        # BERSIHKAN DATA
        # =====================================================

        nama = (
            str(nama).strip()
            if nama is not None
            else ""
        )

        email = (
            str(email)
            .strip()
            .lower()
            if email is not None
            else ""
        )

        phone = (
            str(phone).strip()
            if phone is not None
            and str(phone).strip()
            else None
        )

        alamat = (
            str(alamat).strip()
            if alamat is not None
            and str(alamat).strip()
            else None
        )

        # =====================================================
        # VALIDASI NAMA
        # =====================================================

        if not nama:

            resp.status = falcon.HTTP_400

            resp.media = {
                "success": False,
                "message": (
                    "Nama wajib diisi"
                ),
            }

            return

        # =====================================================
        # VALIDASI EMAIL
        # =====================================================

        if not email:

            resp.status = falcon.HTTP_400

            resp.media = {
                "success": False,
                "message": (
                    "Email wajib diisi"
                ),
            }

            return

        conn = None
        cursor = None

        try:

            conn = get_connection()

            cursor = conn.cursor(
                dictionary=True
            )

            # =================================================
            # JIKA ID TIDAK DIKIRIM
            # CARI BERDASARKAN EMAIL
            # =================================================

            if not id_user and not id_auth:

                cursor.execute(
                    """
                    SELECT
                        id_user
                    FROM `user`
                    WHERE LOWER(email) = %s
                    LIMIT 1
                    """,
                    (email,),
                )

                found_user = cursor.fetchone()

                if found_user:

                    id_user = (
                        found_user["id_user"]
                    )

                else:

                    cursor.execute(
                        """
                        SELECT
                            id_auth
                        FROM auth_user
                        WHERE LOWER(email) = %s
                        LIMIT 1
                        """,
                        (email,),
                    )

                    found_auth = (
                        cursor.fetchone()
                    )

                    if found_auth:

                        id_auth = (
                            found_auth[
                                "id_auth"
                            ]
                        )

            # =================================================
            # USER TIDAK DITEMUKAN
            # =================================================

            if not id_user and not id_auth:

                resp.status = falcon.HTTP_404

                resp.media = {
                    "success": False,
                    "message": (
                        "User tidak ditemukan "
                        "berdasarkan akun yang sedang login"
                    ),
                }

                return

            # =================================================
            # UPDATE USER MANAGEMENT
            # =================================================

            if id_user:

                # ---------------------------------------------
                # CEK USER
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_user
                    FROM `user`
                    WHERE id_user = %s
                    LIMIT 1
                    """,
                    (id_user,),
                )

                existing_user = (
                    cursor.fetchone()
                )

                if not existing_user:

                    resp.status = falcon.HTTP_404

                    resp.media = {
                        "success": False,
                        "message": (
                            "User tidak ditemukan"
                        ),
                    }

                    return

                # ---------------------------------------------
                # CEK EMAIL USER LAIN
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_user
                    FROM `user`
                    WHERE LOWER(email) = %s
                    AND id_user != %s
                    LIMIT 1
                    """,
                    (
                        email,
                        id_user,
                    ),
                )

                if cursor.fetchone():

                    resp.status = falcon.HTTP_409

                    resp.media = {
                        "success": False,
                        "message": (
                            "Email sudah digunakan "
                            "oleh pengguna lain"
                        ),
                    }

                    return

                # ---------------------------------------------
                # CEK EMAIL DI AUTH_USER
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_auth
                    FROM auth_user
                    WHERE LOWER(email) = %s
                    LIMIT 1
                    """,
                    (email,),
                )

                if cursor.fetchone():

                    resp.status = falcon.HTTP_409

                    resp.media = {
                        "success": False,
                        "message": (
                            "Email sudah digunakan "
                            "oleh akun lain"
                        ),
                    }

                    return

                # ---------------------------------------------
                # UPDATE USER (HANYA KOLOM YANG BENAR-BENAR ADA,
                # DENGAN ALIAS NAMA KOLOM phone / alamat)
                # ---------------------------------------------

                user_cols = self.get_table_columns(
                    cursor, "user"
                )

                phone_col = self.resolve_column(
                    user_cols, self.PHONE_ALIASES
                )

                alamat_col = self.resolve_column(
                    user_cols, self.ALAMAT_ALIASES
                )

                set_parts = ["nama = %s", "email = %s"]
                set_values = [nama, email]

                if phone_col:
                    set_parts.append(f"{phone_col} = %s")
                    set_values.append(phone)

                if alamat_col:
                    set_parts.append(f"{alamat_col} = %s")
                    set_values.append(alamat)

                set_values.append(id_user)

                cursor.execute(
                    f"""
                    UPDATE `user`
                    SET {", ".join(set_parts)}
                    WHERE id_user = %s
                    """,
                    tuple(set_values),
                )

                conn.commit()

                # ---------------------------------------------
                # AMBIL DATA TERBARU
                # ---------------------------------------------

                updated_user, _, _ = self.fetch_user_row(
                    cursor,
                    "u.id_user = %s",
                    id_user,
                )

                if not updated_user:

                    raise Exception(
                        "Data user berhasil di-update "
                        "tetapi tidak dapat dibaca kembali"
                    )

                profile = (
                    self.format_user_profile(
                        updated_user
                    )
                )

            # =================================================
            # UPDATE AUTH_USER
            # =================================================

            else:

                # ---------------------------------------------
                # CEK AUTH USER
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_auth
                    FROM auth_user
                    WHERE id_auth = %s
                    LIMIT 1
                    """,
                    (id_auth,),
                )

                existing_auth = (
                    cursor.fetchone()
                )

                if not existing_auth:

                    resp.status = falcon.HTTP_404

                    resp.media = {
                        "success": False,
                        "message": (
                            "Akun Member "
                            "tidak ditemukan"
                        ),
                    }

                    return

                # ---------------------------------------------
                # CEK EMAIL AUTH LAIN
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_auth
                    FROM auth_user
                    WHERE LOWER(email) = %s
                    AND id_auth != %s
                    LIMIT 1
                    """,
                    (
                        email,
                        id_auth,
                    ),
                )

                if cursor.fetchone():

                    resp.status = falcon.HTTP_409

                    resp.media = {
                        "success": False,
                        "message": (
                            "Email sudah digunakan "
                            "oleh akun lain"
                        ),
                    }

                    return

                # ---------------------------------------------
                # CEK EMAIL USER MANAGEMENT
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_user
                    FROM `user`
                    WHERE LOWER(email) = %s
                    LIMIT 1
                    """,
                    (email,),
                )

                if cursor.fetchone():

                    resp.status = falcon.HTTP_409

                    resp.media = {
                        "success": False,
                        "message": (
                            "Email sudah digunakan "
                            "oleh pengguna lain"
                        ),
                    }

                    return

                # ---------------------------------------------
                # UPDATE AUTH USER (HANYA KOLOM YANG BENAR-BENAR ADA,
                # DENGAN ALIAS NAMA KOLOM phone / alamat)
                # ---------------------------------------------

                auth_cols = self.get_table_columns(
                    cursor, "auth_user"
                )

                phone_col = self.resolve_column(
                    auth_cols, self.PHONE_ALIASES
                )

                alamat_col = self.resolve_column(
                    auth_cols, self.ALAMAT_ALIASES
                )

                set_parts = ["nama = %s", "email = %s"]
                set_values = [nama, email]

                if phone_col:
                    set_parts.append(f"{phone_col} = %s")
                    set_values.append(phone)

                if alamat_col:
                    set_parts.append(f"{alamat_col} = %s")
                    set_values.append(alamat)

                set_values.append(id_auth)

                cursor.execute(
                    f"""
                    UPDATE auth_user
                    SET {", ".join(set_parts)}
                    WHERE id_auth = %s
                    """,
                    tuple(set_values),
                )

                conn.commit()

                # ---------------------------------------------
                # AMBIL DATA TERBARU
                # ---------------------------------------------

                updated_auth, _, _ = self.fetch_auth_row(
                    cursor,
                    "a.id_auth = %s",
                    id_auth,
                )

                if not updated_auth:

                    raise Exception(
                        "Data member berhasil di-update "
                        "tetapi tidak dapat dibaca kembali"
                    )

                profile = (
                    self.format_auth_profile(
                        updated_auth
                    )
                )

            # =================================================
            # RESPONSE BERHASIL
            # =================================================

            resp.status = falcon.HTTP_200

            resp.media = {
                "success": True,
                "message": (
                    "Profile berhasil diperbarui"
                ),
                "data": profile,
            }

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "PROFILE UPDATE ERROR:",
                str(e),
                flush=True,
            )

            resp.status = falcon.HTTP_500

            resp.media = {
                "success": False,
                "message": (
                    "Gagal memperbarui profile"
                ),
                "error": str(e),
            }

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()
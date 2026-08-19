import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="db_dashboard_management",
        connection_timeout=5,
        use_pure=True
    )


if __name__ == "__main__":
    print("Mencoba koneksi ke MySQL...", flush=True)

    try:
        print("Menghubungkan...", flush=True)

        conn = get_connection()

        print("DATABASE BERHASIL TERHUBUNG!", flush=True)
        print("Database: db_dashboard_management", flush=True)

        cursor = conn.cursor()

        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()

        print("Database aktif:", database[0], flush=True)

        cursor.execute("SHOW TABLES")

        tables = cursor.fetchall()

        print("Tabel:", flush=True)

        for table in tables:
            print("-", table[0], flush=True)

        print("\nMengecek data USER...", flush=True)

        cursor.execute("""
            SELECT
                id_user,
                nama,
                email,
                password,
                status,
                role_id
            FROM user
        """)

        users = cursor.fetchall()

        if users:
            print("Data USER:", flush=True)

            for user in users:
                print(
                    "ID:", user[0],
                    "| Nama:", user[1],
                    "| Email:", user[2],
                    "| Password:", user[3],
                    "| Status:", user[4],
                    "| Role:", user[5],
                    flush=True
                )
        else:
            print("TABEL USER KOSONG!", flush=True)

        cursor.close()
        conn.close()

        print("\nSelesai!", flush=True)

    except Exception as e:
        print("DATABASE GAGAL TERHUBUNG!", flush=True)
        print(type(e).__name__, flush=True)
        print(str(e), flush=True)
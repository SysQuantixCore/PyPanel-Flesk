import os

import mysql.connector
from mysql.connector import Error


def get_db():
    connection = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "admin"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            connection_timeout=5,
            autocommit=False,
            charset="utf8mb4",
            use_unicode=True
        )

        if not connection.is_connected():
            raise Error("Não foi possível estabelecer conexão com o MySQL.")

        print("[MYSQL] Conexão administrativa estabelecida.")

        return connection

    except Error as err:
        print(f"[MYSQL] Erro de conexão: {err}")

        if connection is not None:
            try:
                connection.close()
            except Error:
                pass

        raise
import os

import pymysql


def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        port=int(os.getenv("DB_PORT", "3307")),
        database=os.getenv("DB_NAME", "taiq_db"),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4"
    )

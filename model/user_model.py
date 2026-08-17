from database import get_db

# =================================
# AUTH FUNCTIONS
# =================================

def get_user_by_login(login):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM ai_users
                WHERE username = %s
                   OR email = %s
                LIMIT 1
            """, (login, login))
            return cursor.fetchone()
    finally:
        db.close()

def get_user_by_username(username):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM ai_users WHERE username = %s LIMIT 1",
                (username,)
            )
            return cursor.fetchone()
    finally:
        db.close()


def create_user(data):
    db = get_db()

    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO ai_users
            (
                name,
                username,
                email,
                password,
                role,
                created_by,
                created_at,
                is_active,
                team_id,
                team_name
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, (
            data["name"],
            data["username"],
            data["email"],
            data["password"],
            data["role"],
            data["created_by"],
            data["created_at"],
            data["is_active"],
            data["team_id"],
            data["team_name"]
        ))

        db.commit()

        # Return inserted user ID
        return cursor.lastrowid

    finally:
        cursor.close()
        db.close()

# =================================
# USER CRUD FUNCTIONS
# =================================

def get_all_users():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    username,
                    email,
                    role,
                    is_active,
                    team_id,
                    team_name,
                    created_at
                FROM ai_users
                ORDER BY id DESC
            """)
            return cursor.fetchall()
    finally:
        db.close()


def get_user(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM ai_users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()
    finally:
        db.close()


def update_user(user_id, data):
    db = get_db()

    try:
        with db.cursor() as cursor:

            if data.get("password"):
                cursor.execute("""
                    UPDATE ai_users
                    SET
                        name=%s,
                        username=%s,
                        email=%s,
                        role=%s,
                        team_id=%s,
                        team_name=%s,
                        is_active=%s,
                        password=%s
                    WHERE id=%s
                """, (
                    data["name"],
                    data["username"],
                    data["email"],
                    data["role"],
                    data["team_id"],
                    data["team_name"],
                    data["is_active"],
                    data["password"],
                    user_id
                ))
            else:
                cursor.execute("""
                    UPDATE ai_users
                    SET
                        name=%s,
                        username=%s,
                        email=%s,
                        role=%s,
                        team_id=%s,
                        team_name=%s,
                        is_active=%s
                    WHERE id=%s
                """, (
                    data["name"],
                    data["username"],
                    data["email"],
                    data["role"],
                    data["team_id"],
                    data["team_name"],
                    data["is_active"],
                    user_id
                ))

            affected_rows = cursor.rowcount
            db.commit()
            return affected_rows

    finally:
        db.close()


def update_password(user_id, password):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE ai_users
                SET password=%s
                WHERE id=%s
            """, (
                password,
                user_id
            ))
            db.commit()
    finally:
        db.close()


def delete_user(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM ai_users WHERE id=%s",
                (user_id,)
            )
            db.commit()
    finally:
        db.close()


def change_user_status(user_id, status):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE ai_users
                SET is_active=%s
                WHERE id=%s
            """, (
                status,
                user_id
            ))
            db.commit()
    finally:
        db.close()

def get_user_by_id(user_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    username,
                    email,
                    role,
                    team_id,
                    team_name,
                    is_active,
                    created_at
                FROM ai_users
                WHERE id = %s
                LIMIT 1
            """, (user_id,))
            user = cursor.fetchone()
            return user
    finally:
        db.close()

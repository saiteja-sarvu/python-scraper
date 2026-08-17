from database import get_db

def get_all_tenders():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    *
                FROM ai_tenders
                ORDER BY id DESC
            """)
            return cursor.fetchall()
    finally:
        db.close()

def get_tender_by_id(tender_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    source,
                    source_url,
                    reference_number,
                    title,
                    organization,
                    country,
                    published_date,
                    deadline,
                    category,
                    keyword,
                    description,
                    status,
                    scraped_at,
                    created_at,
                    updated_at
                FROM ai_tenders
                WHERE id = %s
                LIMIT 1
            """, (tender_id,))
            return cursor.fetchone()

    finally:
        db.close()
        
def create_tender(data):
    db = get_db()

    try:
        with db.cursor() as cursor:

            cursor.execute("""
                INSERT INTO ai_tenders (
                    source,
                    external_id,
                    source_url,
                    reference_number,
                    title,
                    organization,
                    country,
                    published_date,
                    deadline,
                    deadline_timezone,
                    category,
                    keyword,
                    description,
                    status,
                    scraped_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, NOW()
                )
            """, (
                data.get("source"),
                data.get("external_id"),
                data.get("source_url"),
                data.get("reference_number"),
                data.get("title"),
                data.get("organization"),
                data.get("country"),
                data.get("published_date"),
                data.get("deadline"),
                data.get("deadline_timezone"),
                data.get("category"),
                data.get("keyword"),
                data.get("description"),
                data.get("status", "new")
            ))

            db.commit()

            return cursor.lastrowid

    finally:
        db.close()

def tender_exists(source, external_id):
    db = get_db()

    try:
        with db.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM ai_tenders
                WHERE source = %s
                  AND external_id = %s
                LIMIT 1
            """, (
                source,
                external_id
            ))

            return cursor.fetchone() is not None

    finally:
        db.close()
import sqlite3
import os

ESG_DB_PATH = "db/esg_reports.db"

def init_esg_report_db():
    os.makedirs("db", exist_ok=True)
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Industry (
            industry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_name_zh TEXT UNIQUE,
            industry_name_en TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Company (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name_zh TEXT UNIQUE,
            company_name_en TEXT,
            industry_id INTEGER,
            FOREIGN KEY (industry_id) REFERENCES Industry(industry_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ESG_Report (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            report_year INTEGER,
            content TEXT,
            FOREIGN KEY (company_id) REFERENCES Company(company_id)
        );
        """)
        conn.commit()

def insert_industry(industry_name_zh=None, industry_name_en=None):
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO Industry (industry_name_zh, industry_name_en)
            VALUES (?, ?)
        """, (industry_name_zh, industry_name_en))
        conn.commit()

def insert_company(company_name_zh=None, industry_name_zh=None, company_name_en=None, industry_name_en=None):
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()

        # Try zh first, then fallback to en
        if industry_name_zh:
            cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_zh = ?", (industry_name_zh,))
        elif industry_name_en:
            cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_en = ?", (industry_name_en,))
        else:
            raise ValueError("Either industry_name_zh or industry_name_en must be provided.")

        row = cursor.fetchone()

        if not row:
            insert_industry(industry_name_zh or industry_name_en, industry_name_en)
            if industry_name_zh:
                cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_zh = ?", (industry_name_zh,))
            else:
                cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_en = ?", (industry_name_en,))
            row = cursor.fetchone()

        industry_id = row[0]
        cursor.execute("""
            INSERT OR IGNORE INTO Company (company_name_zh, company_name_en, industry_id)
            VALUES (?, ?, ?)
        """, (company_name_zh, company_name_en, industry_id))
        conn.commit()

def insert_esg_report(company_name, report_year, content):
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()

        # Try match by English name first
        cursor.execute("SELECT company_id FROM Company WHERE company_name_en = ?", (company_name,))
        row = cursor.fetchone()

        if not row:
            # Fallback: try matching by Chinese name
            cursor.execute("SELECT company_id FROM Company WHERE company_name_zh = ?", (company_name,))
            row = cursor.fetchone()

        if not row:
            raise ValueError(f"Company '{company_name}' not found in either zh or en. Please insert it first.")

        company_id = row[0]

        # Prevent duplicates
        cursor.execute("""
            SELECT 1 FROM ESG_Report
            WHERE company_id = ? AND report_year = ? AND content = ?
        """, (company_id, report_year, content))
        if cursor.fetchone():
            print("⚠️ Report already exists. Skipping insert.")
            return

        # Insert report
        cursor.execute("""
            INSERT INTO ESG_Report (company_id, report_year, content)
            VALUES (?, ?, ?)
        """, (company_id, report_year, content))
        conn.commit()
        
def insert_esg_report_by_id(company_id, report_year, content, overwrite=False):
    with sqlite3.connect("db/esg_reports.db") as conn:
        cursor = conn.cursor()

        if overwrite:
            cursor.execute("""
                DELETE FROM ESG_Report
                WHERE company_id = ? AND report_year = ?
            """, (company_id, report_year))
            print(f"🧹 Overwritten ESG report: company_id={company_id}, year={report_year}")
        else:
            cursor.execute("""
                SELECT 1 FROM ESG_Report
                WHERE company_id = ? AND report_year = ?
            """, (company_id, report_year))
            if cursor.fetchone():
                print("⚠️ Report already exists. Skipping insert.")
                return

        cursor.execute("""
            INSERT INTO ESG_Report (company_id, report_year, content)
            VALUES (?, ?, ?)
        """, (company_id, report_year, content))
        conn.commit()


#原本的start
# def insert_esg_report_by_id(company_id, report_year, content):
#     with sqlite3.connect(ESG_DB_PATH) as conn:
#         cursor = conn.cursor()

#         cursor.execute("""
#             SELECT 1 FROM ESG_Report
#             WHERE company_id = ? AND report_year = ? AND content = ?
#         """, (company_id, report_year, content))
#         if cursor.fetchone():
#             print("⚠️ Report already exists. Skipping insert.")
#             return

#         cursor.execute("""
#             INSERT INTO ESG_Report (company_id, report_year, content)
#             VALUES (?, ?, ?)
#         """, (company_id, report_year, content))
#         conn.commit()
#end

# def get_company_id_by_en_name(company_name_en):
#     with sqlite3.connect(ESG_DB_PATH) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT company_id FROM Company WHERE company_name_en = ?", (company_name_en,))
#         row = cursor.fetchone()
#         if row:
#             return row[0]
#         else:
#             return None
# def get_company_id_by_zh_name(company_name_zh):
#     with sqlite3.connect(ESG_DB_PATH) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT company_id FROM Company WHERE company_name_zh = ?", (company_name_zh,))
#         row = cursor.fetchone()
#         return row[0] if row else None

import sqlite3
import os
import pandas as pd

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

<<<<<<< HEAD
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
=======
def insert_esg_report_by_id(company_id, report_year, content):
    with sqlite3.connect("db/esg_reports.db") as conn:
        cursor = conn.cursor()

        # 如果已存在，不插入
        cursor.execute("""
            SELECT 1 FROM ESG_Report
            WHERE company_id = ? AND report_year = ?
        """, (company_id, report_year))
        if cursor.fetchone():
            print("⚠️ Report already exists. Skipping insert.")
            return False
>>>>>>> 010d56c (Reinitialize repo after clearing Git corruption)

        cursor.execute("""
            INSERT INTO ESG_Report (company_id, report_year, content)
            VALUES (?, ?, ?)
        """, (company_id, report_year, content))
        conn.commit()
<<<<<<< HEAD

=======
        return True
>>>>>>> 010d56c (Reinitialize repo after clearing Git corruption)

def get_all_esg_reports():
    with sqlite3.connect(ESG_DB_PATH) as conn:
        df = pd.read_sql_query("""
            SELECT ESG_Report.report_id,
                   Company.company_name_en AS company,
                   Company.company_name_zh AS company_zh,
                   Industry.industry_name_en AS industry,
                   Industry.industry_name_zh AS industry_zh,
                   ESG_Report.report_year AS year,
                   ESG_Report.content
            FROM ESG_Report
            JOIN Company ON ESG_Report.company_id = Company.company_id
            JOIN Industry ON Company.industry_id = Industry.industry_id
            ORDER BY ESG_Report.report_year DESC
        """, conn)
    return df

def get_all_companies():
    with sqlite3.connect(ESG_DB_PATH) as conn:
        df = pd.read_sql_query("""
            SELECT company_name_en, company_name_zh
            FROM Company
            WHERE company_name_en IS NOT NULL
            GROUP BY company_name_en
            ORDER BY company_name_en
        """, conn)
    return df

def get_all_industries():
    with sqlite3.connect(ESG_DB_PATH) as conn:
        df = pd.read_sql_query("""
            SELECT industry_name_en, industry_name_zh
            FROM Industry
            WHERE industry_name_en IS NOT NULL
            GROUP BY industry_name_en
            ORDER BY industry_name_en
        """, conn)
    return df
<<<<<<< HEAD
=======

def get_industry_by_company(company_name: str):
    """
    根據公司名稱（中或英文）查找對應的產業名稱（中或英文）

    Args:
        company_name (str): 公司中文或英文名稱

    Returns:
        dict: {"industry_name_zh": ..., "industry_name_en": ...} or None if not found
    """
    with sqlite3.connect(ESG_DB_PATH) as conn:
        company_df = pd.read_sql_query("""
            SELECT *
            FROM Company
            GROUP BY company_id
            ORDER BY company_id
        """, conn)

        industry_df = pd.read_sql_query("""
            SELECT *
            FROM Industry
            GROUP BY industry_id
            ORDER BY industry_id
        """, conn)

    # 找出公司對應的 industry_id
    matched = company_df[
        (company_df["company_name_zh"] == company_name) |
        (company_df["company_name_en"].str.upper() == company_name.upper())
    ]

    if matched.empty:
        return None

    industry_id = matched.iloc[0]["industry_id"]

    # 查找產業名稱
    industry_row = industry_df[industry_df["industry_id"] == industry_id]
    if industry_row.empty:
        return None

    return {
        "industry_name_zh": industry_row.iloc[0]["industry_name_zh"],
        "industry_name_en": industry_row.iloc[0]["industry_name_en"]
    }

def insert_or_get_company_id(company_name, industry, language="en"):
    """
    根據語言自動插入公司與產業，並回傳 company_id
    :param company_name: 公司名稱（中或英文）
    :param industry: 產業名稱（中或英文）
    :param language: 'zh' 或 'en'
    :return: company_id
    """
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()

        # 取得 industry_id，必要時插入
        if language == "zh":
            cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_zh = ?", (industry,))
        else:
            cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_en = ?", (industry,))
        industry_row = cursor.fetchone()

        if not industry_row:
            insert_industry(
                industry_name_zh=industry if language == "zh" else None,
                industry_name_en=industry if language == "en" else None
            )
            # 再查一次
            if language == "zh":
                cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_zh = ?", (industry,))
            else:
                cursor.execute("SELECT industry_id FROM Industry WHERE industry_name_en = ?", (industry,))
            industry_row = cursor.fetchone()

        industry_id = industry_row[0]

        # 取得 company_id，必要時插入
        if language == "zh":
            cursor.execute("SELECT company_id FROM Company WHERE company_name_zh = ?", (company_name,))
        else:
            cursor.execute("SELECT company_id FROM Company WHERE company_name_en = ?", (company_name,))
        company_row = cursor.fetchone()

        if not company_row:
            insert_company(
                company_name_zh=company_name if language == "zh" else None,
                company_name_en=company_name if language == "en" else None,
                industry_name_zh=industry if language == "zh" else None,
                industry_name_en=industry if language == "en" else None
            )
            if language == "zh":
                cursor.execute("SELECT company_id FROM Company WHERE company_name_zh = ?", (company_name,))
            else:
                cursor.execute("SELECT company_id FROM Company WHERE company_name_en = ?", (company_name,))
            company_row = cursor.fetchone()

        if not company_row:
            raise ValueError(f"❌ No company_id found for '{company_name}'")

        return company_row[0]

def delete_esg_reports_by_ids(report_ids):
    """根據 report_id 列表刪除 ESG_Report 資料"""
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "DELETE FROM ESG_Report WHERE report_id = ?",
            [(rid,) for rid in report_ids]
        )
        conn.commit()


def clean_incomplete_company_and_industry():
    """刪除 Company 或 Industry 中欄位為 NULL 的不完整資料"""
    with sqlite3.connect(ESG_DB_PATH) as conn:
        cursor = conn.cursor()
        # 刪除 Company 中任一欄為 NULL
        cursor.execute("""
            DELETE FROM Company
            WHERE company_name_zh IS NULL
               OR company_name_en IS NULL
               OR industry_id IS NULL
        """)
        # 刪除 Industry 中任一欄為 NULL
        cursor.execute("""
            DELETE FROM Industry
            WHERE industry_name_zh IS NULL
               OR industry_name_en IS NULL
        """)
        conn.commit()
>>>>>>> 010d56c (Reinitialize repo after clearing Git corruption)

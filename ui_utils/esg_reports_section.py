import streamlit as st
import pandas as pd
import sqlite3
from db_utils.esg_report_db_utils import *

def show_esg_report_table():
    st.subheader("\U0001F4CA ESG Report Table")

    # Set default session states
    st.session_state.setdefault("selected_company", "All")
    st.session_state.setdefault("selected_industry", "All")
    st.session_state.setdefault("selected_year", "All")
    st.session_state.setdefault("delete_confirm", False)
    st.session_state.setdefault("selected_to_delete", [])

    if st.button("\U0001F4E5 Update ESG DB from TWSE"):
        from qa_utils.twse_scraper import write_twse_example_to_db
        write_twse_example_to_db()
        st.success("\u2705 TWSE ESG data inserted.")

    # Load filter options and data from DB
    with sqlite3.connect("db/esg_reports.db") as conn:
        company_df = pd.read_sql_query("""
            SELECT company_name_en, company_name_zh FROM Company
            WHERE company_name_en IS NOT NULL
            GROUP BY company_name_en
            ORDER BY company_name_en
        """, conn)

        industry_df = pd.read_sql_query("""
            SELECT industry_name_en, industry_name_zh FROM Industry
            WHERE industry_name_en IS NOT NULL
            GROUP BY industry_name_en
            ORDER BY industry_name_en
        """, conn)

        companies = [f"{row['company_name_en']} ({row['company_name_zh']})" for _, row in company_df.iterrows()]
        industries = [f"{row['industry_name_en']} ({row['industry_name_zh']})" for _, row in industry_df.iterrows()]

        df = pd.read_sql_query("""
            SELECT 
                ESG_Report.report_id,
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

    # Filters
    with st.expander("\U0001F50D Filter Conditions", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_company = st.selectbox(
                "Company", ["All"] + companies,
                index=(1 + companies.index(st.session_state["selected_company"]) if st.session_state["selected_company"] in companies else 0)
            )
            st.session_state["selected_company"] = selected_company
        with col2:
            selected_industry = st.selectbox(
                "Industry", ["All"] + industries,
                index=(1 + industries.index(st.session_state["selected_industry"]) if st.session_state["selected_industry"] in industries else 0)
            )
            st.session_state["selected_industry"] = selected_industry
        with col3:
            years = sorted(df["year"].dropna().astype(str).unique())
            selected_year = st.selectbox("Report Year", ["All"] + years,
                index=(1 + list(years).index(st.session_state["selected_year"]) if st.session_state["selected_year"] in years else 0))
            st.session_state["selected_year"] = selected_year

    # Apply filters
    if st.session_state["selected_company"] != "All":
        company_en = st.session_state["selected_company"].split(" (")[0]
        df = df[df["company"] == company_en]
    if st.session_state["selected_industry"] != "All":
        industry_en = st.session_state["selected_industry"].split(" (")[0]
        df = df[df["industry"] == industry_en]
    if st.session_state["selected_year"] != "All":
        df = df[df["year"].astype(str) == st.session_state["selected_year"]]

    # if df.empty:
    #     st.warning("\U0001F50D No ESG reports found for the selected filters.")
    #     return
    if df.empty:
        st.markdown("#### 📄 ESG Report Table")
        st.info("🔍 No ESG reports found for the selected filters.")
        header = st.columns([0.05, 0.25, 0.25, 0.1, 0.35])
        header[0].markdown("**Select**")
        header[1].markdown("**Company**")
        header[2].markdown("**Industry**")
        header[3].markdown("**Year**")
        header[4].markdown("**Content**")
        return

    # Display ESG Report Table
    selected_ids = []
    st.markdown("#### \U0001F4C4 ESG Report Table")
    header = st.columns([0.05, 0.25, 0.25, 0.1, 0.35])
    header[0].markdown("**Select**")
    header[1].markdown("**Company**")
    header[2].markdown("**Industry**")
    header[3].markdown("**Year**")
    header[4].markdown("**Content**")

    for _, row in df.iterrows():
        cols = st.columns([0.05, 0.25, 0.25, 0.1, 0.35])
        with cols[0]:
            if st.checkbox("", key=f"select_{row['report_id']}"):
                selected_ids.append(row["report_id"])
        cols[1].write(f"{row['company']} ({row['company_zh']})")
        cols[2].write(f"{row['industry']} ({row['industry_zh']})")
        cols[3].write(row["year"])
        cols[4].write(row["content"][:100] + "...")

    # Deletion confirm logic
    if selected_ids and not st.session_state["delete_confirm"]:
        if st.button("\U0001F5D1️ Delete Selected"):
            st.session_state.delete_confirm = True
            st.session_state.selected_to_delete = selected_ids
            st.rerun()

    if st.session_state.delete_confirm:
        with st.container():
            st.warning("\u26A0️ This action cannot be undone. Confirm deletion?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("\u2705 Confirm"):
                    with sqlite3.connect("db/esg_reports.db") as conn:
                        cursor = conn.cursor()
                        cursor.executemany("DELETE FROM ESG_Report WHERE report_id = ?", [(rid,) for rid in st.session_state.selected_to_delete])
                        conn.commit()
                    st.success(f"Deleted {len(st.session_state.selected_to_delete)} record(s).")
                    st.session_state.delete_confirm = False
                    st.session_state.selected_to_delete = []
                    st.rerun()
            with col_cancel:
                if st.button("\u274C Cancel"):
                    st.info("Deletion cancelled.")
                    st.session_state.delete_confirm = False
                    st.session_state.selected_to_delete = []

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

LOGFILE = "ltv_input_history.csv"
ARCHIVE_FILE = "deleted_ltv_history.xlsx"

# ────────────────────────────────
# ✅ 고객 이력 저장
# ────────────────────────────────
def save_user_input(overwrite=False):
    record = {
        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "고객명": st.session_state.get("customer_name", "").strip(),
        "주소": st.session_state.get("address_input", "").strip(),
        "KB시세": st.session_state.get("raw_price_input", ""),
        "면적": st.session_state.get("area_input", ""),
        "LTV1": st.session_state.get("raw_ltv1", ""),
        "LTV2": st.session_state.get("raw_ltv2", ""),
        "결과내용": st.session_state.get("text_to_copy", "")
    }

    if not record["고객명"] or not record["주소"]:
        st.warning("⚠️ 고객명과 주소는 필수입니다.")
        return

    df = pd.read_csv(LOGFILE) if os.path.exists(LOGFILE) else pd.DataFrame()

    if overwrite:
        df = df[~((df["고객명"] == record["고객명"]) & (df["주소"] == record["주소"]))]

    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(LOGFILE, index=False, encoding="utf-8-sig")
    st.success("✅ 저장되었습니다.")

# ────────────────────────────────
# ✅ 고객 이력 불러오기
# ────────────────────────────────
def load_customer_input(name: str) -> bool:
    if not os.path.exists(LOGFILE):
        return False

    df = pd.read_csv(LOGFILE)
    row = df[df["고객명"] == name].sort_values("날짜", ascending=False).head(1)
    if row.empty:
        return False

    r = row.iloc[0]
    st.session_state["customer_name"] = r.get("고객명", "")
    st.session_state["address_input"] = r.get("주소", "")
    st.session_state["raw_price_input"] = str(r.get("KB시세", ""))
    st.session_state["area_input"] = str(r.get("면적", ""))
    st.session_state["raw_ltv1"] = str(r.get("LTV1", ""))
    st.session_state["raw_ltv2"] = str(r.get("LTV2", ""))
    st.session_state["text_to_copy"] = str(r.get("결과내용", ""))
    st.success(f"✅ '{name}'님의 최근 이력을 불러왔습니다.")
    return True

# ────────────────────────────────
# ✅ 고객명 목록 가져오기
# ────────────────────────────────
def get_customer_options():
    if not os.path.exists(LOGFILE):
        return []
    df = pd.read_csv(LOGFILE)
    return sorted(df["고객명"].dropna().unique())

# ────────────────────────────────
# ✅ 고객명 검색 (부분일치)
# ────────────────────────────────
def search_customers_by_keyword(keyword):
    if not os.path.exists(LOGFILE) or not keyword:
        return []
    df = pd.read_csv(LOGFILE)
    matches = df[df["고객명"].str.contains(keyword, na=False)]
    return sorted(matches["고객명"].dropna().unique())

# ────────────────────────────────
# ✅ 오래된 이력 정리 및 백업
# ────────────────────────────────
def cleanup_old_history(days=30):
    if not os.path.exists(LOGFILE):
        return

    df = pd.read_csv(LOGFILE, parse_dates=["날짜"])
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    cutoff = datetime.now() - timedelta(days=days)
    deleted_df = df[df["날짜"] < cutoff]
    kept_df = df[df["날짜"] >= cutoff]

    if not deleted_df.empty:
        deleted_df.to_excel(ARCHIVE_FILE, index=False)
        st.session_state["deleted_data_ready"] = True
    else:
        st.session_state["deleted_data_ready"] = False

    kept_df.to_csv(LOGFILE, index=False, encoding="utf-8-sig")

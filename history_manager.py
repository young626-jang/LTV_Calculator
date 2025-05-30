import os
import pandas as pd
import streamlit as st
from datetime import datetime

# 파일 이름 정의
HISTORY_FILE = "ltv_input_history.csv"
ARCHIVE_FILE = "ltv_archive_deleted.xlsx"

# 🔹 현재 입력된 고객명 가져오기
def get_customer_name():
    return st.session_state.get("customer_name", "").strip()

# 🔹 현재 입력된 주소 가져오기
def get_address():
    return st.session_state.get("address_input", "").strip()

# 🔹 입력 내용 저장
def save_user_input(overwrite=False):
    customer_name = get_customer_name()
    address = get_address()

    if not customer_name or not address:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "저장시각": now,
        "고객명": customer_name,
        "주소": address,
    }

    # 세션 상태 값 전부 저장 (문자열, 숫자만)
    for key in st.session_state:
        val = st.session_state[key]
        if isinstance(val, (str, int, float)):
            record[key] = val

    df_new = pd.DataFrame([record])

    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        if overwrite:
            df = df[~((df["고객명"] == customer_name) & (df["주소"] == address))]
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(HISTORY_FILE, index=False)

# 🔹 고객 이력 목록 제공 (중복제거)
def get_customer_options():
    if not os.path.exists(HISTORY_FILE):
        return []
    df = pd.read_csv(HISTORY_FILE)
    return df["고객명"].dropna().unique().tolist()

# 🔹 고객명 기반 데이터 불러오기
def load_customer_input(name):
    if not os.path.exists(HISTORY_FILE):
        return

    df = pd.read_csv(HISTORY_FILE)
    df_match = df[df["고객명"] == name]

    if df_match.empty:
        return

    last = df_match.iloc[-1]

    for key, val in last.items():
        if key in ["고객명", "주소", "저장시각"]:
            continue
        st.session_state[key] = val

# 🔹 키워드로 고객 검색
def search_customers_by_keyword(keyword):
    if not os.path.exists(HISTORY_FILE):
        return []

    df = pd.read_csv(HISTORY_FILE)
    df_result = df[df["고객명"].str.contains(keyword, na=False)]
    return df_result["고객명"].dropna().unique().tolist()

# 🔹 오래된 데이터 정리
def cleanup_old_history(threshold_days=30):
    if not os.path.exists(HISTORY_FILE):
        return

    df = pd.read_csv(HISTORY_FILE)
    df["저장시각"] = pd.to_datetime(df["저장시각"], errors="coerce")
    cutoff = datetime.now() - pd.Timedelta(days=threshold_days)

    to_keep = df[df["저장시각"] >= cutoff]
    to_delete = df[df["저장시각"] < cutoff]

    to_keep.to_csv(HISTORY_FILE, index=False)

    if not to_delete.empty:
        to_delete.to_excel(ARCHIVE_FILE, index=False)
        st.session_state["deleted_data_ready"] = True

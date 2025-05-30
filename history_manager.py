import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import streamlit as st

# ─────────────────────────────
# 🔐 Google Sheets 인증 및 시트 접근
# ─────────────────────────────
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_key.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("ltv_input_history").sheet1  # 시트 이름 및 인덱스
    return sheet

# ─────────────────────────────
# 💾 고객 입력 저장 (Google Sheets)
# ─────────────────────────────
def save_user_input(overwrite=False):
    sheet = get_sheet()

    record = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.get("customer_name", "").strip(),
        st.session_state.get("address_input", "").strip(),
        st.session_state.get("raw_price_input", ""),
        st.session_state.get("area_input", ""),
        st.session_state.get("raw_ltv1", ""),
        st.session_state.get("raw_ltv2", "")
    ]

    if not record[1] or not record[2]:
        return  # 고객명 or 주소 없으면 저장하지 않음

    # 시트 읽기
    data = sheet.get_all_values()
    headers = data[0] if data else ["날짜", "고객명", "주소", "KB시세", "면적", "LTV1", "LTV2"]
    rows = data[1:] if len(data) > 1 else []

    if overwrite:
        rows = [row for row in rows if not (row[1] == record[1] and row[2] == record[2])]
        sheet.clear()
        sheet.append_row(headers)
        for row in rows:
            sheet.append_row(row)

    sheet.append_row(record)

# ─────────────────────────────
# 📂 고객명으로 최근 입력 불러오기
# ─────────────────────────────
def load_customer_input(name):
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        return

    row = df[df["고객명"] == name].sort_values("날짜", ascending=False).head(1)

    if not row.empty:
        r = row.iloc[0]
        st.session_state["customer_name"] = r["고객명"]
        st.session_state["address_input"] = r["주소"]
        st.session_state["raw_price_input"] = str(r["KB시세"])
        st.session_state["area_input"] = str(r["면적"])
        st.session_state["raw_ltv1"] = str(r["LTV1"])
        st.session_state["raw_ltv2"] = str(r["LTV2"])
        st.success(f"✅ {name}님의 입력 이력이 로드되었습니다.")

# ─────────────────────────────
# 🧾 고객명 리스트 추출
# ─────────────────────────────
def get_customer_options():
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return sorted(df["고객명"].dropna().unique())

# ─────────────────────────────
# 🔍 고객명 키워드 검색
# ─────────────────────────────
def search_customers_by_keyword(keyword):
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not keyword:
        return []
    matches = df[df["고객명"].str.contains(keyword, na=False)]
    return sorted(matches["고객명"].dropna().unique())

# ─────────────────────────────
# 🧹 오래된 이력 정리 (권장 X)
# ─────────────────────────────
def cleanup_old_history(days=30):
    st.info("📌 현재는 Google Sheets 사용 중이므로 자동 삭제보다는 시트에서 수동 정리를 권장합니다.")

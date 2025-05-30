import os

import pandas as pd

from datetime import datetime


HISTORY_FILE = "ltv_input_history.csv"

ARCHIVE_FILE = "ltv_archive_deleted.xlsx"


def save_user_input(overwrite=False):

    customer_name = get_customer_name()

    if not customer_name:

        return


    entry = {

        "고객명": customer_name,

        "주소": st.session_state.get("address_input", ""),

        "전용면적": st.session_state.get("area_input", ""),

        "KB시세": st.session_state.get("raw_price_input", ""),

        "저장일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    }


    df_new = pd.DataFrame([entry])


    if os.path.exists(HISTORY_FILE):

        df = pd.read_csv(HISTORY_FILE)

        if overwrite:

            df = df[df["고객명"] != customer_name]

        df = pd.concat([df, df_new], ignore_index=True)

    else:

        df = df_new


    df.to_csv(HISTORY_FILE, index=False)



def get_customer_name():

    return st.session_state.get("customer_name", "").strip()



def get_customer_options():

    if not os.path.exists(HISTORY_FILE):

        return []

    df = pd.read_csv(HISTORY_FILE)

    return df["고객명"].dropna().unique().tolist()



def load_customer_input(name):

    if not os.path.exists(HISTORY_FILE):

        return

    df = pd.read_csv(HISTORY_FILE)

    match = df[df["고객명"] == name]

    if not match.empty:

        row = match.iloc[-1]

        st.session_state["customer_name"] = row["고객명"]

        st.session_state["address_input"] = row["주소"]

        st.session_state["area_input"] = row["전용면적"]

        st.session_state["raw_price_input"] = row["KB시세"]



def cleanup_old_history():

    if not os.path.exists(HISTORY_FILE):

        st.session_state["deleted_data_ready"] = False

        return


    df = pd.read_csv(HISTORY_FILE)

    df["저장일시"] = pd.to_datetime(df["저장일시"], errors='coerce')

    cutoff = datetime.now() - pd.Timedelta(days=30)

    old_entries = df[df["저장일시"] < cutoff]


    if old_entries.empty:

        st.session_state["deleted_data_ready"] = False

        return


    recent_df = df[df["저장일시"] >= cutoff]

    df.to_csv(HISTORY_FILE, index=False)

    old_entries.to_excel(ARCHIVE_FILE, index=False)

    st.session_state["deleted_data_ready"] = True



def search_customers_by_keyword(keyword):

    if not os.path.exists(HISTORY_FILE):

        return []

    df = pd.read_csv(HISTORY_FILE)

    return df[df["고객명"].str.contains(keyword, na=False)]["고객명"].tolist()



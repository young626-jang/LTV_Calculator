import streamlit as st

st.set_page_config(page_title="LTV 계산기", layout="wide")

import fitz  # PyMuPDF
import re
import urllib.parse
from ltv_map import region_map

st.title("🏠 LTV 계산기 (주소+면적추출)")

# 등기명/주소/면적 추출 함수
def extract_owner_number_from_text(text):
    try:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "등록번호" in line:
                line4 = lines[i + 4].strip() if i + 4 < len(lines) else ""
                line5 = lines[i + 5].strip() if i + 5 < len(lines) else ""
                combined = f"{line4} {line5}".strip()
                return combined if combined.strip() else ""
        return ""
    except Exception as e:
        return ""

def extract_address_area_floor_from_text(text):
    try:
        address = re.search(r"\[집합건물\]\s*([^\n]+)", text)
        extracted_address = address.group(1).strip() if address else ""
        area_match = re.findall(r"(\d+\.\d+)\s*㎡", text)
        extracted_area = f"{area_match[-1]}㎡" if area_match else ""
        floor_match = re.findall(r"제(\d+)층", extracted_address)
        floor_num = int(floor_match[-1]) if floor_match else None
        return extracted_address, extracted_area, floor_num
    except:
        return "", "", None

def pdf_to_image(file_path, page_num):
    doc = fitz.open(file_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    img = pix.tobytes("png")
    return img

# 숫자 → 콤마 함수
def format_with_comma(key):
    raw = st.session_state.get(key, "")
    clean = re.sub(r"[^\d]", "", raw)
    if clean.isdigit():
        st.session_state[key] = "{:,}".format(int(clean))
    else:
        st.session_state[key] = ""

# KB시세(한글단위 포함) → 숫자
def parse_korean_number(text: str) -> int:
    txt = text.replace(",", "").strip()
    total = 0
    m = re.search(r"(\d+)\s*억", txt)
    if m:
        total += int(m.group(1)) * 10000
    m = re.search(r"(\d+)\s*천만", txt)
    if m:
        total += int(m.group(1)) * 1000
    m = re.search(r"(\d+)\s*만", txt)
    if m:
        total += int(m.group(1))
    if total == 0:
        try:
            total = int(txt)
        except:
            total = 0
    return total

def format_kb_price():
    raw = st.session_state.get("raw_price", "")
    clean = parse_korean_number(raw)
    st.session_state["raw_price"] = "{:,}".format(clean) if clean else ""

def format_area():
    raw = st.session_state.get("area_input", "")
    clean = re.sub(r"[^\d.]", "", raw)
    if clean and not raw.endswith("㎡"):
        st.session_state["area_input"] = f"{clean}㎡"

def floor_to_unit(value, unit=100):
    return value // unit * unit

# ----------- 변수 선언/초기화 -----------
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 0
if "raw_price" not in st.session_state:
    st.session_state["raw_price"] = "0"

uploaded_file = st.file_uploader("등기부등본 PDF 업로드", type=["pdf"], key="file_upload_main")
extracted_address, extracted_area, floor_num = "", "", None
owner_number = ""
full_text = ""

if uploaded_file:
    path = f"./{uploaded_file.name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    with fitz.open(path) as doc:
        full_text = "".join(page.get_text() for page in doc)
        total_pages = doc.page_count
        extracted_address, extracted_area, floor_num = extract_address_area_floor_from_text(full_text)
        owner_number = extract_owner_number_from_text(full_text)
        # ... (이하 생략, PDF 미리보기 등)
    # ★★★ PDF 사용 끝난 뒤에 바로 파일 삭제!
    import os
    try:
        os.remove(path)
    except Exception as e:
        pass  # 삭제 실패해도 무시(예: 이미 지워졌거나 권한 없음)

        # PDF 미리보기
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state["current_page"] < total_pages:
                img_left = pdf_to_image(path, st.session_state["current_page"])
                st.image(img_left, caption=f"Page {st.session_state['current_page'] + 1} of {total_pages}")
        with col2:
            if st.session_state["current_page"] + 1 < total_pages:
                img_right = pdf_to_image(path, st.session_state["current_page"] + 1)
                st.image(img_right, caption=f"Page {st.session_state['current_page'] + 2} of {total_pages}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀ 이전 페이지", key="prev_page"):
                if st.session_state["current_page"] > 0:
                    st.session_state["current_page"] -= 1
        with col2:
            if st.button("다음 페이지 ▶", key="next_page"):
                if st.session_state["current_page"] < total_pages - 1:
                    st.session_state["current_page"] += 1
else:
    total_pages = 0

# ----------- 입력 UI -----------
address_input = st.text_input("주소", extracted_address, key="address_input")

col1, col2 = st.columns(2)
raw_price_input = col1.text_input("KB 시세 (만원)", key="raw_price", on_change=format_kb_price)
area_input = col2.text_input("전용면적 (㎡)", extracted_area, key="area_input", on_change=format_area)

floor_match = re.findall(r"제(\d+)층", address_input)
floor_num = int(floor_match[-1]) if floor_match else None
if floor_num is not None:
    if floor_num <= 2:
        st.markdown('<span style="color:red; font-weight:bold; font-size:18px">📉 하안가</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#007BFF; font-weight:bold; font-size:18px">📈 일반가</span>', unsafe_allow_html=True)

if st.button("KB 시세 조회"):
    url = "https://kbland.kr/map?xy=37.5205559,126.9265729,17"
    st.components.v1.html(f"<script>window.open('{url}','_blank')</script>", height=0)

col1, col2 = st.columns(2)
region = col1.selectbox("방공제 지역 선택", [""] + list(region_map.keys()))
default_d = region_map.get(region, 0)
manual_d = col2.text_input("방공제 금액 (만)", f"{default_d:,}")
deduction = int(re.sub(r"[^\d]", "", manual_d)) if manual_d else default_d

col1, col2 = st.columns(2)
raw_ltv1 = col1.text_input("LTV 비율 ①", "80")
raw_ltv2 = col2.text_input("LTV 비율 ②", "")

ltv_selected = []
for val in [raw_ltv1, raw_ltv2]:
    try:
        v = int(val)
        if 1 <= v <= 100:
            ltv_selected.append(v)
    except:
        pass
ltv_selected = list(dict.fromkeys(ltv_selected))

# ----------- 대출 항목 입력 UI -----------
st.markdown("### 📝 대출 항목 입력")
rows = st.number_input("항목 개수", min_value=1, max_value=10, value=3)
items = []
for i in range(int(rows)):
    cols = st.columns(5)
    lender = cols[0].text_input("설정자", key=f"lender_{i}")
    max_amt_key = f"maxamt_{i}"
    cols[1].text_input(
        "채권최고액 (만)",
        key=max_amt_key,
        on_change=format_with_comma,
        args=(max_amt_key,)
    )
    ratio = cols[2].text_input("설정비율 (%)", "120", key=f"ratio_{i}")
    try:
        calc = int(re.sub(r"[^\d]", "", st.session_state.get(max_amt_key, "0")) or 0) * 100 // int(ratio or 100)
    except:
        calc = 0
    principal_key = f"principal_{i}"
    cols[3].text_input(
        "원금",
        key=principal_key,
        value=f"{calc:,}",
        on_change=format_with_comma,
        args=(principal_key,)
    )
    status = cols[4].selectbox("진행구분", ["유지", "대환", "선말소"], key=f"status_{i}")
    items.append({
        "설정자": lender,
        "채권최고액": st.session_state.get(max_amt_key, ""),
        "설정비율": ratio,
        "원금": st.session_state.get(principal_key, ""),
        "진행구분": status
    })

# ----------- 계산부 -----------
total_value = parse_korean_number(raw_price_input)
senior_principal_sum = sum(
    int(re.sub(r"[^\d]", "", item.get("원금", "0")) or 0)
    for item in items if item.get("진행구분") in ["대환", "선말소"]
)
sum_dh = sum(
    int(re.sub(r"[^\d]", "", item.get("원금", "0")) or 0)
    for item in items if item.get("진행구분") == "대환"
)
sum_sm = sum(
    int(re.sub(r"[^\d]", "", item.get("원금", "0")) or 0)
    for item in items if item.get("진행구분") == "선말소"
)

valid_items = []
for item in items:
    is_valid = any([
        item.get("설정자", "").strip(),
        re.sub(r"[^\d]", "", item.get("채권최고액", "") or "0") != "0",
        re.sub(r"[^\d]", "", item.get("원금", "") or "0") != "0"
    ])
    if is_valid:
        valid_items.append(item)

def calculate_ltv(total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, is_senior=True):
    if is_senior:
        limit = int(total_value * (ltv / 100) - deduction)
        available = int(limit - senior_principal_sum)
    else:
        limit = int(total_value * (ltv / 100) - maintain_maxamt_sum - deduction)
        available = int(limit - senior_principal_sum)
    # 10만 단위로 반올림
    limit = (limit // 10) * 10
    available = (available // 10) * 10
    return limit, available

has_maintain = any(item["진행구분"] == "유지" for item in items)
has_senior = any(item["진행구분"] in ["대환", "선말소"] for item in items)

limit_senior = avail_senior = limit_sub = avail_sub = 0

for ltv in ltv_selected:
    # 선순위 LTV: "유지"가 없을 때만
    if has_senior and not has_maintain:
        limit_senior, avail_senior = calculate_ltv(
            total_value, deduction, senior_principal_sum, 0, ltv, is_senior=True
        )
        limit_senior = floor_to_unit(limit_senior)
        avail_senior = floor_to_unit(avail_senior)
    # 후순위 LTV: "유지"가 있을 때만
    if has_maintain:
        maintain_maxamt_sum = sum(
            int(re.sub(r"[^\d]", "", item.get("채권최고액", "") or "0"))
            for item in items if item["진행구분"] == "유지"
        )
        limit_sub, avail_sub = calculate_ltv(
            total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, is_senior=False
        )
        limit_sub = floor_to_unit(limit_sub)
        avail_sub = floor_to_unit(avail_sub)

# ----------- 결과내용 조립/출력 -----------
text_to_copy = f"고객명: {owner_number}\n주소: {address_input}\n"

type_of_price = "📉 하안가" if floor_num and floor_num <= 2 else "📈 일반가"
text_to_copy += f"{type_of_price} | KB시세: {raw_price_input}만 | 전용면적: {area_input} | 방공제 금액: {deduction:,}만\n"

if valid_items:
    text_to_copy += "\n📋 대출 항목\n"
    for item in valid_items:
        max_amt = int(re.sub(r"[^\d]", "", item.get("채권최고액", "") or "0"))
        principal_amt = int(re.sub(r"[^\d]", "", item.get("원금", "") or "0"))
        text_to_copy += f"{item['설정자']} | 채권최고액: {max_amt:,} | 비율: {item.get('설정비율', '0')}% | 원금: {principal_amt:,} | {item['진행구분']}\n"

for ltv in ltv_selected:
    if has_senior and not has_maintain:
        text_to_copy += f"\n✅ 선순위 LTV {ltv}% ☞ 대출가능금액 {limit_senior:,} 가용 {avail_senior:,}"
    if has_maintain:
        text_to_copy += f"\n✅ 후순위 LTV {ltv}% ☞ 대출가능금액 {limit_sub:,} 가용 {avail_sub:,}"

text_to_copy += "\n[진행구분별 원금 합계]\n"
if sum_dh > 0:
    text_to_copy += f"대환: {sum_dh:,}만\n"
if sum_sm > 0:
    text_to_copy += f"선말소: {sum_sm:,}만\n"

st.text_area("📋 결과 내용", value=text_to_copy, height=300)

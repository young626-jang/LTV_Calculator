import streamlit as st
import os
import fitz  # PyMuPDF
import re
from ltv_map import region_map
import subprocess
import sys
import webbrowser

st.set_page_config(page_title="LTV 계산기", layout="wide")
st.title("🏠 LTV 계산기 (주소+면적추출)")

# ------------------------------
# 🔹 텍스트 기반 추출 함수들
# ------------------------------

def extract_address(text):
    m = re.search(r"\[집합건물\]\s*([^\n]+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"소재지\s*[:：]?\s*([^\n]+)", text)
    if m:
        return m.group(1).strip()
    return ""

def extract_area_floor(text):
    m = re.findall(r"(\d+\.\d+)\s*㎡", text.replace('\n', ' '))
    area = f"{m[-1]}㎡" if m else ""
    floor = None
    addr = extract_address(text)
    f_match = re.findall(r"제(\d+)층", addr)
    if f_match:
        floor = int(f_match[-1])
    return area, floor

def extract_all_names_and_births(text):
    start = text.find("주요 등기사항 요약")
    if start == -1:
        return []
    summary = text[start:]
    lines = [l.strip() for l in summary.splitlines() if l.strip()]
    result = []
    for i in range(len(lines)):
        if re.match(r"[가-힣]+ \(공유자\)|[가-힣]+ \(소유자\)", lines[i]):
            name = re.match(r"([가-힣]+)", lines[i]).group(1)
            if i + 1 < len(lines):
                birth_match = re.match(r"(\d{6})-", lines[i + 1])
                if birth_match:
                    birth = birth_match.group(1)
                    result.append((name, birth))
    return result

# ------------------------------
# 🔹 PDF 처리 함수
# ------------------------------

def process_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    external_links = []

    for page in doc:
        text += page.get_text("text")
        links = page.get_links()
        for link in links:
            if "uri" in link:
                external_links.append(link["uri"])

    doc.close()

    address = extract_address(text)
    area, floor = extract_area_floor(text)
    co_owners = extract_all_names_and_births(text)

    return text, external_links, address, area, floor, co_owners

# ------------------------------
# 🔹 유틸 함수
# ------------------------------

def floor_to_unit(value, unit=100):
    return value // unit * unit

def pdf_to_image(file, page_num):
    file.seek(0)  # ✅ 반드시 필요!
    doc = fitz.open(stream=file.read(), filetype="pdf")
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    return pix.tobytes("png")


def format_with_comma(key):
    raw = st.session_state.get(key, "")
    clean = re.sub(r"[^\d]", "", raw)
    if clean.isdigit():
        st.session_state[key] = "{:,}".format(int(clean))
    else:
        st.session_state[key] = ""

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
    raw = st.session_state.get("raw_price_input", "")
    clean = parse_korean_number(raw)
    st.session_state["raw_price"] = "{:,}".format(clean) if clean else ""

def format_area():
    raw = st.session_state.get("area_input", "")
    clean = re.sub(r"[^\d.]", "", raw)
    st.session_state["extracted_area"] = f"{clean}㎡" if clean else ""

def calculate_ltv(total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, is_senior=True):
    if is_senior:
        limit = int(total_value * (ltv / 100) - deduction)
        available = int(limit - senior_principal_sum)
    else:
        limit = int(total_value * (ltv / 100) - maintain_maxamt_sum - deduction)
        available = int(limit - senior_principal_sum)
    return (limit // 10) * 10, (available // 10) * 10

# ------------------------------
# 🔹 세션 초기화
# ------------------------------

for key in ["extracted_address", "extracted_area", "raw_price", "co_owners", "extracted_floor"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "co_owners" else []

# ------------------------------
# 🔹 PDF 업로드
# ------------------------------

uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드하세요", type="pdf")

if uploaded_file is not None:
    text, external_links, address, area, floor, co_owners = process_pdf(uploaded_file)

    st.session_state["extracted_address"] = address
    st.session_state["extracted_area"] = area
    st.session_state["extracted_floor"] = floor
    st.session_state["co_owners"] = co_owners

    st.success(f"📍 PDF에서 주소 추출: {address}")

    # 📸 PDF 1페이지 미리보기 표시
    img_data = pdf_to_image(uploaded_file, page_num=0)
    st.image(img_data, caption="📄 1페이지 미리보기", use_container_width=True)

    # 🖥 외부 뷰어 열기 버튼 (윈도우 환경에서만 작동)
    def open_pdf_viewer(filepath):
        try:
            if sys.platform.startswith("win"):
                os.startfile(filepath)
            elif sys.platform.startswith("darwin"):  # macOS
                subprocess.call(["open", filepath])
            else:  # Linux
                subprocess.call(["xdg-open", filepath])
        except Exception as e:
            st.error(f"❌ 뷰어 열기 실패: {e}")

    # 🔗 외부 링크 경고
    if external_links:
        st.warning("📎 PDF 내부에 외부 링크가 포함되어 있습니다:")
        for uri in external_links:
            st.code(uri)  # ✅ 여기에 이 코드가 빠졌던 것!


# ------------------------------
# 🔹 입력 UI
# ------------------------------

col1, col2 = st.columns(2)

with col1:
    address_input = st.text_input("주소", st.session_state["extracted_address"], key="address_input")

with col2:
    # 공동명의자 정보를 불러와서 문자열로 변환
    co_owners = st.session_state.get("co_owners", [])
    default_name_text = "  ".join([f"{name} - {birth}" for name, birth in co_owners]) if co_owners else ""

    # 고객명 입력란에 공동명의자 정보 자동 채움
    customer_name = st.text_input("고객명", default_name_text, key="customer_name")

col1, col2 = st.columns(2)
raw_price_value = st.session_state.get("raw_price", "0")
raw_price_input = col1.text_input("KB 시세 (만원)", value=raw_price_value, key="raw_price_input", on_change=format_kb_price)

area_value = st.session_state.get("extracted_area", "")
area_input = col2.text_input("전용면적 (㎡)", value=area_value, key="area_input", on_change=format_area)

# ------------------------------
# 🔹 층수 판단
# ------------------------------

floor_match = re.findall(r"제(\d+)층", address_input)
floor_num = int(floor_match[-1]) if floor_match else None
if floor_num is not None:
    if floor_num <= 2:
        st.markdown('<span style="color:red; font-weight:bold; font-size:18px">📉 하안가</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#007BFF; font-weight:bold; font-size:18px">📈 일반가</span>', unsafe_allow_html=True)

# ------------------------------
# 🔹 버튼 & 지역 설정
# ------------------------------

col1, col2 = st.columns(2)
with col1:
    if st.button("KB 시세 조회"):
        st.components.v1.html("<script>window.open('https://kbland.kr/map','_blank')</script>", height=0)

with col2:
    if st.button("하우스머치 시세조회"):
        st.components.v1.html("<script>window.open('https://www.howsmuch.com','_blank')</script>", height=0)

col1, col2 = st.columns(2)
region = col1.selectbox("방공제 지역 선택", [""] + list(region_map.keys()))
default_d = region_map.get(region, 0)
manual_d = col2.text_input("방공제 금액 (만)", f"{default_d:,}")
deduction = int(re.sub(r"[^\d]", "", manual_d)) if manual_d else default_d

# ------------------------------
# 🔹 LTV 입력
# ------------------------------

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

# ------------------------------
# 🔹 대출 항목 입력
# ------------------------------

rows = st.number_input("대출 항목", min_value=1, max_value=10, value=3)
items = []

for i in range(rows):
    cols = st.columns(5)
    lender = cols[0].text_input("설정자", key=f"lender_{i}")
    max_amt_key = f"maxamt_{i}"
    cols[1].text_input("채권최고액 (만)", key=max_amt_key, on_change=format_with_comma, args=(max_amt_key,))
    ratio = cols[2].text_input("설정비율 (%)", "120", key=f"ratio_{i}")

    try:
        calc = int(re.sub(r"[^\d]", "", st.session_state.get(max_amt_key, "0")) or 0) * 100 // int(ratio or 100)
    except:
        calc = 0

    principal_key = f"principal_{i}"
    cols[3].text_input("원금", key=principal_key, value=f"{calc:,}", on_change=format_with_comma, args=(principal_key,))
    status = cols[4].selectbox("진행구분", ["유지", "대환", "선말소"], key=f"status_{i}")

    items.append({
        "설정자": lender,
        "채권최고액": st.session_state.get(max_amt_key, ""),
        "설정비율": ratio,
        "원금": st.session_state.get(principal_key, ""),
        "진행구분": status
    })

# ------------------------------
# 🔹 LTV 계산부
# ------------------------------

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

valid_items = [item for item in items if any([
    item.get("설정자", "").strip(),
    re.sub(r"[^\d]", "", item.get("채권최고액", "") or "0") != "0",
    re.sub(r"[^\d]", "", item.get("원금", "") or "0") != "0"
])]

limit_senior = avail_senior = limit_sub = avail_sub = 0

for ltv in ltv_selected:
    if has_senior := any(item["진행구분"] in ["대환", "선말소"] for item in items):
        if not any(item["진행구분"] == "유지" for item in items):
            limit_senior, avail_senior = calculate_ltv(total_value, deduction, senior_principal_sum, 0, ltv, True)
    if has_maintain := any(item["진행구분"] == "유지" for item in items):
        maintain_maxamt_sum = sum(
            int(re.sub(r"[^\d]", "", item.get("채권최고액", "0")) or 0)
            for item in items if item.get("진행구분") == "유지"
        )
        limit_sub, avail_sub = calculate_ltv(total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, False)

# ------------------------------
# 🔹 결과 출력
# ------------------------------

text_to_copy = f"고객명 : {customer_name}\n주소 : {address_input}\n"
type_of_price = "하안가" if floor_num and floor_num <= 2 else "일반가"
text_to_copy += f"{type_of_price} | KB시세: {raw_price_input}만 | 전용면적 : {area_input} | 방공제 금액 : {deduction:,}만\n"

if valid_items:
    text_to_copy += "\n대출 항목\n"
    for item in valid_items:
        max_amt = int(re.sub(r"[^\d]", "", item.get("채권최고액", "") or "0"))
        principal_amt = int(re.sub(r"[^\d]", "", item.get("원금", "") or "0"))
        text_to_copy += f"{item['설정자']} | 채권최고액: {max_amt:,} | 비율: {item.get('설정비율', '0')}% | 원금: {principal_amt:,} | {item['진행구분']}\n"

for ltv in ltv_selected:
    if has_senior and not has_maintain:
        text_to_copy += f"\n선순위 LTV {ltv}% {limit_senior:,} 가용 {avail_senior:,}"
    if has_maintain:
        text_to_copy += f"\n후순위 LTV {ltv}% {limit_sub:,} 가용 {avail_sub:,}"

text_to_copy += "\n진행구분별 원금 합계\n"
if sum_dh > 0:
    text_to_copy += f"대환: {sum_dh:,}만\n"
if sum_sm > 0:
    text_to_copy += f"선말소: {sum_sm:,}만\n"

st.text_area("결과 내용", value=text_to_copy, height=320)

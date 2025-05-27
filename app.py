import streamlit as st
from tkinter import Tk, filedialog
import os
import fitz  # PyMuPDF
import re
import urllib.parse
from ltv_map import region_map

st.set_page_config(page_title="LTV 계산기", layout="wide")
st.title("🏠 LTV 계산기 (주소+면적추출)")

# 유틸 함수
def floor_to_unit(value, unit=100):
    return value // unit * unit

# 주소 추출 함수 (실제 정규표현식으로 교체 가능)
def extract_address_from_text(text):
    match = re.search(r"소재지\s*[:：]?\s*([^\n]+)", text)
    return match.group(1).strip() if match else ""

# PDF 처리 함수
def process_pdf(path):
    doc = fitz.open(path)
    text = "".join([p.get_text() for p in doc])
    doc.close()
 주소 = extract_address_from_text(텍스트)
 st.session_state["extracted_주소"] = 주소
 st.success(f")PDF 에서 주소 추출: {주소}}"

# 등기명/주소/면적 추출 함수
def_owner_number_from_text(텍스트):
 시도:
 선 = text.split 선 ()
 i의 경우, enumerate(line)에 줄을 세웁니다:
 "등록번호"가 일렬로 있는 경우:
 line4 = line[i + 4].i + 4 < 렌(라인)이 아닌 경우 스트립 ()"
 line5 = line[i + 5].i + 5 < 렌(라인)인 경우 스트립 ()"
 결합 = f"{line4} {line5}"스트립 ()
 결합된 경우 반환합니다.strip () else"
        돌아가다 ""
 예외:
        돌아가다 ""

def_extract_address_area_floor_from_text(텍스트):
 시도:
 주소 = re.search(r"\\[집합건물\\]\s*([^\n]+)), 텍스트)
 extracted_address = address.group(1).strip ()(다른 주소일 경우)"
 area_match = re.findall(r(\\d+\\.\d+)\\s*㎡), 텍스트)
 추출된_면적 = f"{area_match[-1]}㎡", 면적_match가 다른 경우"
 floor_match = re.findall(r"제(\\d+)층", extracted_address)
 floor_num = int(floor_match[-1]), floor_match가 다른 경우 없음
 return extracted_address, extracted_area, floor_num
 단:
 "",", "", 없음"을 반환합니다

# PDF → 이미지 변환
def pdf_to_image(파일_경로, 페이지_num):
 doc = fitz.open(파일_경로)
 페이지 = doc.load_page(페이지_num)
 pix = 페이지.get_pixmap ()
 img = pix.tobytes("png")
 이미지 반환

# 숫자 → 콤마 자동 포맷
def format_with_comma(key):
    raw = st.session_state.get(key, "")
    clean = re.sub(r"[^\d]", "", raw)
    if clean.isdigit():
        st.session_state[key] = "{:,}".format(int(clean))
    else:
        st.session_state[key] = ""

# KB 시세 (한글단위 포함) → 정수 숫자
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

# KB 시세 입력값 포맷 처리
def format_kb_price():
    raw = st.session_state.get("raw_price", "")
    clean = parse_korean_number(raw)
    st.session_state["raw_price"] = "{:,}".format(clean) if clean else ""

# 전용면적 입력값 포맷 처리
def format_area():
    raw = st.session_state.get("area_input", "")
    clean = re.sub(r"[^\d.]", "", raw)
    if clean and not raw.endswith("㎡"):
        st.session_state["area_input"] = f"{clean}㎡"

# 세션 상태 초기화
if "extracted_address" not in st.session_state:
    st.session_state["extracted_address"] = ""
if "extracted_area" not in st.session_state:
    st.session_state["extracted_area"] = ""
if "raw_price" not in st.session_state:
    st.session_state["raw_price"] = "0"

# 로컬 PDF 선택 버튼
uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드하세요", type="pdf")
if uploaded_file is not None:
    tmp_path = f"tmp_{uploaded_file.name}"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.read())
    process_pdf(tmp_path)
    # 임시파일 삭제(필요시)
    try:
        os.remove(tmp_path)
    except Exception:
        pass

# ----------- 입력 UI -----------
col1, col2 = st.columns(2)

with col1:
    address_input = st.text_input("주소", st.session_state["extracted_address"], key="address_input")    
with col2:
    customer_name = st.text_input("고객명", "", key="customer_name")

col1, col2 = st.columns(2)
raw_price_input = col1.text_input("KB 시세 (만원)", st.session_state["raw_price"], key="raw_price", on_change=format_kb_price)
area_input = col2.text_input("전용면적 (㎡)", st.session_state["extracted_area"], key="area_input", on_change=format_area)

# 층수 판단
floor_match = re.findall(r"제(\d+)층", address_input)
floor_num = int(floor_match[-1]) if floor_match else None
if floor_num is not None:
    if floor_num <= 2:
        st.markdown('<span style="color:red; font-weight:bold; font-size:18px">📉 하안가</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#007BFF; font-weight:bold; font-size:18px">📈 일반가</span>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("KB 시세 조회"):
        url = "https://kbland.kr/map?xy=37.5205559,126.9265729,17"
        st.components.v1.html(f"<script>window.open('{url}','_blank')</script>", height=0)
with col2:
    if st.button("하우스머치 시세조회"):
        url2 = "https://www.howsmuch.com/"
        st.components.v1.html(f"<script>window.open('{url2}','_blank')</script>", height=0)

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
if "format_with_comma" not in globals():
    def format_with_comma(key):  # 안전 가드용 예시 함수
        try:
            value = re.sub(r"[^\d]", "", st.session_state.get(key, "0"))
            formatted = f"{int(value):,}"
            st.session_state[key] = formatted
        except:
            st.session_state[key] = "0"

rows = st.number_input("대출 항목", min_value=1, max_value=10, value=3)
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
 콜스[3].텍스트_입력(
 "원금",
 key=principal_key,
 value=f"{calc:,}",
 on_change=format_with_comma,
 args=(principal_key,)
 )

 상태 = cols[4].선택 상자 ("진행구분", ["유지", "대환", "선말소", 키=f"status_{i}")

 항목.append({
 "설정자": 대출 기관,
 "채권최고액": st.session_state.get(max_amt_key, ","),
 "설정비율": ratio,
 "원금": st.session_state.get(principal_key, ","),
 "진행구분": 상태
 })

# ----------- 계산부 -----------
total_value = parse_korean_number(raw_price_input)

# 선순위 원금 합계 (대환 + 선말소)
시니어_principal_합 = 합(
 int(re.sub(r "[^\\d], "", item.get ("원금", "0") 또는 0)
 항목의 항목에 대해 ["대환", "선말소"]에서 항목을 선택합니다
)

# 대환 합계
sum_dh = sum(
 int(re.sub(r "[^\\d], "", item.get ("원금", "0") 또는 0)
 항목의 항목에 대해 "item.get ("진행구분") == "대환"
)

# 선말소 합계
sum_sm = sum(
 int(re.sub(r "[^\\d], "", item.get ("원금", "0") 또는 0)
 항목의 항목에 대해 "item.get ("진행구분") == "선말소"
)

# 유효 항목만 필터링
유효_items = []
항목 내 항목에 대해:
 is_valid = any([
 item.get ("설정자", "".strip (),"
 re.sub(r "[^\\d], ", "item.get ("채권최고액", "" 또는 "0")!= "0",
 re.sub(r "[^\\d], ", "item.get ("원금", "" 또는 "0")!= "0"
 ])
 만약 _valid:
 유효_items.append(항목)

# LTV 계산 함수
def calculate_ltv(total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, is_senior=True):
    if is_senior:
        limit = int(total_value * (ltv / 100) - deduction)
        available = int(limit - senior_principal_sum)
    else:
        limit = int(total_value * (ltv / 100) - maintain_maxamt_sum - deduction)
        available = int(limit - senior_principal_sum)
    # 10만 단위 절사
    limit = (limit // 10) * 10
    available = (available // 10) * 10
    return limit, available

# 조건 확인
has_maintain = any(item["진행구분"] == "유지" for item in items)
has_senior = any(item["진행구분"] in ["대환", "선말소"] for item in items)

# 초기화
limit_senior = avail_senior = limit_sub = avail_sub = 0

# LTV별 계산
for ltv in ltv_selected:
    # 선순위 계산: 유지 없고, 대환/선말소 있을 때
    if has_senior and not has_maintain:
        limit_senior, avail_senior = calculate_ltv(
            total_value, deduction, senior_principal_sum, 0, ltv, True
        )
    # 후순위 계산: 유지가 있을 때
    if has_maintain:
        maintain_maxamt_sum = sum(
            int(re.sub(r"[^\d]", "", item.get("채권최고액", "0")) or 0)
            for item in items if item.get("진행구분") == "유지"
        )
        limit_sub, avail_sub = calculate_ltv(
            total_value, deduction, senior_principal_sum, maintain_maxamt_sum, ltv, False
        )

# ----------- 결과내용 조립/출력 -----------
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

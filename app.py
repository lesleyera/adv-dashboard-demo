import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# 0. 페이지 기본 설정
st.set_page_config(
    page_title="신문사 성과 대시보드",
    page_icon="📰",
    layout="wide"
)

# 1. 데이터 로딩 (캐시 사용)
@st.cache_data
def load_data(file_path="data.csv"):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. 동일 폴더에 데이터 파일을 위치시켜주세요.")
        return pd.DataFrame()
        
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

df = load_data()

if df.empty:
    st.stop()

# --- 사이드바 ---
st.sidebar.header("필터 설정")

min_date = df['날짜'].min().date()
max_date = df['날짜'].max().date()

start_date, end_date = st.sidebar.date_input(
    "조회 기간을 선택하세요:",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
    format="YYYY.MM.DD"
)

# --- 필터링된 데이터 생성 ---
df_filtered = df[
    (df['날짜'] >= pd.to_datetime(start_date)) & 
    (df['날짜'] <= pd.to_datetime(end_date))
]

if df_filtered.empty:
    st.warning("선택한 기간에 데이터가 없습니다.")
    st.stop()

# --- 메인 대시보드 ---
st.title("📰 인터넷 신문사 성과 대시보드 (Streamlit Demo v2)")

# 2. 탭(Tabs)으로 리포트 페이지 분리 (PDF의 페이지 구분과 유사)
tab1, tab2 = st.tabs(["1. 전체 성과 요약 (PDF 1p)", "2. 카테고리별 분석 (PDF 3p)"])

# --- Tab 1: 전체 성과 요약 ---
with tab1:
    st.header("📈 전체 성과 요약")
    
    # 4. KPI 스코어카드
    total_pv = int(df_filtered['PV'].sum())
    total_uv = int(df_filtered['UV'].sum())
    # 가중 평균 이탈률 계산
    avg_bounce_rate = (df_filtered['이탈률'] * df_filtered['PV']).sum() / total_pv

    col1, col2, col3 = st.columns(3)
    col1.metric(label="총 조회수 (PV)", value=f"{total_pv:,}")
    col2.metric(label="총 사용자 (UV)", value=f"{total_uv:,}")
    col3.metric(label="평균 이탈률", value=f"{avg_bounce_rate:.1%}")

    st.markdown("---")

    # 5. 일별 트래픽 차트 (PDF 1페이지처럼 2개로 분리)
    col_chart1, col_chart2 = st.columns(2)
    df_daily = df_filtered.groupby('날짜')[['PV', 'UV']].sum().reset_index()

    with col_chart1:
        st.subheader("일별 조회수(PV) 추이")
        fig_bar_pv = px.bar(df_daily, x='날짜', y='PV', title='일별 조회수')
        st.plotly_chart(fig_bar_pv, use_container_width=True)

    with col_chart2:
        st.subheader("일별 사용자(UV) 추이")
        fig_bar_uv = px.bar(df_daily, x='날짜', y='UV', title='일별 순 사용자', color_discrete_sequence=['orange'])
        st.plotly_chart(fig_bar_uv, use_container_width=True)

    st.markdown("---")

    # 6. 유입 경로 (PDF 1페이지 하단)
    st.subheader("유입 경로별 사용자 (UV)")
    df_source = df_filtered.groupby('유입 경로')['UV'].sum().sort_values(ascending=False).reset_index()
    
    fig_pie = px.pie(
        df_source, 
        names='유입 경로', 
        values='UV', 
        title='유입 경로 비중',
        hole=0.4
    )
    # PDF 차트처럼 값(value)을 차트 위에 표시
    fig_pie.update_traces(textposition='outside', textinfo='value+label')
    st.plotly_chart(fig_pie, use_container_width=True)


# --- Tab 2: 카테고리별 분석 ---
with tab2:
    st.header("🗂️ 카테고리별 성과 분석 (PDF 3페이지)")

    # 7. 카테고리별 데이터 집계
    df_category = df_filtered.groupby('기사 카테고리').agg(
        PV=('PV', 'sum'),
        UV=('UV', 'sum'),
        기사수=('날짜', 'count'), # 여기서는 '날짜'의 count를 '기사 수'로 임시 사용
        이탈률=('이탈률', 'mean')
    ).reset_index().sort_values(by="PV", ascending=False)
    
    st.subheader("카테고리별 조회수 (PV)")
    
    # 8. 카테고리별 막대 차트
    fig_cat_bar = px.bar(
        df_category,
        x='기사 카테고리',
        y='PV',
        title='카테고리별 총 조회수'
    )
    st.plotly_chart(fig_cat_bar, use_container_width=True)
    
    st.markdown("---")

    # 9. 카테고리별 상세 테이블 (PDF 3페이지의 표)
    st.subheader("카테고리별 상세 데이터")
    st.dataframe(
        df_category,
        use_container_width=True,
        # 숫자에 콤마 추가 및 소수점 정리
        column_config={
            "PV": st.column_config.NumberColumn(format="%,d"),
            "UV": st.column_config.NumberColumn(format="%,d"),
            "이탈률": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=1,
            ),
        }
    )
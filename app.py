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
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. GitHub 저장소에 data.csv가 있는지 확인하세요.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return pd.DataFrame()
        
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 광고 데이터가 없는 경우(NaN) 0으로 처리
    df['광고비'] = df['광고비'].fillna(0)
    df['클릭수'] = df['클릭수'].fillna(0)
    
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
st.title("📰 인터넷 신문사 성과 대시보드 (v4 - 광고 포함)")

# 2. 탭(Tabs)으로 리포트 페이지 분리
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. 전체 성과 (PDF 1p)", 
    "2. 카테고리 분석 (PDF 3p)",
    "3. 인기 기사 분석 (PDF 2p)",
    "4. 독자 특성 분석 (PDF 4p)",
    "5. 광고 성과 분석 (신규)"
])

# --- Tab 1: 전체 성과 요약 ---
with tab1:
    st.header("📈 전체 성과 요약")
    
    total_pv = int(df_filtered['PV'].sum())
    total_uv = int(df_filtered['UV'].sum())
    total_cost = int(df_filtered['광고비'].sum())
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="총 조회수 (PV)", value=f"{total_pv:,}")
    col2.metric(label="총 사용자 (UV)", value=f"{total_uv:,}")
    col3.metric(label="총 광고비", value=f"₩{total_cost:,}") # 전체 탭에도 광고비 요약 추가

    st.markdown("---")
    # (이하 Tab 1의 나머지 코드는 v3와 동일)
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
    st.subheader("유입 경로별 사용자 (UV)")
    df_source = df_filtered.groupby('유입 경로')['UV'].sum().sort_values(ascending=False).reset_index()
    fig_pie_source = px.pie(df_source, names='유입 경로', values='UV', hole=0.4)
    fig_pie_source.update_traces(textposition='outside', textinfo='value+label')
    st.plotly_chart(fig_pie_source, use_container_width=True)


# --- Tab 2: 카테고리별 분석 ---
with tab2:
    st.header("🗂️ 카테고리별 성과 분석")
    # (v3와 동일)
    df_category = df_filtered.groupby('기사 카테고리').agg(
        PV=('PV', 'sum'),
        UV=('UV', 'sum'),
        기사수=('날짜', 'count'),
        이탈률=('이탈률', 'mean')
    ).reset_index().sort_values(by="PV", ascending=False)
    
    st.subheader("카테고리별 조회수 (PV)")
    fig_cat_bar = px.bar(df_category, x='기사 카테고리', y='PV', title='카테고리별 총 조회수')
    st.plotly_chart(fig_cat_bar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("카테고리별 상세 데이터")
    st.dataframe(
        df_category, use_container_width=True,
        column_config={"PV": st.column_config.NumberColumn("조회수", format="%,d"),
                       "UV": st.column_config.NumberColumn("사용자", format="%,d"),
                       "기사수": st.column_config.NumberColumn(format="%,d"),
                       "이탈률": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                      })

# --- Tab 3: 인기 기사 분석 ---
with tab3:
    st.header("📝 인기 기사 분석 (Top 10)")
    # (v3와 동일)
    df_article = df_filtered.groupby(['기사 제목', '작성자', '기사 카테고리']).agg(
        PV=('PV', 'sum'),
        UV=('UV', 'sum'),
        이탈률=('이탈률', 'mean')
    ).reset_index().sort_values(by="PV", ascending=False)

    st.subheader("기사별 상세 데이터 (Top 10)")
    st.dataframe(
        df_article.head(10), use_container_width=True,
        column_config={"PV": st.column_config.NumberColumn("조회수", format="%,d"),
                       "UV": st.column_config.NumberColumn("사용자", format="%,d"),
                       "이탈률": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                      }, hide_index=True)

    st.markdown("---")
    st.subheader("작성자별 성과")
    df_author = df_filtered.groupby('작성자').agg(
        PV=('PV', 'sum'),
        기사수=('기사 제목', 'nunique')
    ).reset_index().sort_values(by="PV", ascending=False)
    fig_author = px.bar(df_author, x='작성자', y='PV', title='작성자별 총 조회수')
    st.plotly_chart(fig_author, use_container_width=True)


# --- Tab 4: 독자 특성 분석 ---
with tab4:
    st.header("👥 독자 특성 분석 (Demographics)")
    # (v3와 동일)
    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        st.subheader("기기별 사용자(UV)")
        df_device = df_filtered.groupby('기기')['UV'].sum().reset_index()
        fig_device = px.pie(df_device, names='기기', values='UV')
        st.plotly_chart(fig_device, use_container_width=True)

        st.subheader("지역별 사용자(UV)")
        df_region = df_filtered.groupby('지역')['UV'].sum().reset_index().sort_values(by="UV", ascending=False)
        df_region = df_region[df_region['지역'] != '(not set)']
        fig_region = px.pie(df_region.head(7), names='지역', values='UV')
        st.plotly_chart(fig_region, use_container_width=True)
    with col_demo2:
        st.subheader("성별 사용자(UV)")
        df_gender = df_filtered.groupby('성별')['UV'].sum().reset_index()
        df_gender = df_gender[df_gender['성별'] != 'unknown']
        fig_gender = px.pie(df_gender, names='성별', values='UV')
        st.plotly_chart(fig_gender, use_container_width=True)

        st.subheader("연령별 사용자(UV)")
        df_age = df_filtered.groupby('연령')['UV'].sum().reset_index()
        df_age = df_age[df_age['연령'] != 'unknown']
        fig_age = px.pie(df_age, names='연령', values='UV')
        st.plotly_chart(fig_age, use_container_width=True)


# --- Tab 5: 광고 성과 분석 (NEW) ---
with tab5:
    st.header("📊 광고 성과 분석")

    # 1. 광고 KPI 요약
    total_cost = int(df_filtered['광고비'].sum())
    total_clicks = int(df_filtered['클릭수'].sum())
    total_pv = int(df_filtered['PV'].sum()) # CTR 계산용
    
    # 0으로 나누기 방지
    avg_cpc = total_cost / total_clicks if total_clicks > 0 else 0
    avg_ctr = (total_clicks / total_pv) * 100 if total_pv > 0 else 0

    st.subheader("광고 핵심 지표(KPI)")
    col_ad1, col_ad2, col_ad3 = st.columns(3)
    col_ad1.metric(label="총 광고비", value=f"₩{total_cost:,}")
    col_ad2.metric(label="총 클릭수 (Clicks)", value=f"{total_clicks:,}")
    col_ad3.metric(label="평균 클릭당비용 (CPC)", value=f"₩{avg_cpc:,.0f}")
    col_ad1.metric(label="평균 클릭률 (CTR)", value=f"{avg_ctr:.2f}%")
    
    st.markdown("---")

    # 2. 요청하신 "표" (카테고리별 광고 성과)
    st.subheader("카테고리별 광고 성과 상세 (표)")
    
    df_ad_category = df_filtered.groupby('기사 카테고리').agg(
        광고비=('광고비', 'sum'),
        클릭수=('클릭수', 'sum'),
        PV=('PV', 'sum')
    ).reset_index()
    
    # CPC (클릭당 비용) 계산
    df_ad_category['CPC'] = df_ad_category.apply(
        lambda row: row['광고비'] / row['클릭수'] if row['클릭수'] > 0 else 0, axis=1
    )
    # CTR (클릭률) 계산
    df_ad_category['CTR'] = df_ad_category.apply(
        lambda row: (row['클릭수'] / row['PV']) * 100 if row['PV'] > 0 else 0, axis=1
    )
    
    df_ad_category = df_ad_category.sort_values(by="광고비", ascending=False)

    st.dataframe(
        df_ad_category,
        use_container_width=True,
        column_config={
            "광고비": st.column_config.NumberColumn(format="₩ %,d"),
            "클릭수": st.column_config.NumberColumn(format="%,d"),
            "PV": st.column_config.NumberColumn(format="%,d"),
            "CPC": st.column_config.NumberColumn(format="₩ %,.0f"),
            "CTR": st.column_config.ProgressColumn(
                format="%.2f%%", min_value=0, max_value=df_ad_category['CTR'].max(),
            ),
        }
    )
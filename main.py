import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 레이아웃을 wide로 설정 (전체 폭 활용)
st.set_page_config(page_title="3000번 버스 탈 수 있을까?", layout="wide")

st.title("3000번 버스 탈 수 있을까?")

# CSV 파일 로드 (캐싱을 활용해 재사용)
@st.cache_data
def load_data():
    return pd.read_csv('processed_bus_data.csv')

data = load_data()

# stationName 컬럼의 결측치를 제거하고 모든 값을 문자열로 변환 후 정렬
station_names = sorted(data['stationName'].dropna().astype(str).unique())

# 왼쪽 사이드바에 정류장 선택 필터 배치 (디폴트는 '강남역나라빌딩앞')
st.sidebar.subheader("정류장 선택")
selected_stations = st.sidebar.multiselect(
    "필요한 정류장을 선택하세요:",
    options=station_names,
    default=['강남역나라빌딩앞']
)

# 선택된 정류장에 해당하는 데이터 필터링 (비교 시에도 문자열로 변환)
if selected_stations:
    filtered_data = data[data['stationName'].astype(str).isin(selected_stations)]
else:
    filtered_data = data.copy()

# 데이터가 있을 경우에만 처리 진행
if not filtered_data.empty:
    # bucket_time 별로 그룹화하여 각 그룹의 집계 결과 생성
    # warning_bus_id_count는 잔여좌석이 5개 이하인 버스의 수를 의미함
    result = filtered_data.groupby('bucket_time').apply(
        lambda group: pd.Series({
            'distinct_bus_id_count': group['bus_id'].nunique(),
            'warning_bus_id_count': group.loc[group['is_warning'], 'bus_id'].nunique()
        })
    ).reset_index()

    # wide 형태의 결과 데이터를 long 형태로 변환
    df_melt = result.melt(
        id_vars='bucket_time',
        value_vars=['distinct_bus_id_count', 'warning_bus_id_count'],
        var_name='count_type',
        value_name='count'
    )
    
    # 범례 이름 변경
    df_melt['count_type'] = df_melt['count_type'].replace({
        'distinct_bus_id_count': '총 버스 운행 수',
        'warning_bus_id_count': '잔여좌석 5회 이하 버스 수'
    })

    # Plotly Express를 이용해 라인 차트 생성
    fig = px.line(
        df_melt,
        x='bucket_time',
        y='count',
        color='count_type',
        title='버스 ID 카운트 by Bucket Time\n(잔여좌석 5개 이하인 버스는 빨간색으로 표시)',
        color_discrete_map={
            '총 버스 운행 수': 'blue',
            '잔여좌석 5회 이하 버스 수': 'red'
        }
    )
    fig.update_layout(
        xaxis_title='Bucket Time',
        yaxis_title='Count',
        xaxis=dict(tickangle=45),
        width=1200,
        height=600
    )

    # 차트를 먼저 표시 (use_container_width=False로 고정 크기 사용)
    st.plotly_chart(fig, use_container_width=False)
    
    # 하단에 집계 결과 테이블 표시
    st.write("집계 결과:", result)
else:
    st.write("선택된 정류장에 해당하는 데이터가 없습니다.")

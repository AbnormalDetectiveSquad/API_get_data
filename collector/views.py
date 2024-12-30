import requests
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from dateutil.relativedelta import relativedelta  
from datetime import datetime, timedelta


def home_view(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>Home</title>
        <style>
            /* 기본 페이지 스타일 */
            body {
                margin: 0;
                padding: 0;
                background-color: #F0F2F5; /* 은은한 회색 배경 */
                color: #333;
                font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
                line-height: 1.5;
                font-size: 18px;  /* 텍스트 크기 크게 */
            }

            /* 메인 컨테이너 */
            .container {
                max-width: 700px;
                margin: 5rem auto; /* 위아래 5rem, 좌우는 자동 중앙정렬 */
                background-color: #fff;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            /* 메인 타이틀 */
            .container h1 {
                text-align: center;
                font-size: 2rem;   /* 큰 헤더 폰트 */
                font-weight: 700;  /* 두껍게 */
                margin-bottom: 1rem;
                color: #444;
            }

            /* 링크 목록 래퍼 */
            .links {
                margin-top: 2rem;
                display: flex;
                flex-direction: column; /* 세로로 버튼 배치 */
                gap: 1rem;             /* 버튼 사이 간격 */
            }

            /* 버튼(링크) 스타일 */
            .links a {
                display: inline-block;
                background-color: #007BFF; /* 파랑 계열 버튼 */
                color: #fff;
                padding: 0.75rem 1.25rem;  /* 버튼 안 여백 */
                border-radius: 5px;
                text-decoration: none;
                font-size: 1.125rem;  /* 18px 정도 */
                font-weight: 600;
                text-align: center;
                transition: background-color 0.3s ease;
            }

            /* 버튼 hover 시 더 짙은 파랑 */
            .links a:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>서울특별시 TOPIS OPEN API</h1>
            <div class="links">
                <a href="/collect_citywall/">한양도성 도로통계</a>
                <a href="/collect_road/">도로별 통계</a>
                <a href="/collect_living/">생활권역별 통계</a>
                <a href="/collect_section/">구간별 통계</a>
                <a href="/collect_direction/">도로별 방향별 통계</a>
                <a href="/collect_divroad/">도로구분별 통계</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

def apply_korean_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    df의 컬럼을 (영어이름, 한국어명칭) 형태의 2행 멀티 인덱스로 만든다.
    - df.columns에는 이미 rename_map 적용 등으로 최종 영문 컬럼 이름이 들어있다고 가정.
    - 각 영문 컬럼에 대응하는 한국어 이름(주석 등)을 아래 dict로 관리한다.
    """

    # 영문 컬럼 -> 한글 주석 매핑
    # (여기서 "avgSpd" -> "(평균속도)" 처럼 원하는 매핑 작성)
    korean_map = {
        "axis_name":         "(도로명)",
        "time_nm":           "(시간대 설명)",
        "time_grp_nm":       "(첨두시 구분)",
        "stnd_dt":           "(기준일자)",
        "time_cd":           "(시간코드)",
        "road_div_nm":       "(도로구분명)",
        "link_seq":          "(구간순서)",
        "link_id":           "(링크ID)",
        "st_node_nm":        "(시점명)",
        "road_div_cd":       "(도로구분코드)",
        "avg_spd":           "(평균속도)",
        "axis_cd":           "(도로코드)",
        "axis_dir_div_cd":   "(도로방향구분코드)",
        "axis_dir_div_nm":   "(도로방향구분명)",
        "day_cd":            "(요일코드)",
        "day_grp_cd":        "(요일그룹코드)",
        "ed_node_nm":        "(종점명)",
    }

    new_cols = []
    for col in df.columns:
        # col이 korean_map에 있으면 (col, 매핑된_한글) 사용
        # 없으면 (col, '') 등으로 처리
        kr_label = korean_map.get(col, "")
        new_cols.append( (col, kr_label) )

    # 실제 멀티 인덱스 적용
    df.columns = pd.MultiIndex.from_tuples(new_cols)
    return df

# 모든 뷰에서 공통으로 사용할 열, 리네임 맵, 로직을 편의상 함수화
def _common_collect_logic(request, base_url: str):
    """
    base_url에 대해 '오늘 날짜부터 하루씩 빼며' API 호출 -> 유효 데이터 찾는 공통 로직
    """

    all_columns = [
        "axis_name",       # (도로명)
        "time_nm",         # (시간대 설명)
        "time_grp_nm",     # (첨두시 구분)
        "stnd_dt",         # (기준일자)
        "time_cd",         # (시간코드)
        "road_div_nm",     # (도로구분명)
        "link_seq",        # (구간순서)
        "link_id",         # (링크ID)
        "st_node_nm",      # (시점명)
        "road_div_cd",     # (도로구분코드)
        "avg_spd",         # (평균속도)  
        "axis_cd",         # (도로코드)
        "axis_dir_div_cd", # (도로방향구분코드)
        "axis_dir_div_nm", # (도로방향구분명)
        "day_cd",          # (요일코드)
        "day_grp_cd",      # (요일그룹코드)
        "ed_node_nm",      # (종점명)
    ]
    rename_map = {
        # timeNm → time_nm
        "timeNm":       "time_nm",
        "time_nm":      "time_nm",
        "TimeNm":       "time_nm",

        # timeGrpNm → time_grp_nm
        "timeGrpNm":    "time_grp_nm",
        "time_grp_nm":  "time_grp_nm",
        "TimeGrpNm":    "time_grp_nm",

        # stndDt → stnd_dt
        "stndDt":       "stnd_dt",
        "StndDt":       "stnd_dt",
        "stnd_dt":      "stnd_dt",

        # timeCd → time_cd
        "timeCd":       "time_cd",
        "TimeCd":       "time_cd",
        "time_cd":      "time_cd",

        # roadDivNm → road_div_nm
        "roadDivNm":    "road_div_nm",
        "road_div_nm":  "road_div_nm",
        "RoadDivNm":    "road_div_nm",

        # linkSeq → link_seq
        "linkSeq":      "link_seq",
        "link_seq":     "link_seq",
        "LinkSeq":      "link_seq",

        # linkId → link_id
        "linkId":       "link_id",
        "link_id":      "link_id",
        "LinkId":       "link_id",

        # stNodeNm → st_node_nm
        "stNodeNm":     "st_node_nm",
        "st_node_nm":   "st_node_nm",
        "StNodeNm":     "st_node_nm",

        # roadDivCd → road_div_cd
        "roadDivCd":    "road_div_cd",
        "road_div_cd":  "road_div_cd",
        "RoadDivCd":    "road_div_cd",

        # edNodeNm → ed_node_nm
        "edNodeNm":     "ed_node_nm",
        "ed_node_nm":   "ed_node_nm",
        "EdNodeNm":     "ed_node_nm",

        # avgSpd → avg_spd
        "avgSpd":       "avg_spd",
        "avg_spd":      "avg_spd",
        "AvgSpd":       "avg_spd",

        # dayCd → day_cd
        "dayCd":        "day_cd",
        "day_cd":       "day_cd",
        "DayCd":        "day_cd",

        # dayGrpCd → day_grp_cd
        "dayGrpCd":     "day_grp_cd",
        "day_grp_cd":   "day_grp_cd",
        "DayGrpCd":     "day_grp_cd",
        
        # dayGrpCd →axis_dir_div_cd
        "axisDirDivCd": "axis_dir_div_cd",
        "axis_dir_div_cd": "axis_dir_div_cd",
        "AxisDirDivCd": "axis_dir_div_cd",
        
        # axisDirDivNm → axis_dir_div_nm
        "axisDirDivNm": "axis_dir_div_nm",
        "axis_dir_div_nm": "axis_dir_div_nm",
        "AxisDirDivNm": "axis_dir_div_nm",
        
        # axisCd → axis_cd
        "axis_cd": "axis_cd",
        "AxisCd": "axis_cd",
        "axisCd": "axis_cd",
        
        # axisName → axis_name
        "axisName": "axis_name",
        "axis_name": "axis_name",
        "AxisName": "axis_name",
        
        
        
    }

    # 오늘 날짜 기준
    today = datetime.now()
    max_days = 60
    days_checked = 0
    final_data = None
    final_url = None
    final_date_str = None

    # API 키
    api_key = "361e8c5d-95ac-4e20-adad-c0972fb6ce5b"

    while days_checked < max_days:
        target_date = today - timedelta(days=days_checked)
        stndDt_str = target_date.strftime("%Y%m%d")

        params = {
            "apikey": api_key,
            "stndDt": stndDt_str,
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            final_url = response.url
            response.raise_for_status()

            data = response.json()  # JSON -> Python
            if isinstance(data, list) and len(data) > 0:
                final_data = data
                final_date_str = stndDt_str
                break
            else:
                days_checked += 1

        except requests.exceptions.RequestException:
            days_checked += 1

    if not final_data:
        error_msg = f"""
        <h1>오류/데이터 없음</h1>
        <p>최대 {max_days}일 동안 과거 날짜를 내려가며 시도했으나 
        유효 데이터를 찾지 못했습니다.</p>
        <p>마지막 시도 URL: {final_url}</p>
        """
        return HttpResponse(error_msg)

    df = pd.DataFrame(final_data)
    if df.empty:
        msg = f"<h1>데이터가 없습니다.</h1><p>마지막 시도 URL: {final_url}</p>"
        return HttpResponse(msg)

    # rename 적용
    df.rename(columns=rename_map, inplace=True)

    # 없으면 None으로 채우기
    for col in all_columns:
        if col not in df.columns:
            df[col] = None

    df_selected = df[all_columns]
    df_selected = apply_korean_labels(df_selected)
    html_table = df_selected.to_html(classes="table table-bordered", index=False)

    html_content = f"""
    <html>
      <head>
        <title>All Columns Table</title>
      </head>
      <body>
        <!-- [상단] 홈으로 돌아가기 -->
        <p><a href="/">[홈으로 돌아가기]</a></p>

        <h2>최종 호출 API URL</h2>
        <p>{final_url}</p>
        <h2>성공 기준일자 (stndDt): {final_date_str}</h2>

        <h1>API 결과 (모든 컬럼 포함)</h1>
        {html_table}
        
      </body>
    </html>
    """
    return HttpResponse(html_content)


def collect_data_citywall_view(request):
    """
    [한양도성 도로통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesRoadDivTrfCityWallStats/1.0"
    )
    return _common_collect_logic(request, base_url)


def collect_data_road_view(request):
    """
    [도로별 통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesRoadTrfRoadStats/1.0"
    )
    return _common_collect_logic(request, base_url)


def collect_data_living_view(request):
    """
    [생활권역별 통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesRoadDivTrfLivingStats/1.0"
    )
    return _common_collect_logic(request, base_url)


def collect_data_section_view(request):
    """
    [구간별 통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesLinkTrfSectionStats/1.0"
    )
    return _common_collect_logic(request, base_url)


def collect_data_direction_view(request):
    """
    [도로별 방향별 통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesRoadTrfDirectionStats/1.0"
    )
    return _common_collect_logic(request, base_url)



    
def collect_data_DivRoad_view(request):
    """
    [도로구분별 통계]
    """
    base_url = (
        "https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/"
        "TopisIccStTimesRoadDivTrfRoadStats/1.0"
    )
    return _common_collect_logic(request, base_url)
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
            <h1>서울특별시 OPEN API</h1>
            <div class="links">
                <a href="/collect_citywall/">한양도성 도로통계</a>
                <a href="/collect_road/">도로별 통계</a>
                <a href="/collect_living/">생활권역별 통계</a>
                <a href="/collect_section/">구간별 통계</a>
                <a href="/collect_direction/">도로별 방향별 통계</a>
                <a href="/collect_divroad/">도로구분별 통계</a>
                <a href="/collect_its_eventInfo/">ITS 돌발상황정보</a>
                <a href="/collect_its_traficInfo/">ITS 교통소통정보</a>
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


def _its_collect_logic(request, input_params: dict, bbox: dict = None):#API 마다 필수 입력 변수 차이 때문에 입력 파라미터를 딕셔너리로 받고 option 항목에 따라 분기 처리 하도록 변경
    """
    ITS API 호출을 위한 공통 로직
    TOPIS와 달리 실시간 데이터를 조회하므로 날짜 기반 반복 호출은 하지 않음

    Parameters:
    - road_type: 도로 유형 (all/ex/its/loc/sgg/etc)
    - event_type: 이벤트 유형 (all/cor/acc/wea/ete/dis/etc)
    - bbox: 검색 영역 좌표 (선택)
    """
    # 필수 파라미터 검증
    event_type = None
    base_url = input_params.get("base_url") 
    option = input_params.get("option")
    if option == "eventInfo":
        api_key = input_params.get("api_key")
        road_type = input_params.get("road_type")
        event_type = input_params.get("event_type")
        if not api_key:
            return HttpResponse("<h1>API 키가 필요합니다.</h1>")

        if road_type not in ["all", "ex", "its", "loc", "sgg", "etc"]:
            return HttpResponse("<h1>잘못된 도로 유형입니다.</h1>")

        if event_type not in ["all", "cor", "acc", "wea", "ete", "dis", "etc"]:
            return HttpResponse("<h1>잘못된 이벤트 유형입니다.</h1>")

        # 기본 파라미터
        params = {
            "apiKey": api_key,
            "type": road_type,
            "eventType": event_type,
            "getType": "json"
        }

    elif option == "traficInfo":
        api_key = input_params.get("api_key")
        road_type = input_params.get("road_type")
        routeNo = input_params.get("routeNo")
        drcType = input_params.get("drcType")
        if not api_key:
            return HttpResponse("<h1>API 키가 필요합니다.</h1>")

        if road_type not in ["all", "ex", "its", "loc", "sgg", "etc"]:
            return HttpResponse("<h1>잘못된 도로 유형입니다.</h1>")

        if routeNo != "all":
            try:
                int(routeNo)  # 정수 변환 시도
            except ValueError:
                return HttpResponse("<h1>잘못된 도로번호 유형입니다.</h1>")
        if drcType not in ["all", "up", "down", "start", "end"]:
            return HttpResponse("<h1>잘못된 도로 방향 유형입니다.</h1>")

        # 기본 파라미터
        params = {
            "apiKey": api_key,
            "type": road_type,
            "routeNo": routeNo,
            "drcType": drcType,
            "getType": "json"
        }

        # 검색 영역이 지정된 경우에만 좌표 파라미터 추가
    if bbox:
        params.update({
            "minX": bbox.get("minX"),
            "maxX": bbox.get("maxX"),
            "minY": bbox.get("minY"),
            "maxY": bbox.get("maxY")
        })
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # API 응답 코드 확인
        result_code = data['header'].get('resultCode')
        result_msg = data['header'].get('resultMsg')

        if result_code != 0:  # 실패
            return HttpResponse(f"""
                <h1>API 오류</h1>
                <p>응답 코드: {result_code}</p>
                <p>오류 메시지: {result_msg}</p>
            """)

        # 데이터가 없는 경우
        total_count = int(data['body'].get('totalCount', 0))
        if total_count == 0:
            return HttpResponse("<h1>조회된 데이터가 없습니다.</h1>")

        # body 데이터 확인
        df = pd.DataFrame(data['body']['items'])

        # 컬럼 매핑 정보 (API 응답의 실제 컬럼명에 맞게 수정)
        columns_map = {
            'roadname': '도로명',
            'enddate': '종료일시',
            'startdate': '발생일시',
            'eventtype': '이벤트유형',
            'eventdetailtype': '이벤트세부유형',
            'coordx': '경도',
            'coordy': '위도',
            'linkid': '링크ID',
            'roadno': '도로번호',
            'roaddrctype': '도로방향',
            'lanesblocktype': '차단유형',
            'lanesblocked': '차단차로',
            'message': '돌발내용',
            # 쿄통 소통 정보 추가 컬럼
            'speed': '통행 속도',
            'startnodeid': '시작노드ID',
            'endnodeid': '종료노드ID',
            'traveltime': '통행시간(초)',
            'createddate': '생성일시',
            'linkno': '링크번호',
        }

        # 대소문자를 무시하고 매핑
        df.columns = df.columns.str.lower()
        existing_columns = [col for col in columns_map.keys() if col in df.columns]

        # 컬럼 이름 변경
        df = df.rename(columns={col: columns_map[col] for col in existing_columns})

        # 날짜 포맷 변경 (YYYYMMDDHH24MISS -> YYYY-MM-DD HH:MM:SS)
        date_columns = ['발생일시', '종료일시','생성일시']#쿄통 소통 정보용 생성일시 추가
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:]}" if pd.notnull(x) and len(
                        str(x)) == 14 else x)

        # HTML 테이블 생성
        html_table = df.to_html(classes="table table-bordered", index=False)

        html_content = f"""
        <html>
          <head>
            <title>ITS 공사/사고정보</title>
            <style>
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .table th, .table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                .table th {{
                    background-color: #f5f5f5;
                }}
                .info {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
          </head>
          <body>
            <p><a href="/">[홈으로 돌아가기]</a></p>

            <div class="info">
                <h2>API 응답 정보</h2>
                <ul>
                    <li>응답 코드: {result_code}</li>
                    <li>응답 메시지: {result_msg}</li>
                    <li>총 데이터 수: {total_count}건</li>
                </ul>

                <h3>조회 조건</h3>
                <ul>
                    <li>도로 유형: {road_type}</li>
                    {f'<li>이벤트 유형: {event_type}</li>' if event_type else ''}
                    {f'<li>검색 영역: {bbox}</li>' if bbox else ''}
                </ul>
            </div>

            <h2>최종 호출 API URL</h2>
            <p>{response.url}</p>

            <h1>ITS 공사/사고정보 현황</h1>
            {html_table}
          </body>
        </html>
        """
        return HttpResponse(html_content)

    except requests.exceptions.RequestException as e:
        error_msg = f"""
        <h1>오류 발생</h1>
        <p>API 호출 중 오류가 발생했습니다: {str(e)}</p>
        <p>URL: {base_url}</p>
        """
        return HttpResponse(error_msg)


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


def collect_data_its_eventInfo(request):
    """
    [공사ㆍ사고정보 데이터]
    - ITS API를 통해 실시간 공사/사고 정보를 조회
    """
    base_url = "https://openapi.its.go.kr:9443/eventInfo"
    api_key = "25b9372d7c39424aa49f2c27c47c6276"  # 실제 ITS API 키로 교체 필요

    # 서울시 영역 좌표 (선택적)
    seoul_bbox = {
        "minX": "126.734086",
        "maxX": "127.269311",
        "minY": "37.413294",
        "maxY": "37.715133"
    }

    # URL 파라미터에서 도로/이벤트 유형 가져오기 (기본값: all)
    road_type = request.GET.get('road_type', 'all')
    event_type = request.GET.get('event_type', 'all')

    return _its_collect_logic(
        request=request,
        input_params={
            "base_url":base_url,
            "api_key":api_key,
            "road_type":road_type,
            "event_type":event_type,
            "option" : "eventInfo"
        },
        bbox=seoul_bbox
    )

def collect_data_its_traficInfo(request):
    """
    [공사ㆍ사고정보 데이터]
    - ITS API를 통해 5분단위 교통 소통 정보 조회
    """
    base_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = "25b9372d7c39424aa49f2c27c47c6276"  # 실제 ITS API 키로 교체 필요

    # 서울시 영역 좌표 (선택적)
    seoul_bbox = {
        "minX": "126.734086",
        "maxX": "127.269311",
        "minY": "37.413294",
        "maxY": "37.715133"
    }

    # URL 파라미터에서 도로/이벤트 유형 가져오기 (기본값: all)
    road_type = request.GET.get('road_type', 'all')
    routeNo = request.GET.get('routeNo', 'all')
    drcType = request.GET.get('drcType', 'all')


    return _its_collect_logic(
        request=request,
        input_params={
            "base_url":base_url,
            "api_key":api_key,
            "road_type":road_type,
            "routeNo":routeNo,
            "drcType":drcType,
            "option" : "traficInfo"
        },
        bbox=seoul_bbox
    )

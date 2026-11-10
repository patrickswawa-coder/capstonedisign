# RiskZero Risk Fusion 분석 모듈
# 영상 분석 결과 + 센서 분석 결과 융합

from pathlib import Path
import json


# =========================================================
# 기본 설정
# =========================================================

# 영상 이벤트와 센서 이벤트를
# 같은 위험 상황으로 판단할 최대 시간 차이
MATCH_THRESHOLD_SECONDS = 1.0


# =========================================================
# Risk Fusion 실행 함수
# =========================================================

def analyze_fusion(
    video_result: dict,
    sensor_result: dict,
    output_path: str
) -> dict:

    # -----------------------------------------------------
    # 입력 데이터 확인
    # -----------------------------------------------------

    if not isinstance(video_result, dict):
        raise ValueError(
            "video_result는 dict 형식이어야 합니다."
        )

    if not isinstance(sensor_result, dict):
        raise ValueError(
            "sensor_result는 dict 형식이어야 합니다."
        )


    # 영상 위험 이벤트 가져오기
    video_events = video_result.get(
        "risk_events",
        []
    )


    # 센서 위험 이벤트 가져오기
    sensor_events = sensor_result.get(
        "risk_events",
        []
    )


    matched_events = []

    unmatched_video_events = []

    unmatched_sensor_events = []


    # 이미 매칭된 센서 이벤트 인덱스 저장
    used_sensor_indexes = set()


    # =====================================================
    # 영상 이벤트와 센서 이벤트 시간 기준 매칭
    # =====================================================

    for video_event in video_events:

        video_timestamp = float(
            video_event.get(
                "timestamp",
                0.0
            )
        )


        best_sensor_index = None

        best_time_difference = None


        # 현재 영상 이벤트와 가장 가까운 센서 이벤트 탐색
        for sensor_index, sensor_event in enumerate(
            sensor_events
        ):

            # 이미 다른 영상 이벤트와 매칭된 센서 이벤트는 제외
            if sensor_index in used_sensor_indexes:
                continue


            sensor_timestamp = float(
                sensor_event.get(
                    "timestamp",
                    0.0
                )
            )


            time_difference = abs(
                video_timestamp
                - sensor_timestamp
            )


            # 허용 시간 범위를 벗어나면 제외
            if (
                time_difference
                > MATCH_THRESHOLD_SECONDS
            ):
                continue


            # 현재까지 가장 가까운 이벤트 선택
            if (
                best_time_difference is None
                or time_difference < best_time_difference
            ):

                best_sensor_index = sensor_index

                best_time_difference = time_difference


        # -------------------------------------------------
        # 매칭된 센서 이벤트가 있는 경우
        # -------------------------------------------------

        if best_sensor_index is not None:

            sensor_event = sensor_events[
                best_sensor_index
            ]


            used_sensor_indexes.add(
                best_sensor_index
            )


            video_risk_score = float(
                video_event.get(
                    "risk_score",
                    0.0
                )
            )


            sensor_risk_score = float(
                sensor_event.get(
                    "risk_score",
                    0.0
                )
            )


            # 현재는 가장 단순한 평균 방식
            # 추후 실제 Risk Fusion 알고리즘으로 변경
            fusion_risk_score = (
                video_risk_score
                + sensor_risk_score
            ) / 2


            fusion_risk_score = round(
                fusion_risk_score,
                3
            )


            matched_event = {

                "video_timestamp": video_timestamp,

                "sensor_timestamp": float(
                    sensor_event.get(
                        "timestamp",
                        0.0
                    )
                ),

                "time_difference": round(
                    best_time_difference,
                    3
                ),

                "video_event_type": video_event.get(
                    "event_type",
                    "unknown"
                ),

                "sensor_event_type": sensor_event.get(
                    "event_type",
                    "unknown"
                ),

                "video_risk_score": video_risk_score,

                "sensor_risk_score": sensor_risk_score,

                "fusion_risk_score": fusion_risk_score
            }


            matched_events.append(
                matched_event
            )


        # -------------------------------------------------
        # 매칭된 센서 이벤트가 없는 경우
        # -------------------------------------------------

        else:

            unmatched_video_events.append(
                video_event
            )


    # =====================================================
    # 매칭되지 않은 센서 이벤트 저장
    # =====================================================

    for sensor_index, sensor_event in enumerate(
        sensor_events
    ):

        if sensor_index not in used_sensor_indexes:

            unmatched_sensor_events.append(
                sensor_event
            )


    # =====================================================
    # 전체 위험도 계산
    # =====================================================

    all_risk_scores = []


    # 매칭된 융합 이벤트 위험도
    for event in matched_events:

        all_risk_scores.append(
            event[
                "fusion_risk_score"
            ]
        )


    # 매칭되지 않은 영상 위험도
    for event in unmatched_video_events:

        all_risk_scores.append(
            float(
                event.get(
                    "risk_score",
                    0.0
                )
            )
        )


    # 매칭되지 않은 센서 위험도
    for event in unmatched_sensor_events:

        all_risk_scores.append(
            float(
                event.get(
                    "risk_score",
                    0.0
                )
            )
        )


    # 위험 이벤트가 하나라도 있으면 평균 계산
    if all_risk_scores:

        overall_risk_score = round(
            sum(all_risk_scores)
            / len(all_risk_scores),
            3
        )

    else:

        overall_risk_score = 0.0


    # =====================================================
    # 최종 Fusion 결과
    # =====================================================

    result = {

        "matched_event_count": len(
            matched_events
        ),

        "unmatched_video_event_count": len(
            unmatched_video_events
        ),

        "unmatched_sensor_event_count": len(
            unmatched_sensor_events
        ),

        "matched_events": matched_events,

        "unmatched_video_events": unmatched_video_events,

        "unmatched_sensor_events": unmatched_sensor_events,

        "overall_risk_score": overall_risk_score
    }


    # =====================================================
    # JSON 파일 저장
    # =====================================================

    result_path = Path(
        output_path
    )


    result_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        result_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=4
        )


    return result
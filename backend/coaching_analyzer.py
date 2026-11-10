# RiskZero Coaching 분석 모듈
# Safety Score + Risk Fusion 결과를 기반으로
# 맞춤형 안전운전 코칭 생성


# =========================================================
# 점수 등급별 요약 메시지
# =========================================================

GRADE_SUMMARIES = {
    "excellent": (
        "전반적으로 매우 안정적인 운전 패턴이 확인되었습니다. "
        "현재의 안전운전 습관을 유지하세요."
    ),

    "good": (
        "전반적으로 안정적인 운전이 확인되었습니다. "
        "일부 위험 행동을 줄이면 더욱 안전한 주행이 가능합니다."
    ),

    "normal": (
        "일부 주행 구간에서 위험 행동이 감지되었습니다. "
        "주행 습관을 점검할 필요가 있습니다."
    ),

    "caution": (
        "주의가 필요한 운전 패턴이 여러 차례 감지되었습니다. "
        "급격한 차량 조작과 전방 위험 상황에 주의하세요."
    ),

    "danger": (
        "위험도가 높은 운전 패턴이 확인되었습니다. "
        "안전거리 확보와 급격한 차량 조작 개선이 필요합니다."
    )
}


# =========================================================
# 이벤트별 코칭 메시지
# =========================================================

EVENT_COACHING = {

    "front_vehicle_risk": (
        "전방 차량과의 안전거리를 충분히 확보하고, "
        "앞차의 움직임을 미리 확인하세요."
    ),

    "hard_acceleration": (
        "급가속을 줄이고 가속 페달을 부드럽게 조작하세요."
    ),

    "hard_braking": (
        "급제동을 줄이기 위해 전방 상황을 미리 확인하고 "
        "충분한 제동거리를 확보하세요."
    ),

    "hard_cornering": (
        "급회전을 피하고 코너 진입 전에 충분히 감속하세요."
    ),

    "lane_departure": (
        "차선을 안정적으로 유지하고 차선 변경 전 "
        "주변 차량을 충분히 확인하세요."
    ),

    "pedestrian_risk": (
        "보행자가 있는 구간에서는 속도를 줄이고 "
        "갑작스러운 보행자 진입에 대비하세요."
    )
}


# =========================================================
# 기본 코칭 메시지
# =========================================================

DEFAULT_COACHING = (
    "위험 이벤트가 감지되었습니다. "
    "주변 교통 상황을 충분히 확인하고 안정적으로 운전하세요."
)


# =========================================================
# 중복 코칭 방지 함수
# =========================================================

def add_recommendation(
    recommendations: list,
    message: str
):

    if message not in recommendations:
        recommendations.append(
            message
        )


# =========================================================
# Coaching 생성 함수
# =========================================================

def generate_coaching(
    fusion_result: dict,
    score_result: dict
) -> dict:

    # -----------------------------------------------------
    # 입력 데이터 검증
    # -----------------------------------------------------

    if not isinstance(
        fusion_result,
        dict
    ):

        raise ValueError(
            "fusion_result는 dict 형식이어야 합니다."
        )


    if not isinstance(
        score_result,
        dict
    ):

        raise ValueError(
            "score_result는 dict 형식이어야 합니다."
        )


    # =====================================================
    # Safety Score 정보
    # =====================================================

    safety_score = float(
        score_result.get(
            "safety_score",
            0.0
        )
    )


    grade = score_result.get(
        "grade",
        "normal"
    )


    summary = GRADE_SUMMARIES.get(
        grade,
        GRADE_SUMMARIES[
            "normal"
        ]
    )


    # =====================================================
    # Fusion 이벤트 가져오기
    # =====================================================

    matched_events = fusion_result.get(
        "matched_events",
        []
    )


    unmatched_video_events = fusion_result.get(
        "unmatched_video_events",
        []
    )


    unmatched_sensor_events = fusion_result.get(
        "unmatched_sensor_events",
        []
    )


    recommendations = []

    detected_patterns = []


    # =====================================================
    # 1. 영상 + 센서 매칭 이벤트 분석
    # =====================================================

    for event in matched_events:

        video_event_type = event.get(
            "video_event_type",
            "unknown"
        )


        sensor_event_type = event.get(
            "sensor_event_type",
            "unknown"
        )


        fusion_risk_score = float(
            event.get(
                "fusion_risk_score",
                0.0
            )
        )


        # 감지 패턴 저장
        detected_patterns.append({

            "type": "matched",

            "video_event_type": video_event_type,

            "sensor_event_type": sensor_event_type,

            "risk_score": fusion_risk_score
        })


        # 영상 이벤트 코칭
        if video_event_type in EVENT_COACHING:

            add_recommendation(
                recommendations,
                EVENT_COACHING[
                    video_event_type
                ]
            )


        # 센서 이벤트 코칭
        if sensor_event_type in EVENT_COACHING:

            add_recommendation(
                recommendations,
                EVENT_COACHING[
                    sensor_event_type
                ]
            )


    # =====================================================
    # 2. 영상 단독 이벤트 분석
    # =====================================================

    for event in unmatched_video_events:

        event_type = event.get(
            "event_type",
            "unknown"
        )


        risk_score = float(
            event.get(
                "risk_score",
                0.0
            )
        )


        detected_patterns.append({

            "type": "video_only",

            "event_type": event_type,

            "risk_score": risk_score
        })


        if event_type in EVENT_COACHING:

            add_recommendation(
                recommendations,
                EVENT_COACHING[
                    event_type
                ]
            )

        else:

            add_recommendation(
                recommendations,
                DEFAULT_COACHING
            )


    # =====================================================
    # 3. 센서 단독 이벤트 분석
    # =====================================================

    for event in unmatched_sensor_events:

        event_type = event.get(
            "event_type",
            "unknown"
        )


        risk_score = float(
            event.get(
                "risk_score",
                0.0
            )
        )


        detected_patterns.append({

            "type": "sensor_only",

            "event_type": event_type,

            "risk_score": risk_score
        })


        if event_type in EVENT_COACHING:

            add_recommendation(
                recommendations,
                EVENT_COACHING[
                    event_type
                ]
            )

        else:

            add_recommendation(
                recommendations,
                DEFAULT_COACHING
            )


    # =====================================================
    # 위험 이벤트가 없는 경우
    # =====================================================

    if len(
        recommendations
    ) == 0:

        recommendations.append(
            "특별한 위험 운전 패턴이 감지되지 않았습니다. "
            "현재의 안전운전 습관을 유지하세요."
        )


    # =====================================================
    # 위험 이벤트 수
    # =====================================================

    total_risk_events = (
        len(
            matched_events
        )
        + len(
            unmatched_video_events
        )
        + len(
            unmatched_sensor_events
        )
    )


    # =====================================================
    # 위험 수준 결정
    # =====================================================

    if safety_score >= 90:

        risk_level = "very_low"

    elif safety_score >= 80:

        risk_level = "low"

    elif safety_score >= 70:

        risk_level = "medium"

    elif safety_score >= 60:

        risk_level = "high"

    else:

        risk_level = "very_high"


    # =====================================================
    # 최종 Coaching 결과
    # =====================================================

    result = {

        "safety_score": safety_score,

        "grade": grade,

        "risk_level": risk_level,

        "summary": summary,

        "total_risk_events": total_risk_events,

        "recommendations": recommendations,

        "detected_patterns": detected_patterns
    }


    return result
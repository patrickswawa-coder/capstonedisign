# RiskZero Safety Score 분석 모듈
# Risk Fusion 결과를 기반으로 안전운전 점수 계산


# =========================================================
# 기본 설정
# =========================================================

BASE_SCORE = 100.0


# 융합 이벤트는
# 영상 + 센서에서 동시에 확인된 위험상황이므로
# 가장 높은 가중치 적용
MATCHED_EVENT_WEIGHT = 25.0


# 영상에서만 감지된 위험 이벤트
VIDEO_EVENT_WEIGHT = 15.0


# 센서에서만 감지된 위험 이벤트
SENSOR_EVENT_WEIGHT = 12.0


# =========================================================
# 점수 등급 계산
# =========================================================

def get_score_grade(
    safety_score: float
) -> str:

    if safety_score >= 90:
        return "excellent"

    if safety_score >= 80:
        return "good"

    if safety_score >= 70:
        return "normal"

    if safety_score >= 60:
        return "caution"

    return "danger"


# =========================================================
# Safety Score 계산
# =========================================================

def calculate_safety_score(
    fusion_result: dict
) -> dict:

    # -----------------------------------------------------
    # 입력값 검증
    # -----------------------------------------------------

    if not isinstance(
        fusion_result,
        dict
    ):

        raise ValueError(
            "fusion_result는 dict 형식이어야 합니다."
        )


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


    # =====================================================
    # 1. 영상 + 센서 융합 이벤트 감점
    # =====================================================

    matched_event_penalty = 0.0


    for event in matched_events:

        risk_score = float(
            event.get(
                "fusion_risk_score",
                0.0
            )
        )


        # 위험도 범위 보호
        risk_score = max(
            0.0,
            min(
                risk_score,
                1.0
            )
        )


        penalty = (
            risk_score
            * MATCHED_EVENT_WEIGHT
        )


        matched_event_penalty += penalty


    # =====================================================
    # 2. 영상 단독 위험 이벤트 감점
    # =====================================================

    video_event_penalty = 0.0


    for event in unmatched_video_events:

        risk_score = float(
            event.get(
                "risk_score",
                0.0
            )
        )


        risk_score = max(
            0.0,
            min(
                risk_score,
                1.0
            )
        )


        penalty = (
            risk_score
            * VIDEO_EVENT_WEIGHT
        )


        video_event_penalty += penalty


    # =====================================================
    # 3. 센서 단독 위험 이벤트 감점
    # =====================================================

    sensor_event_penalty = 0.0


    for event in unmatched_sensor_events:

        risk_score = float(
            event.get(
                "risk_score",
                0.0
            )
        )


        risk_score = max(
            0.0,
            min(
                risk_score,
                1.0
            )
        )


        penalty = (
            risk_score
            * SENSOR_EVENT_WEIGHT
        )


        sensor_event_penalty += penalty


    # =====================================================
    # 4. 전체 감점 계산
    # =====================================================

    total_penalty = (
        matched_event_penalty
        + video_event_penalty
        + sensor_event_penalty
    )


    # =====================================================
    # 5. 안전운전 점수 계산
    # =====================================================

    safety_score = (
        BASE_SCORE
        - total_penalty
    )


    # 0 ~ 100 범위 제한
    safety_score = max(
        0.0,
        min(
            safety_score,
            100.0
        )
    )


    safety_score = round(
        safety_score,
        1
    )


    # =====================================================
    # 6. 등급 계산
    # =====================================================

    grade = get_score_grade(
        safety_score
    )


    # =====================================================
    # 7. 결과 반환
    # =====================================================

    result = {

        "safety_score": safety_score,

        "grade": grade,

        "base_score": BASE_SCORE,

        "total_penalty": round(
            total_penalty,
            2
        ),

        "penalty_breakdown": {

            "matched_event_penalty": round(
                matched_event_penalty,
                2
            ),

            "video_event_penalty": round(
                video_event_penalty,
                2
            ),

            "sensor_event_penalty": round(
                sensor_event_penalty,
                2
            )
        },

        "event_count": {

            "matched_events": len(
                matched_events
            ),

            "video_only_events": len(
                unmatched_video_events
            ),

            "sensor_only_events": len(
                unmatched_sensor_events
            )
        }
    }


    return result
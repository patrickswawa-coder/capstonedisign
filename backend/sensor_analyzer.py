# RiskZero 센서 분석 모듈
# 현재: Mock 센서 분석
# 추후: 실제 스마트폰 센서 분석 AI 연결

from pathlib import Path
import json
import time


BASE_DIR = Path(__file__).resolve().parent


def analyze_sensor(
    input_path: str,
    output_path: str
) -> dict:

    # 입력 CSV 존재 확인
    sensor_path = Path(
        input_path
    )


    if not sensor_path.is_file():

        raise FileNotFoundError(
            f"센서 CSV 파일을 찾을 수 없습니다: {input_path}"
        )


    # 현재는 실제 AI 대신 3초 대기
    time.sleep(3)


    # =====================================================
    # Mock 센서 분석 결과
    #
    # 추후 실제 분석 결과 형식도
    # 가능하면 이 구조를 유지
    # =====================================================

    result = {

        "hard_acceleration_count": 2,

        "hard_braking_count": 3,

        "hard_cornering_count": 1,

        "risk_events": [

            {
                "timestamp": 8.4,
                "event_type": "hard_acceleration",
                "risk_score": 0.61
            },

            {
                "timestamp": 12.7,
                "event_type": "hard_braking",
                "risk_score": 0.84
            },

            {
                "timestamp": 25.3,
                "event_type": "hard_cornering",
                "risk_score": 0.67
            }
        ]
    }


    # 결과 저장 경로
    result_path = Path(
        output_path
    )


    result_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # JSON 파일 저장
    with open(
        result_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=4
        )


    return result
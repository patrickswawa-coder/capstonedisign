
# RiskZero AI 분석 모듈
# 현재: JSON 기반 Mock AI
# 추후: 실제 영상 분석 AI 연결

from pathlib import Path
import json
import time


BASE_DIR = Path(__file__).resolve().parent


def analyze_video(
    input_path: str,
    output_path: str
) -> dict:

    # 입력 영상이 존재하는지 확인
    video_path = Path(input_path)

    if not video_path.is_file():
        raise FileNotFoundError(
            f"영상 파일을 찾을 수 없습니다: {input_path}"
        )

    # 현재는 Mock AI 분석
    time.sleep(3)

    # JSON 결과 파일 읽기
    json_path = BASE_DIR / "ai_result_example.json"

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as f:
        result = json.load(f)

    # 결과 저장 디렉터리 생성
    result_path = Path(output_path)
    result_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 분석 결과를 개별 JSON 파일로 저장
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

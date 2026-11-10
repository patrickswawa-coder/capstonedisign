# RiskZero 백엔드
# Trip + 영상 + 센서 + Risk Fusion + Safety Score + Coaching
# 통합 자동 분석 Pipeline

from datetime import datetime
from pathlib import Path
from uuid import uuid4
import json
import logging

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from ai_analyzer import analyze_video as run_video_ai_model
from sensor_analyzer import analyze_sensor as run_sensor_ai_model
from fusion_analyzer import analyze_fusion as run_fusion_model
from score_analyzer import calculate_safety_score
from coaching_analyzer import generate_coaching


# =========================================================
# FastAPI
# =========================================================

app = FastAPI(
    title="RiskZero Driving Risk AI API",
    version="1.0.0"
)

logger = logging.getLogger(__name__)


# =========================================================
# 기본 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent


VIDEO_UPLOAD_DIR = BASE_DIR / "uploads"
VIDEO_UPLOAD_DIR.mkdir(exist_ok=True)


SENSOR_UPLOAD_DIR = BASE_DIR / "sensor_uploads"
SENSOR_UPLOAD_DIR.mkdir(exist_ok=True)


VIDEO_RESULT_DIR = BASE_DIR / "results"
VIDEO_RESULT_DIR.mkdir(exist_ok=True)


SENSOR_RESULT_DIR = BASE_DIR / "sensor_results"
SENSOR_RESULT_DIR.mkdir(exist_ok=True)


FUSION_RESULT_DIR = BASE_DIR / "fusion_results"
FUSION_RESULT_DIR.mkdir(exist_ok=True)


SCORE_RESULT_DIR = BASE_DIR / "score_results"
SCORE_RESULT_DIR.mkdir(exist_ok=True)


COACHING_RESULT_DIR = BASE_DIR / "coaching_results"
COACHING_RESULT_DIR.mkdir(exist_ok=True)


# =========================================================
# 파일 설정
# =========================================================

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
}


ALLOWED_SENSOR_EXTENSIONS = {
    ".csv",
}


MAX_VIDEO_FILE_SIZE = 5 * 1024 * 1024 * 1024

MAX_SENSOR_FILE_SIZE = 500 * 1024 * 1024

CHUNK_SIZE = 8 * 1024 * 1024


# =========================================================
# 임시 메모리 저장소
#
# 서버 재시작 시 초기화됨
# 추후 PostgreSQL로 교체 예정
# =========================================================

videos = {}

sensors = {}

trips = {}


# =========================================================
# JSON 저장 함수
# =========================================================

def save_json(
    output_path: Path,
    data: dict
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# 기본 API
# =========================================================

@app.get("/")
def root():

    return {
        "message": "RiskZero Driving Risk AI API",
        "version": "1.0.0"
    }


# =========================================================
# Trip 상태 업데이트
# =========================================================

def update_trip_status(
    trip_id: str
):

    if trip_id not in trips:
        return


    trip = trips[
        trip_id
    ]


    pipeline_status = trip.get(
        "pipeline_status"
    )


    coaching_status = trip.get(
        "coaching_status"
    )


    score_status = trip.get(
        "score_status"
    )


    fusion_status = trip.get(
        "fusion_status"
    )


    video_status = trip.get(
        "video_status"
    )


    sensor_status = trip.get(
        "sensor_status"
    )


    # =====================================================
    # 통합 Pipeline 상태
    # =====================================================

    if pipeline_status == "running":

        trip[
            "status"
        ] = "analysis_running"

        return


    if pipeline_status == "failed":

        trip[
            "status"
        ] = "analysis_failed"

        return


    if pipeline_status == "completed":

        trip[
            "status"
        ] = "completed"

        return


    # =====================================================
    # Coaching 상태
    # =====================================================

    if coaching_status == "completed":

        trip[
            "status"
        ] = "coaching_completed"

        return


    if coaching_status == "analyzing":

        trip[
            "status"
        ] = "coaching_analyzing"

        return


    # =====================================================
    # Score 상태
    # =====================================================

    if score_status == "completed":

        trip[
            "status"
        ] = "score_completed"

        return


    if score_status == "analyzing":

        trip[
            "status"
        ] = "score_analyzing"

        return


    # =====================================================
    # Fusion 상태
    # =====================================================

    if fusion_status == "completed":

        trip[
            "status"
        ] = "fusion_completed"

        return


    if fusion_status == "analyzing":

        trip[
            "status"
        ] = "fusion_analyzing"

        return


    # =====================================================
    # 영상 + 센서 상태
    # =====================================================

    if (
        video_status == "completed"
        and sensor_status == "completed"
    ):

        trip[
            "status"
        ] = "analysis_completed"

        return


    if (
        video_status == "analyzing"
        or sensor_status == "analyzing"
    ):

        trip[
            "status"
        ] = "analyzing"

        return


    if video_status == "completed":

        trip[
            "status"
        ] = "video_analysis_completed"

        return


    if sensor_status == "completed":

        trip[
            "status"
        ] = "sensor_analysis_completed"

        return


# =========================================================
# 분석 결과 초기화
# =========================================================

def clear_downstream_results(
    trip: dict
):

    trip[
        "fusion_status"
    ] = None

    trip[
        "fusion_result"
    ] = None


    trip[
        "score_status"
    ] = None

    trip[
        "score_result"
    ] = None

    trip[
        "safety_score"
    ] = None


    trip[
        "coaching_status"
    ] = None

    trip[
        "coaching"
    ] = None


# =========================================================
# 1. Trip 생성
# =========================================================

@app.post("/trips")
def create_trip():

    trip_id = str(
        uuid4()
    )


    trips[
        trip_id
    ] = {

        "trip_id": trip_id,

        "created_at": datetime.now().isoformat(),

        "status": "created",

        # 통합 Pipeline
        "pipeline_status": None,

        # 영상
        "video_id": None,
        "video_status": None,
        "video_result": None,

        # 센서
        "sensor_id": None,
        "sensor_file": None,
        "sensor_status": None,
        "sensor_result": None,

        # Fusion
        "fusion_status": None,
        "fusion_result": None,

        # Safety Score
        "score_status": None,
        "score_result": None,
        "safety_score": None,

        # Coaching
        "coaching_status": None,
        "coaching": None,
    }


    return {

        "message": "Trip Created",

        "trip_id": trip_id,

        "status": "created"
    }


# =========================================================
# 2. Trip 조회
# =========================================================

@app.get("/trips/{trip_id}")
def get_trip(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    return trips[
        trip_id
    ]


# =========================================================
# 3. 영상 업로드
# =========================================================

@app.post("/trips/{trip_id}/video")
async def upload_trip_video(
    trip_id: str,
    file: UploadFile = File(...)
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "video_id"
    ] is not None:

        raise HTTPException(
            status_code=409,
            detail="이미 영상이 등록된 주행입니다."
        )


    original_filename = (
        file.filename
        or ""
    )


    extension = Path(
        original_filename
    ).suffix.lower()


    if extension not in ALLOWED_VIDEO_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "지원하지 않는 영상 형식입니다. "
                "mp4, avi, mov, mkv만 업로드할 수 있습니다."
            )
        )


    video_id = str(
        uuid4()
    )


    saved_filename = (
        f"{video_id}{extension}"
    )


    saved_path = (
        VIDEO_UPLOAD_DIR
        / saved_filename
    )


    file_size = 0


    try:

        with open(
            saved_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    CHUNK_SIZE
                )


                if not chunk:
                    break


                file_size += len(
                    chunk
                )


                if (
                    file_size
                    > MAX_VIDEO_FILE_SIZE
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "영상은 최대 "
                            "5GB까지 업로드 가능합니다."
                        )
                    )


                buffer.write(
                    chunk
                )


    except HTTPException:

        saved_path.unlink(
            missing_ok=True
        )

        raise


    except Exception:

        saved_path.unlink(
            missing_ok=True
        )


        logger.exception(
            "영상 업로드 실패"
        )


        raise HTTPException(
            status_code=500,
            detail="영상 저장 중 오류가 발생했습니다."
        )


    finally:

        await file.close()


    videos[
        video_id
    ] = {

        "video_id": video_id,

        "trip_id": trip_id,

        "original_filename": original_filename,

        "saved_filename": saved_filename,

        "saved_path": str(
            saved_path
        ),

        "size_bytes": file_size,

        "status": "uploaded",

        "result": None,
    }


    trip[
        "video_id"
    ] = video_id


    trip[
        "video_status"
    ] = "uploaded"


    trip[
        "status"
    ] = "video_uploaded"


    return {

        "message": "Video Upload Success",

        "trip_id": trip_id,

        "video_id": video_id,

        "original_filename": original_filename,

        "saved_filename": saved_filename,

        "size_mb": round(
            file_size
            / (1024 * 1024),
            2
        ),

        "status": "video_uploaded"
    }


# =========================================================
# 4. 센서 CSV 업로드
# =========================================================

@app.post("/trips/{trip_id}/sensor")
async def upload_trip_sensor(
    trip_id: str,
    file: UploadFile = File(...)
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "sensor_id"
    ] is not None:

        raise HTTPException(
            status_code=409,
            detail="이미 센서 데이터가 등록된 주행입니다."
        )


    original_filename = (
        file.filename
        or ""
    )


    extension = Path(
        original_filename
    ).suffix.lower()


    if extension not in ALLOWED_SENSOR_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "센서 데이터는 "
                "CSV 파일만 업로드할 수 있습니다."
            )
        )


    sensor_id = str(
        uuid4()
    )


    saved_filename = (
        f"{sensor_id}{extension}"
    )


    saved_path = (
        SENSOR_UPLOAD_DIR
        / saved_filename
    )


    file_size = 0


    try:

        with open(
            saved_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    CHUNK_SIZE
                )


                if not chunk:
                    break


                file_size += len(
                    chunk
                )


                if (
                    file_size
                    > MAX_SENSOR_FILE_SIZE
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "센서 CSV는 최대 "
                            "500MB까지 업로드 가능합니다."
                        )
                    )


                buffer.write(
                    chunk
                )


    except HTTPException:

        saved_path.unlink(
            missing_ok=True
        )

        raise


    except Exception:

        saved_path.unlink(
            missing_ok=True
        )


        logger.exception(
            "센서 CSV 업로드 실패"
        )


        raise HTTPException(
            status_code=500,
            detail="센서 파일 저장 중 오류가 발생했습니다."
        )


    finally:

        await file.close()


    sensors[
        sensor_id
    ] = {

        "sensor_id": sensor_id,

        "trip_id": trip_id,

        "original_filename": original_filename,

        "saved_filename": saved_filename,

        "saved_path": str(
            saved_path
        ),

        "size_bytes": file_size,

        "status": "uploaded",

        "result": None,
    }


    trip[
        "sensor_id"
    ] = sensor_id


    trip[
        "sensor_file"
    ] = str(
        saved_path
    )


    trip[
        "sensor_status"
    ] = "uploaded"


    trip[
        "status"
    ] = "sensor_uploaded"


    return {

        "message": "Sensor Upload Success",

        "trip_id": trip_id,

        "sensor_id": sensor_id,

        "original_filename": original_filename,

        "saved_filename": saved_filename,

        "size_mb": round(
            file_size
            / (1024 * 1024),
            2
        ),

        "status": "sensor_uploaded"
    }


# =========================================================
# 영상 분석 실행
# =========================================================

def run_video_analysis(
    video_id: str
):

    video = videos.get(
        video_id
    )


    if video is None:

        raise ValueError(
            "영상 정보를 찾을 수 없습니다."
        )


    trip_id = video.get(
        "trip_id"
    )


    input_path = video[
        "saved_path"
    ]


    output_path = str(
        VIDEO_RESULT_DIR
        / f"{video_id}.json"
    )


    try:

        video[
            "status"
        ] = "analyzing"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trip = trips[
                trip_id
            ]


            clear_downstream_results(
                trip
            )


            trip[
                "video_status"
            ] = "analyzing"


            update_trip_status(
                trip_id
            )


        result = run_video_ai_model(
            input_path=input_path,
            output_path=output_path
        )


        video[
            "result"
        ] = result


        video[
            "status"
        ] = "completed"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trips[
                trip_id
            ][
                "video_result"
            ] = result


            trips[
                trip_id
            ][
                "video_status"
            ] = "completed"


            update_trip_status(
                trip_id
            )


        return result


    except Exception:

        logger.exception(
            "영상 분석 실패: video_id=%s",
            video_id
        )


        video[
            "result"
        ] = None


        video[
            "status"
        ] = "failed"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trips[
                trip_id
            ][
                "video_status"
            ] = "failed"


        raise


# =========================================================
# 센서 분석 실행
# =========================================================

def run_sensor_analysis(
    sensor_id: str
):

    sensor = sensors.get(
        sensor_id
    )


    if sensor is None:

        raise ValueError(
            "센서 정보를 찾을 수 없습니다."
        )


    trip_id = sensor.get(
        "trip_id"
    )


    input_path = sensor[
        "saved_path"
    ]


    output_path = str(
        SENSOR_RESULT_DIR
        / f"{sensor_id}.json"
    )


    try:

        sensor[
            "status"
        ] = "analyzing"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trip = trips[
                trip_id
            ]


            clear_downstream_results(
                trip
            )


            trip[
                "sensor_status"
            ] = "analyzing"


            update_trip_status(
                trip_id
            )


        result = run_sensor_ai_model(
            input_path=input_path,
            output_path=output_path
        )


        sensor[
            "result"
        ] = result


        sensor[
            "status"
        ] = "completed"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trips[
                trip_id
            ][
                "sensor_result"
            ] = result


            trips[
                trip_id
            ][
                "sensor_status"
            ] = "completed"


            update_trip_status(
                trip_id
            )


        return result


    except Exception:

        logger.exception(
            "센서 분석 실패: sensor_id=%s",
            sensor_id
        )


        sensor[
            "result"
        ] = None


        sensor[
            "status"
        ] = "failed"


        if (
            trip_id is not None
            and trip_id in trips
        ):

            trips[
                trip_id
            ][
                "sensor_status"
            ] = "failed"


        raise


# =========================================================
# Fusion 실행
# =========================================================

def execute_fusion(
    trip_id: str
):

    if trip_id not in trips:

        raise ValueError(
            "Trip 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "video_result"
    ] is None:

        raise ValueError(
            "영상 분석 결과가 없습니다."
        )


    if trip[
        "sensor_result"
    ] is None:

        raise ValueError(
            "센서 분석 결과가 없습니다."
        )


    trip[
        "fusion_status"
    ] = "analyzing"


    update_trip_status(
        trip_id
    )


    output_path = str(
        FUSION_RESULT_DIR
        / f"{trip_id}.json"
    )


    try:

        result = run_fusion_model(

            video_result=trip[
                "video_result"
            ],

            sensor_result=trip[
                "sensor_result"
            ],

            output_path=output_path
        )


        trip[
            "fusion_result"
        ] = result


        trip[
            "fusion_status"
        ] = "completed"


        # Fusion이 변경되면
        # Score와 Coaching은 다시 계산해야 함
        trip[
            "score_status"
        ] = None

        trip[
            "score_result"
        ] = None

        trip[
            "safety_score"
        ] = None


        trip[
            "coaching_status"
        ] = None

        trip[
            "coaching"
        ] = None


        update_trip_status(
            trip_id
        )


        return result


    except Exception:

        logger.exception(
            "Risk Fusion 실패: trip_id=%s",
            trip_id
        )


        trip[
            "fusion_status"
        ] = "failed"


        trip[
            "fusion_result"
        ] = None


        raise


# =========================================================
# Safety Score 실행
# =========================================================

def execute_score(
    trip_id: str
):

    if trip_id not in trips:

        raise ValueError(
            "Trip 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "fusion_result"
    ] is None:

        raise ValueError(
            "Risk Fusion 결과가 없습니다."
        )


    trip[
        "score_status"
    ] = "analyzing"


    update_trip_status(
        trip_id
    )


    try:

        result = calculate_safety_score(
            trip[
                "fusion_result"
            ]
        )


        trip[
            "score_result"
        ] = result


        trip[
            "safety_score"
        ] = result[
            "safety_score"
        ]


        trip[
            "score_status"
        ] = "completed"


        # 점수가 바뀌면 Coaching도 다시 생성
        trip[
            "coaching_status"
        ] = None

        trip[
            "coaching"
        ] = None


        output_path = (
            SCORE_RESULT_DIR
            / f"{trip_id}.json"
        )


        save_json(
            output_path,
            result
        )


        update_trip_status(
            trip_id
        )


        return result


    except Exception:

        logger.exception(
            "Safety Score 계산 실패: trip_id=%s",
            trip_id
        )


        trip[
            "score_status"
        ] = "failed"


        trip[
            "score_result"
        ] = None


        trip[
            "safety_score"
        ] = None


        raise


# =========================================================
# Coaching 실행
# =========================================================

def execute_coaching(
    trip_id: str
):

    if trip_id not in trips:

        raise ValueError(
            "Trip 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "fusion_result"
    ] is None:

        raise ValueError(
            "Risk Fusion 결과가 없습니다."
        )


    if trip[
        "score_result"
    ] is None:

        raise ValueError(
            "Safety Score 결과가 없습니다."
        )


    trip[
        "coaching_status"
    ] = "analyzing"


    update_trip_status(
        trip_id
    )


    try:

        result = generate_coaching(

            fusion_result=trip[
                "fusion_result"
            ],

            score_result=trip[
                "score_result"
            ]
        )


        trip[
            "coaching"
        ] = result


        trip[
            "coaching_status"
        ] = "completed"


        output_path = (
            COACHING_RESULT_DIR
            / f"{trip_id}.json"
        )


        save_json(
            output_path,
            result
        )


        update_trip_status(
            trip_id
        )


        return result


    except Exception:

        logger.exception(
            "Coaching 생성 실패: trip_id=%s",
            trip_id
        )


        trip[
            "coaching_status"
        ] = "failed"


        trip[
            "coaching"
        ] = None


        raise


# =========================================================
# 통합 자동 분석 Pipeline
#
# 영상
# ↓
# 센서
# ↓
# Fusion
# ↓
# Safety Score
# ↓
# Coaching
# =========================================================

def run_trip_analysis(
    trip_id: str
):

    if trip_id not in trips:
        return


    trip = trips[
        trip_id
    ]


    video_id = trip.get(
        "video_id"
    )


    sensor_id = trip.get(
        "sensor_id"
    )


    try:

        trip[
            "pipeline_status"
        ] = "running"


        trip[
            "status"
        ] = "analysis_running"


        # 이전 분석 결과 초기화
        trip[
            "video_result"
        ] = None


        trip[
            "sensor_result"
        ] = None


        clear_downstream_results(
            trip
        )


        # =================================================
        # 1. 영상 분석
        # =================================================

        run_video_analysis(
            video_id
        )


        # =================================================
        # 2. 센서 분석
        # =================================================

        run_sensor_analysis(
            sensor_id
        )


        # =================================================
        # 3. Risk Fusion
        # =================================================

        execute_fusion(
            trip_id
        )


        # =================================================
        # 4. Safety Score
        # =================================================

        execute_score(
            trip_id
        )


        # =================================================
        # 5. Coaching
        # =================================================

        execute_coaching(
            trip_id
        )


        # =================================================
        # 전체 분석 완료
        # =================================================

        trip[
            "pipeline_status"
        ] = "completed"


        trip[
            "status"
        ] = "completed"


    except Exception:

        logger.exception(
            "통합 분석 실패: trip_id=%s",
            trip_id
        )


        trip[
            "pipeline_status"
        ] = "failed"


        trip[
            "status"
        ] = "analysis_failed"


# =========================================================
# 5. 통합 자동 분석 요청
# =========================================================

@app.post("/trips/{trip_id}/analyze")
def request_trip_analysis(
    trip_id: str,
    background_tasks: BackgroundTasks
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if trip[
        "video_id"
    ] is None:

        raise HTTPException(
            status_code=409,
            detail="영상이 업로드되지 않았습니다."
        )


    if trip[
        "sensor_id"
    ] is None:

        raise HTTPException(
            status_code=409,
            detail="센서 CSV가 업로드되지 않았습니다."
        )


    if (
        trip.get(
            "pipeline_status"
        )
        == "running"
    ):

        return {

            "message": "Trip Analysis Already Running",

            "trip_id": trip_id,

            "status": "analysis_running"
        }


    trip[
        "pipeline_status"
    ] = "running"


    trip[
        "status"
    ] = "analysis_running"


    background_tasks.add_task(
        run_trip_analysis,
        trip_id
    )


    return {

        "message": "Trip Analysis Started",

        "trip_id": trip_id,

        "status": "analysis_running"
    }


# =========================================================
# 6. 영상 개별 분석 요청
# =========================================================

@app.post("/videos/{video_id}/analyze")
def request_video_analysis(
    video_id: str,
    background_tasks: BackgroundTasks
):

    if video_id not in videos:

        raise HTTPException(
            status_code=404,
            detail="영상을 찾을 수 없습니다."
        )


    video = videos[
        video_id
    ]


    if (
        video[
            "status"
        ]
        == "analyzing"
    ):

        return {

            "message": "Analysis Already Running",

            "video_id": video_id,

            "status": "analyzing"
        }


    background_tasks.add_task(
        run_video_analysis,
        video_id
    )


    return {

        "message": "Video Analysis Started",

        "video_id": video_id,

        "trip_id": video.get(
            "trip_id"
        ),

        "status": "analyzing"
    }


# =========================================================
# 7. 센서 개별 분석 요청
# =========================================================

@app.post("/sensors/{sensor_id}/analyze")
def request_sensor_analysis(
    sensor_id: str,
    background_tasks: BackgroundTasks
):

    if sensor_id not in sensors:

        raise HTTPException(
            status_code=404,
            detail="센서 데이터를 찾을 수 없습니다."
        )


    sensor = sensors[
        sensor_id
    ]


    if (
        sensor[
            "status"
        ]
        == "analyzing"
    ):

        return {

            "message": "Sensor Analysis Already Running",

            "sensor_id": sensor_id,

            "status": "analyzing"
        }


    background_tasks.add_task(
        run_sensor_analysis,
        sensor_id
    )


    return {

        "message": "Sensor Analysis Started",

        "sensor_id": sensor_id,

        "trip_id": sensor.get(
            "trip_id"
        ),

        "status": "analyzing"
    }


# =========================================================
# 8. Fusion 개별 실행
# =========================================================

@app.post("/trips/{trip_id}/fusion")
def request_fusion_analysis(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "video_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="영상 분석이 완료되지 않았습니다."
        )


    if (
        trip[
            "sensor_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="센서 분석이 완료되지 않았습니다."
        )


    try:

        trip[
            "pipeline_status"
        ] = None


        result = execute_fusion(
            trip_id
        )


        return {

            "message": "Fusion Analysis Completed",

            "trip_id": trip_id,

            "status": "completed",

            "fusion_result": result
        }


    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Risk Fusion 처리 중 오류가 발생했습니다."
        )


# =========================================================
# 9. Safety Score 개별 실행
# =========================================================

@app.post("/trips/{trip_id}/score")
def request_safety_score(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "fusion_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Risk Fusion이 완료되지 않았습니다."
        )


    try:

        trip[
            "pipeline_status"
        ] = None


        result = execute_score(
            trip_id
        )


        return {

            "message": "Safety Score Calculated",

            "trip_id": trip_id,

            "status": "completed",

            "score_result": result
        }


    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Safety Score 계산 중 오류가 발생했습니다."
        )


# =========================================================
# 10. Coaching 개별 실행
# =========================================================

@app.post("/trips/{trip_id}/coaching")
def request_coaching(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "fusion_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Risk Fusion이 완료되지 않았습니다."
        )


    if (
        trip[
            "score_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Safety Score 계산이 완료되지 않았습니다."
        )


    try:

        trip[
            "pipeline_status"
        ] = None


        result = execute_coaching(
            trip_id
        )


        return {

            "message": "Coaching Generated",

            "trip_id": trip_id,

            "status": "completed",

            "coaching": result
        }


    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Coaching 생성 중 오류가 발생했습니다."
        )


# =========================================================
# 11. 영상 분석 상태 조회
# =========================================================

@app.get("/videos/{video_id}/status")
def get_video_analysis_status(
    video_id: str
):

    if video_id not in videos:

        raise HTTPException(
            status_code=404,
            detail="영상을 찾을 수 없습니다."
        )


    video = videos[
        video_id
    ]


    return {

        "video_id": video_id,

        "trip_id": video.get(
            "trip_id"
        ),

        "status": video[
            "status"
        ]
    }


# =========================================================
# 12. 영상 분석 결과 조회
# =========================================================

@app.get("/videos/{video_id}/result")
def get_video_analysis_result(
    video_id: str
):

    if video_id not in videos:

        raise HTTPException(
            status_code=404,
            detail="영상을 찾을 수 없습니다."
        )


    video = videos[
        video_id
    ]


    if (
        video[
            "status"
        ]
        == "failed"
    ):

        raise HTTPException(
            status_code=500,
            detail="영상 AI 분석 중 오류가 발생했습니다."
        )


    if (
        video[
            "status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="영상 AI 분석이 아직 완료되지 않았습니다."
        )


    return {

        "video_id": video_id,

        "trip_id": video.get(
            "trip_id"
        ),

        "status": video[
            "status"
        ],

        "result": video[
            "result"
        ]
    }


# =========================================================
# 13. 센서 분석 상태 조회
# =========================================================

@app.get("/sensors/{sensor_id}/status")
def get_sensor_analysis_status(
    sensor_id: str
):

    if sensor_id not in sensors:

        raise HTTPException(
            status_code=404,
            detail="센서 데이터를 찾을 수 없습니다."
        )


    sensor = sensors[
        sensor_id
    ]


    return {

        "sensor_id": sensor_id,

        "trip_id": sensor.get(
            "trip_id"
        ),

        "status": sensor[
            "status"
        ]
    }


# =========================================================
# 14. 센서 분석 결과 조회
# =========================================================

@app.get("/sensors/{sensor_id}/result")
def get_sensor_analysis_result(
    sensor_id: str
):

    if sensor_id not in sensors:

        raise HTTPException(
            status_code=404,
            detail="센서 데이터를 찾을 수 없습니다."
        )


    sensor = sensors[
        sensor_id
    ]


    if (
        sensor[
            "status"
        ]
        == "failed"
    ):

        raise HTTPException(
            status_code=500,
            detail="센서 분석 중 오류가 발생했습니다."
        )


    if (
        sensor[
            "status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="센서 분석이 아직 완료되지 않았습니다."
        )


    return {

        "sensor_id": sensor_id,

        "trip_id": sensor.get(
            "trip_id"
        ),

        "status": sensor[
            "status"
        ],

        "result": sensor[
            "result"
        ]
    }


# =========================================================
# 15. Fusion 결과 조회
# =========================================================

@app.get("/trips/{trip_id}/fusion")
def get_fusion_result(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "fusion_status"
        ]
        == "failed"
    ):

        raise HTTPException(
            status_code=500,
            detail="Risk Fusion 처리 중 오류가 발생했습니다."
        )


    if (
        trip[
            "fusion_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Risk Fusion이 아직 완료되지 않았습니다."
        )


    return {

        "trip_id": trip_id,

        "status": trip[
            "fusion_status"
        ],

        "fusion_result": trip[
            "fusion_result"
        ]
    }


# =========================================================
# 16. Safety Score 결과 조회
# =========================================================

@app.get("/trips/{trip_id}/score")
def get_safety_score(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "score_status"
        ]
        == "failed"
    ):

        raise HTTPException(
            status_code=500,
            detail="Safety Score 계산 중 오류가 발생했습니다."
        )


    if (
        trip[
            "score_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Safety Score가 아직 계산되지 않았습니다."
        )


    return {

        "trip_id": trip_id,

        "status": trip[
            "score_status"
        ],

        "score_result": trip[
            "score_result"
        ]
    }


# =========================================================
# 17. Coaching 결과 조회
# =========================================================

@app.get("/trips/{trip_id}/coaching")
def get_coaching(
    trip_id: str
):

    if trip_id not in trips:

        raise HTTPException(
            status_code=404,
            detail="주행 정보를 찾을 수 없습니다."
        )


    trip = trips[
        trip_id
    ]


    if (
        trip[
            "coaching_status"
        ]
        == "failed"
    ):

        raise HTTPException(
            status_code=500,
            detail="Coaching 생성 중 오류가 발생했습니다."
        )


    if (
        trip[
            "coaching_status"
        ]
        != "completed"
    ):

        raise HTTPException(
            status_code=409,
            detail="Coaching이 아직 생성되지 않았습니다."
        )


    return {

        "trip_id": trip_id,

        "status": trip[
            "coaching_status"
        ],

        "coaching": trip[
            "coaching"
        ]
    }
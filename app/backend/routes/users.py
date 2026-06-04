"""
Users Router - Endpoint quản lý hồ sơ người dùng (personas)
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["Users"])

# Đường dẫn đến mock database
DATA_PATH = Path(__file__).parent.parent / "data" / "mock_db.json"


# ============================================================
# Pydantic Models
# ============================================================
class TastePreferences(BaseModel):
    """Sở thích khẩu vị"""
    preferred: list[str]
    disliked: list[str]


class UserSummary(BaseModel):
    """Thông tin tóm tắt user (cho danh sách)"""
    id: str
    name: str
    avatar: str
    demographic: str


class UserProfile(BaseModel):
    """Hồ sơ đầy đủ của user"""
    id: str
    name: str
    avatar: str
    demographic: str
    cohort: str
    location: str
    avg_order_value_limit: int
    taste_preferences: TastePreferences
    allergies: list[str]


class UserListResponse(BaseModel):
    """Response cho danh sách users"""
    users: list[UserSummary]
    total: int


# ============================================================
# Helper functions
# ============================================================
def _load_users() -> dict:
    """Đọc dữ liệu users từ mock database"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
            return db.get("users", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc database: {str(e)}")


# ============================================================
# Endpoints
# ============================================================
@router.get("", response_model=UserListResponse)
async def list_users() -> UserListResponse:
    """
    Lấy danh sách tất cả user personas (thông tin tóm tắt).

    Trả về id, name, avatar, demographic cho mỗi user.
    """
    users_data = _load_users()

    summaries: list[UserSummary] = []
    for user_id, user_info in users_data.items():
        summaries.append(
            UserSummary(
                id=user_info["id"],
                name=user_info["name"],
                avatar=user_info["avatar"],
                demographic=user_info["demographic"],
            )
        )

    return UserListResponse(users=summaries, total=len(summaries))


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str) -> UserProfile:
    """
    Lấy hồ sơ đầy đủ của một user persona.

    - **user_id**: ID của user, ví dụ student_hoc_sinh, university_student, office_worker
    """
    users_data = _load_users()

    user_info = users_data.get(user_id)
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy người dùng với ID: {user_id}",
        )

    return UserProfile(**user_info)

"""
Chat Router - Endpoint xử lý hội thoại với AI Copilot
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.gemini_service import gemini_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Đường dẫn đến mock database
DATA_PATH = Path(__file__).parent.parent / "data" / "mock_db.json"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_MOCK_DATA_PATH = PROJECT_ROOT / "ai_chat_mock_data.json"


# ============================================================
# Pydantic Models - Request / Response
# ============================================================
class ConversationEntry(BaseModel):
    """Một entry trong lịch sử hội thoại"""
    role: str = Field(..., description="'user' hoặc 'assistant'")
    content: str = Field(..., description="Nội dung tin nhắn")


class ChatRequest(BaseModel):
    """Request body cho endpoint chat"""
    user_id: str = Field(..., description="ID của user persona")
    message: str = Field(..., min_length=1, description="Tin nhắn từ người dùng")
    conversation_history: list[ConversationEntry] = Field(
        default_factory=list,
        description="Lịch sử hội thoại trước đó",
    )


class FoodSuggestion(BaseModel):
    """Thông tin món ăn được gợi ý"""
    id: str
    name: str
    shop: str
    price: int
    rating: float
    distance: str
    eta: str
    image: str
    image_alt: str = ""
    budget_tier: str
    taste_tags: list[str]
    allergy_tags: list[str]
    description: str
    category: str


class ChatResponse(BaseModel):
    """Response trả về cho client"""
    response: str = Field(..., description="Phản hồi từ AI")
    suggested_foods: list[FoodSuggestion] = Field(
        default_factory=list,
        description="Danh sách món ăn được gợi ý",
    )
    timestamp: str = Field(..., description="Thời gian phản hồi ISO 8601")


# ============================================================
# Helper functions
# ============================================================
def _load_database() -> dict:
    """Đọc mock database từ file JSON"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Không tìm thấy file database. Kiểm tra data/mock_db.json",
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="File database bị lỗi format JSON",
        )


def _load_ai_mock_data() -> dict:
    """Đọc mock data lớn dùng làm context cho LLM."""
    try:
        with open(AI_MOCK_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="File ai_chat_mock_data.json bị lỗi format JSON",
        )


def _normalize_cohort(cohort: str) -> str:
    """Đưa cohort trong mock mới về 3 nhóm frontend đang dùng."""
    if cohort == "university":
        return "student"
    return cohort


def _budget_tier(price: int) -> str:
    if price <= 30000:
        return "low"
    if price <= 60000:
        return "medium"
    return "high"


def _allergy_tags_from_ingredients(ingredients: list[str]) -> list[str]:
    tags: list[str] = []
    allergen_keywords = {
        "đậu phộng": "Đậu phộng",
        "đậu nành": "Đậu nành",
        "soy": "Đậu nành",
        "sữa": "Sữa",
        "phô mai": "Sữa",
        "trứng": "Trứng",
        "tép": "Hải sản",
        "mực": "Hải sản",
        "seafood": "Hải sản",
    }

    joined = " ".join(ingredients).lower()
    for keyword, label in allergen_keywords.items():
        if keyword in joined and label not in tags:
            tags.append(label)
    return tags


def _taste_tags_from_item(item: dict, restaurant: dict) -> list[str]:
    tags: list[str] = []
    item_text = item.get("name", "").lower()
    cuisine_text = restaurant.get("cuisine", "").lower()

    keyword_tags = {
        "trà sữa": "Trà sữa",
        "trà đào": "Giải khát",
        "trà vải": "Giải khát",
        "trà ô long": "Giải khát",
        "matcha": "Trà sữa",
        "nước ép": "Giải khát",
        "sinh tố": "Giải khát",
        "detox": "Healthy",
        "cold brew": "Cà phê",
        "bạc xỉu": "Cà phê",
        "sữa chua": "Ngọt",
        "chè": "Ngọt",
        "flan": "Ngọt",
        "tàu hũ": "Ngọt",
        "bánh tráng": "Ăn vặt",
        "nem": "Ăn vặt",
        "khoai": "Ăn vặt",
        "cá viên": "Ăn vặt",
        "phô mai": "Ăn vặt",
        "tokbokki": "Ăn vặt",
        "cơm cuộn": "Ăn vặt",
        "mì": "Mì trộn",
        "udon": "Mì trộn",
        "cơm": "Cơm trưa",
        "bento": "Cơm trưa",
        "xôi": "Cơm trưa",
        "bánh mì": "Bữa sáng",
        "salad": "Healthy",
        "gạo lứt": "Healthy",
        "yến mạch": "Healthy",
        "healthy": "Healthy",
        "chay": "Healthy",
        "cà phê": "Cà phê",
        "trà chanh": "Giải khát",
        "nước": "Giải khát",
        "phở": "Truyền thống",
        "bún": "Truyền thống",
        "cháo": "Truyền thống",
        "miến": "Truyền thống",
        "gà": "Giòn",
    }
    for keyword, tag in keyword_tags.items():
        if keyword == "mì" and "bánh mì" in item_text:
            continue
        if keyword in item_text and tag not in tags:
            tags.append(tag)

    cuisine_tags = {
        "ăn vặt": "Ăn vặt",
        "cơm": "Cơm trưa",
        "nước ép": "Giải khát",
        "sinh tố": "Giải khát",
        "detox": "Healthy",
        "trà": "Giải khát",
        "bánh mì": "Bữa sáng",
        "bữa sáng": "Bữa sáng",
        "xôi": "Cơm trưa",
        "món chay": "Healthy",
        "cà phê": "Cà phê",
        "bún": "Truyền thống",
        "phở": "Truyền thống",
        "cháo": "Truyền thống",
    }
    for keyword, tag in cuisine_tags.items():
        if keyword in cuisine_text and tag not in tags:
            tags.append(tag)

    if item.get("is_healthy") and "Healthy" not in tags:
        tags.append("Healthy")

    spicy_level = item.get("spicy_level", 0)
    tags.append("Không cay" if spicy_level == 0 else "Có cay")

    return tags or [restaurant.get("cuisine", "Món ăn")]


def _flatten_restaurant_menu(ai_mock_data: dict) -> list[dict]:
    """Chuyển restaurants[].menu[] từ mock mới thành food_catalog cho frontend."""
    foods: list[dict] = []
    for restaurant in ai_mock_data.get("restaurants", []):
        distance = restaurant.get("distance_km", 0)
        eta = restaurant.get("eta_minutes", 0)
        for item in restaurant.get("menu", []):
            price = int(item.get("price_new") or item.get("price_old") or 0)
            ingredients = item.get("ingredients", [])
            food_id = item.get("id")
            if not food_id:
                continue

            foods.append(
                {
                    "id": food_id,
                    "name": item.get("name", "Món ăn"),
                    "shop": restaurant.get("name", "ShopeeFood Partner"),
                    "price": price,
                    "rating": float(restaurant.get("rating", 0)),
                    "distance": f"{distance} km",
                    "eta": f"{eta} phút",
                    "image": item.get("image_url", ""),
                    "image_alt": item.get("image_alt", item.get("name", "Món ăn")),
                    "budget_tier": _budget_tier(price),
                    "taste_tags": _taste_tags_from_item(item, restaurant),
                    "is_healthy": bool(item.get("is_healthy")),
                    "allergy_tags": _allergy_tags_from_ingredients(ingredients),
                    "description": (
                        f"{item.get('name', 'Món ăn')} từ {restaurant.get('name', 'quán')}. "
                        f"Thành phần: {', '.join(ingredients) if ingredients else 'đang cập nhật'}."
                    ),
                    "category": restaurant.get("cuisine", "Món ăn"),
                }
            )
    return foods


def _select_runtime_user(requested_user: dict, ai_mock_data: dict) -> dict:
    """
    Ghép persona đang chọn ở frontend với một user mẫu trong mock lớn.
    Giữ nguyên id frontend để các endpoint hiện tại không vỡ.
    """
    users = ai_mock_data.get("users", [])
    if not users:
        return requested_user

    target_cohort = requested_user.get("cohort")
    if target_cohort == "pupil":
        candidate = next((u for u in users if u.get("cohort") == "student"), None)
    elif target_cohort == "student":
        candidate = next((u for u in users if u.get("cohort") == "university"), None)
    else:
        candidate = next((u for u in users if u.get("cohort") == "office"), None)

    if not candidate:
        return requested_user

    merged = dict(requested_user)
    merged["llm_mock_profile"] = candidate
    merged["budget_preference"] = candidate.get("budget_preference")
    merged["preferences"] = candidate.get("preferences")
    merged["cohort_for_prompt"] = _normalize_cohort(candidate.get("cohort", target_cohort))
    return merged


# ============================================================
# Endpoints
# ============================================================
@router.post("", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """
    Gửi tin nhắn đến ShopeeFood AI Copilot và nhận gợi ý món ăn.

    - Tự động load hồ sơ người dùng và catalog món ăn
    - Trả về response kèm danh sách món gợi ý chi tiết
    """
    # Load database
    db = _load_database()
    ai_mock_data = _load_ai_mock_data()

    # Lấy user profile
    user_profile = db.get("users", {}).get(request.user_id)
    if not user_profile:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy người dùng với ID: {request.user_id}",
        )

    # Lấy food catalog. Ưu tiên ghép thêm restaurant menu từ mock data mới.
    food_catalog: list[dict] = [
        *db.get("food_catalog", []),
        *_flatten_restaurant_menu(ai_mock_data),
    ]
    runtime_user_profile = _select_runtime_user(user_profile, ai_mock_data)

    # Chuyển conversation_history thành list[dict]
    history = [entry.model_dump() for entry in request.conversation_history]

    # Gọi Gemini service
    ai_result = await gemini_service.chat(
        user_profile=runtime_user_profile,
        message=request.message,
        food_catalog=food_catalog,
        conversation_history=history,
        full_mock_data=ai_mock_data,
    )

    # Map food_ids -> food objects đầy đủ
    suggested_food_ids: list[str] = ai_result.get("suggested_food_ids", [])
    food_map = {food["id"]: food for food in food_catalog}

    suggested_foods: list[FoodSuggestion] = []
    for food_id in suggested_food_ids:
        if food_id in food_map:
            suggested_foods.append(FoodSuggestion(**food_map[food_id]))

    return ChatResponse(
        response=ai_result["response"],
        suggested_foods=suggested_foods,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

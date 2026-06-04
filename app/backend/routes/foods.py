"""
Foods Router - Endpoint quản lý catalog món ăn
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/foods", tags=["Foods"])

# Đường dẫn đến mock database
DATA_PATH = Path(__file__).parent.parent / "data" / "mock_db.json"


# ============================================================
# Pydantic Models
# ============================================================
class FoodItem(BaseModel):
    """Schema cho một món ăn"""
    id: str
    name: str
    shop: str
    price: int
    rating: float
    distance: str
    eta: str
    image: str
    budget_tier: str
    taste_tags: list[str]
    allergy_tags: list[str]
    description: str
    category: str


class FoodListResponse(BaseModel):
    """Response cho danh sách món ăn"""
    foods: list[FoodItem]
    total: int
    filters_applied: dict


# ============================================================
# Helper functions
# ============================================================
def _load_food_catalog() -> list[dict]:
    """Đọc danh sách món ăn từ mock database và mock data lớn"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
            catalog = db.get("food_catalog", [])

        # Import helper functions from routes.chat to load and flatten large mock data
        from routes.chat import _load_ai_mock_data, _flatten_restaurant_menu
        ai_mock_data = _load_ai_mock_data()
        flat_menu = _flatten_restaurant_menu(ai_mock_data)

        return [*catalog, *flat_menu]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc database: {str(e)}")


# ============================================================
# Endpoints
# ============================================================
@router.get("", response_model=FoodListResponse)
async def list_foods(
    budget_tier: Optional[str] = Query(
        None,
        description="Lọc theo mức giá: low, medium, high",
        regex="^(low|medium|high)$",
    ),
    taste_tag: Optional[str] = Query(
        None,
        description="Lọc theo tag khẩu vị, ví dụ: Ngọt, Đậm đà, Healthy",
    ),
    category: Optional[str] = Query(
        None,
        description="Lọc theo danh mục: Đồ uống, Ăn vặt, Cơm - Mì, Healthy",
    ),
) -> FoodListResponse:
    """
    Lấy danh sách tất cả món ăn với bộ lọc tùy chọn.

    - **budget_tier**: low (< 30k), medium (30k-60k), high (> 60k)
    - **taste_tag**: Lọc theo tag khẩu vị
    - **category**: Lọc theo danh mục món ăn
    """
    foods = _load_food_catalog()

    # Áp dụng bộ lọc
    filters_applied: dict[str, str] = {}

    if budget_tier:
        foods = [f for f in foods if f.get("budget_tier") == budget_tier]
        filters_applied["budget_tier"] = budget_tier

    if taste_tag:
        foods = [
            f for f in foods
            if any(taste_tag.lower() in tag.lower() for tag in f.get("taste_tags", []))
        ]
        filters_applied["taste_tag"] = taste_tag

    if category:
        foods = [
            f for f in foods
            if category.lower() in f.get("category", "").lower()
        ]
        filters_applied["category"] = category

    return FoodListResponse(
        foods=[FoodItem(**f) for f in foods],
        total=len(foods),
        filters_applied=filters_applied,
    )


@router.get("/{food_id}", response_model=FoodItem)
async def get_food_detail(food_id: str) -> FoodItem:
    """
    Lấy thông tin chi tiết của một món ăn theo ID.

    - **food_id**: ID của món, ví dụ food_001
    """
    foods = _load_food_catalog()

    for food in foods:
        if food["id"] == food_id:
            return FoodItem(**food)

    raise HTTPException(
        status_code=404,
        detail=f"Không tìm thấy món ăn với ID: {food_id}",
    )

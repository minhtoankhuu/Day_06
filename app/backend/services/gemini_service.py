"""
Gemini Service - Xử lý giao tiếp với Google Gemini API
Bao gồm chế độ fallback thông minh khi không có API key
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "ai_chat_system_prompt.md"


def _load_system_prompt() -> str:
    """Load prompt mới từ markdown để team chỉnh prompt không cần sửa code."""
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Không tìm thấy ai_chat_system_prompt.md, dùng prompt fallback")
        return (
            'Bạn là "ShopeeFood AI Copilot". Hãy trả lời bằng tiếng Việt, '
            "chỉ gợi ý món có trong food_catalog, tôn trọng ngân sách và cảnh báo dị ứng."
        )


SYSTEM_PROMPT = _load_system_prompt()


class GeminiService:
    """Service class quản lý tương tác với Google Gemini API"""

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.model_name: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None

        # Khởi tạo client nếu có API key
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("✅ Gemini API client khởi tạo thành công")
            except Exception as e:
                logger.warning(f"⚠️ Không thể khởi tạo Gemini client: {e}")
                self._client = None
        else:
            logger.warning("⚠️ GEMINI_API_KEY chưa được cấu hình — chạy chế độ FALLBACK")

    async def chat(
        self,
        user_profile: dict,
        message: str,
        food_catalog: list,
        conversation_history: list,
        full_mock_data: Optional[dict] = None,
    ) -> dict:
        """
        Gửi tin nhắn chat và nhận phản hồi từ AI.

        Args:
            user_profile: Hồ sơ người dùng từ mock_db
            message: Tin nhắn của người dùng
            food_catalog: Danh sách món ăn
            conversation_history: Lịch sử hội thoại

        Returns:
            dict với "response" (str) và "suggested_food_ids" (list[str])
        """
        candidate_foods = self._rank_candidate_foods(user_profile, message, food_catalog)

        if self._client:
            result = await self._call_gemini(
                user_profile, message, food_catalog, conversation_history, full_mock_data, candidate_foods
            )
        else:
            result = self._fallback_response(
                user_profile, message, food_catalog, candidate_foods
            )

        result["suggested_food_ids"] = self._ensure_suggested_ids(
            result.get("suggested_food_ids", []),
            candidate_foods,
            target_count=3,
        )
        return result

    async def _call_gemini(
        self,
        user_profile: dict,
        message: str,
        food_catalog: list,
        conversation_history: list,
        full_mock_data: Optional[dict] = None,
        candidate_foods: Optional[list[dict]] = None,
    ) -> dict:
        """Gọi Gemini API thực tế"""
        try:
            # Xây dựng context đầy đủ
            context_parts = [
                SYSTEM_PROMPT,
                f"\n--- HỒ SƠ NGƯỜI DÙNG ---\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}",
                f"\n--- FOOD_CANDIDATES ĐÃ ĐƯỢC BACKEND LỌC THEO QUERY/RÀNG BUỘC ---\n{json.dumps(candidate_foods or food_catalog[:12], ensure_ascii=False, indent=2)}",
                "\n--- RÀNG BUỘC KỸ THUẬT ---\n"
                "Khi đề xuất món cụ thể, bắt buộc ghi ID món trong ngoặc vuông, "
                "ví dụ [item_yogurt_coconut] hoặc [food_005], để frontend render thẻ món. "
                "Hãy chọn đúng 3 món từ FOOD_CANDIDATES nếu có đủ ứng viên.",
            ]

            if full_mock_data:
                context_parts.append(
                    "\n--- MOCK DATA TÓM TẮT CHO LLM THAM KHẢO ---\n"
                    f"{json.dumps(self._summarize_mock_data(full_mock_data), ensure_ascii=False, indent=2)}"
                )

            # Thêm lịch sử hội thoại
            if conversation_history:
                history_text = "\n--- LỊCH SỬ HỘI THOẠI ---\n"
                for entry in conversation_history[-10:]:  # Giới hạn 10 tin nhắn gần nhất
                    role = entry.get("role", "user")
                    content = entry.get("content", "")
                    history_text += f"{role}: {content}\n"
                context_parts.append(history_text)

            # Thêm tin nhắn hiện tại
            context_parts.append(f"\n--- TIN NHẮN MỚI TỪ NGƯỜI DÙNG ---\n{message}")

            full_prompt = "\n".join(context_parts)

            # Gọi Gemini API
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )

            response_text = response.text

            # Trích xuất food IDs từ phản hồi
            suggested_food_ids = self._extract_food_ids(response_text)

            return {
                "response": response_text,
                "suggested_food_ids": suggested_food_ids,
            }

        except Exception as e:
            logger.error(f"❌ Lỗi khi gọi Gemini API: {e}")
            # Fallback khi API lỗi
            return self._fallback_response(
                user_profile,
                message,
                food_catalog,
                candidate_foods,
            )

    def _fallback_response(
        self,
        user_profile: dict,
        message: str,
        food_catalog: list,
        candidate_foods: Optional[list[dict]] = None,
    ) -> dict:
        """
        Chế độ fallback thông minh - phân tích query và persona
        để tạo response phù hợp khi không có API key
        """
        query_lower = message.lower()
        def has_kw(kw):
            if " " in kw:
                return kw in query_lower
            return bool(re.search(rf"\b{kw}\b", query_lower))

        unrelated_keywords = ["thời tiết", "weather", "code", "lập trình", "python", "javascript", "html", "css", "toán", "thơ", "chính trị", "tin tức", "lịch sử", "địa lý", "hát", "nhảy", "nhạc", "vẽ"]
        non_food_compounds = ["bánh xe", "bánh răng", "bánh lái", "bánh xà phòng", "bánh xà bông", "bánh vẽ", "bánh đà", "nước mắt", "nước hoa", "nước sơn", "nước rửa", "nước lau", "đậu xe", "đậu đại học", "đậu tốt nghiệp", "đậu đỗ", "đỗ xe"]
        food_keywords = ["ăn", "uống", "đói", "thèm", "cơm", "bún", "mì", "phở", "nước", "trà", "sữa", "bánh", "lẩu", "gà", "sườn", "cháo", "salad", "healthy", "chay", "ốc", "nem", "xiên"]
        is_unrelated = (
            any(has_kw(kw) for kw in non_food_compounds)
            or (any(has_kw(kw) for kw in unrelated_keywords) and not any(has_kw(kw) for kw in food_keywords))
        )
        
        if is_unrelated:
            cohort = user_profile.get("cohort", "student")
            if cohort == "pupil":
                refusal = (
                    "Hế lô cậu nhen! Mình là trợ lý tìm món của ShopeeFood chứ không phải là chuyên gia về chủ đề này đâu nè. "
                    "Hôm nay cậu muốn mình tìm món gì ăn vặt hay trà sữa ngọt thơm không, bảo mình để mình tìm nhen! Cậu xác nhận lại món cậu thèm giúp mình nhé! 😋"
                )
            elif cohort == "student":
                refusal = (
                    "Yo đồng môn! Mình chỉ rành tìm món ăn, cứu đói thôi chứ chủ đề này mình chịu rồi! "
                    "Đồng môn hôm nay muốn tìm mì trộn, cơm sườn hay món gì ăn no nạp năng lượng không? Xác nhận lại món thèm để mình tìm cho nha! 🔥"
                )
            else: # office
                refusal = (
                    "Chào anh/chị. Em là Trợ lý AI Tìm Món của ShopeeFood, nên em chỉ có thể hỗ trợ anh/chị tìm kiếm món ăn hoặc thức uống thôi ạ. "
                    "Hôm nay anh/chị có nhu cầu tìm món ăn trưa, salad healthy hay nước uống nào không ạ? Xin anh/chị xác nhận lại yêu cầu món ăn giúp em nhé. 🙏"
                )
            return {
                "response": refusal,
                "suggested_food_ids": [],
            }

        cohort = user_profile.get("cohort", "student")
        preferred_tastes = user_profile.get("taste_preferences", {}).get("preferred", [])
        allergies = self._get_allergy_terms(user_profile, message)
        matched_foods = (candidate_foods or self._rank_candidate_foods(user_profile, message, food_catalog))[:3]

        # Kiểm tra dị ứng
        allergy_warnings: list[dict] = []
        if allergies:
            for food in matched_foods:
                for tag in food.get("allergy_tags", []):
                    for allergy in allergies:
                        if allergy.lower() in tag.lower():
                            allergy_warnings.append({
                                "food": food["name"],
                                "allergen": tag,
                            })

        # Chọn tone phù hợp
        greeting, suggestion_intro, closing = self._get_tone(cohort)

        # Tạo response text
        response_parts = [greeting]

        if not matched_foods:
            response_parts.append(
                "Hiện tại mình chưa tìm thấy món nào phù hợp chính xác với yêu cầu. "
                "Nhưng đây là một vài gợi ý khác có thể cậu sẽ thích:"
            )
            # Fallback: gợi ý top 2 món phù hợp ngân sách
            matched_foods = self._rank_candidate_foods(user_profile, message, food_catalog, relax_query=True)[:3]

        response_parts.append(suggestion_intro)

        suggested_ids: list[str] = []
        for food in matched_foods[:3]:  # Giới hạn 3 món
            food_id = food["id"]
            suggested_ids.append(food_id)

            price_str = f"{food['price']:,}đ".replace(",", ".")
            food_text = (
                f"\n**{food['name']}** - {food['shop']}\n"
                f"⭐ {food['rating']} | 📍 {food['distance']} | ⏱️ {food['eta']}\n"
                f"💸 {price_str} | ✨ {', '.join(food.get('taste_tags', []))}\n"
                f"💡 Lý do: {self._generate_reason(food, preferred_tastes, cohort)}"
            )

            # Cảnh báo dị ứng
            warning = next(
                (w for w in allergy_warnings if w["food"] == food["name"]), None
            )
            if warning:
                food_text += f"\n⚠️ Lưu ý: Món này chứa {warning['allergen']} - có thể gây dị ứng!"

            response_parts.append(food_text)

        response_parts.append(f"\n{closing}")

        return {
            "response": "\n".join(response_parts),
            "suggested_food_ids": suggested_ids,
        }

    def _match_foods_by_query(
        self,
        query: str,
        affordable_foods: list,
        preferred_tastes: list[str],
        all_foods: list,
    ) -> list:
        """Tìm món ăn phù hợp với query của người dùng"""

        # Từ khóa mapping theo intent
        keyword_mapping: dict[str, list[str]] = {
            "trà sữa": ["Trà sữa", "Ngọt"],
            "tra sua": ["Trà sữa", "Ngọt"],
            "ăn vặt": ["Ăn vặt"],
            "an vat": ["Ăn vặt"],
            "bánh tráng": ["Ăn vặt", "Bánh tráng"],
            "banh trang": ["Ăn vặt", "Bánh tráng"],
            "cơm": ["Cơm trưa", "Đậm đà"],
            "com": ["Cơm trưa", "Đậm đà"],
            "mì": ["Mì trộn"],
            "mi tron": ["Mì trộn"],
            "healthy": ["Healthy", "Ít béo", "Rau xanh"],
            "salad": ["Healthy", "Rau xanh"],
            "giải khát": ["Giải khát", "Chua ngọt"],
            "giai khat": ["Giải khát"],
            "uống": ["Giải khát", "Trà sữa", "Chua ngọt"],
            "uong": ["Giải khát", "Trà sữa"],
            "trà chanh": ["Chua ngọt", "Giải khát"],
            "tra chanh": ["Chua ngọt", "Giải khát"],
            "phở": ["Đậm đà", "Nóng", "Truyền thống"],
            "pho": ["Đậm đà", "Nóng", "Truyền thống"],
            "đói": ["Cơm trưa", "Đậm đà", "Mì trộn"],
            "doi": ["Cơm trưa", "Đậm đà"],
            "gà": ["Giòn", "Cơm trưa"],
            "ga": ["Giòn"],
            "no": ["Cơm trưa", "Đậm đà"],
            "rẻ": ["low"],
            "re": ["low"],
            "ngon": [],  # Gợi ý theo rating
        }

        # Tìm tags liên quan từ query
        relevant_tags: list[str] = []
        for keyword, tags in keyword_mapping.items():
            if keyword in query:
                relevant_tags.extend(tags)

        # Nếu không match keyword nào, dùng preferred tastes
        if not relevant_tags:
            relevant_tags = [t.lower() for t in preferred_tastes]

        # Tìm budget_tier filter
        budget_filter = None
        if "rẻ" in query or "re " in query or "giá rẻ" in query or "tiết kiệm" in query:
            budget_filter = "low"
        elif "sang" in query or "đặc biệt" in query:
            budget_filter = "high"

        # Scoring từng món
        scored_foods: list[tuple[dict, float]] = []
        search_pool = affordable_foods if affordable_foods else all_foods

        for food in search_pool:
            score = 0.0
            food_tags = [t.lower() for t in food.get("taste_tags", [])]
            food_category = food.get("category", "").lower()
            food_name = food.get("name", "").lower()

            # Match với relevant tags
            for tag in relevant_tags:
                if tag.lower() in food_tags:
                    score += 2.0
                if tag.lower() in food_category:
                    score += 1.0
                if tag.lower() in food_name:
                    score += 1.5

            # Budget tier match
            if budget_filter and food.get("budget_tier") == budget_filter:
                score += 1.5

            # Bonus cho rating cao
            score += food.get("rating", 0) * 0.3

            # Tìm keyword trong tên món
            for word in query.split():
                if len(word) > 2 and word in food_name:
                    score += 3.0

            if score > 0:
                scored_foods.append((food, score))

        # Sắp xếp theo score giảm dần
        scored_foods.sort(key=lambda x: x[1], reverse=True)

        return [food for food, _ in scored_foods[:3]]

    def _rank_candidate_foods(
        self,
        user_profile: dict,
        message: str,
        food_catalog: list,
        limit: int = 12,
        relax_query: bool = False,
    ) -> list[dict]:
        """Lọc/rank món trước khi đưa cho LLM hoặc fallback."""
        query = message.lower()
        budget_limit = self._get_budget_limit(user_profile, query)
        budget_filter = self._get_budget_filter(query)
        avoid_spicy = self._should_avoid_spicy(user_profile, message)
        allergies = self._get_allergy_terms(user_profile, message)
        relevant_tags = self._get_relevant_tags(query)
        preferred_tastes = user_profile.get("taste_preferences", {}).get("preferred", [])

        if not relevant_tags and not relax_query:
            relevant_tags = preferred_tastes[:]

        scored_foods: list[tuple[dict, float]] = []

        for food in food_catalog:
            price = food.get("price", 0)
            if price > budget_limit:
                continue

            if budget_filter and food.get("budget_tier") != budget_filter:
                continue

            if avoid_spicy and self._food_is_spicy(food):
                continue

            if allergies and self._food_matches_allergy(food, allergies):
                continue

            score = self._score_food(food, query, relevant_tags, preferred_tastes)
            if relax_query:
                score += food.get("rating", 0) * 0.4

            if score > 0 or relax_query:
                scored_foods.append((food, score))

        scored_foods.sort(key=lambda x: (x[1], -x[0].get("price", 0)), reverse=True)
        return [food for food, _ in scored_foods[:limit]]

    def _get_budget_limit(self, user_profile: dict, query: str) -> int:
        """Lấy ngân sách tối đa từ query, profile mới/cũ, hoặc intent giá rẻ."""
        explicit_budget = self._extract_budget_from_query(query)
        profile_limit = int(user_profile.get("avg_order_value_limit", 50000))

        llm_budget = user_profile.get("budget_preference", {})
        if isinstance(llm_budget, dict) and llm_budget.get("max"):
            profile_limit = min(profile_limit, int(llm_budget["max"]))

        if explicit_budget:
            return min(profile_limit, explicit_budget)

        if self._get_budget_filter(query) == "low":
            return min(profile_limit, 30000)

        return profile_limit

    def _extract_budget_from_query(self, query: str) -> Optional[int]:
        """Parse các dạng 'dưới 30k', '< 50k', '30000đ'."""
        patterns = [
            r"(?:dưới|duoi|<=|<|tối đa|toi da)\s*(\d{1,3})\s*k",
            r"(\d{1,3})\s*k",
            r"(\d{2,3})[.,]?000\s*đ?",
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                value = int(match.group(1))
                return value * 1000 if value < 1000 else value
        return None

    def _get_budget_filter(self, query: str) -> Optional[str]:
        if any(keyword in query for keyword in ("rẻ", "re ", "giá rẻ", "gia re", "tiết kiệm", "tiet kiem", "hạt dẻ", "hat de")):
            return "low"
        if any(keyword in query for keyword in ("cao cấp", "cao cap", "sang", "đặc biệt", "dac biet")):
            return "high"
        return None

    def _get_relevant_tags(self, query: str) -> list[str]:
        keyword_mapping: dict[str, list[str]] = {
            "trà sữa": ["Trà sữa", "Ngọt"],
            "tra sua": ["Trà sữa", "Ngọt"],
            "matcha": ["Trà sữa", "Ngọt"],
            "trà đào": ["Giải khát", "Chua ngọt"],
            "tra dao": ["Giải khát", "Chua ngọt"],
            "trà vải": ["Giải khát", "Chua ngọt"],
            "tra vai": ["Giải khát", "Chua ngọt"],
            "ăn vặt": ["Ăn vặt"],
            "an vat": ["Ăn vặt"],
            "bánh tráng": ["Ăn vặt", "Bánh tráng"],
            "banh trang": ["Ăn vặt", "Bánh tráng"],
            "tokbokki": ["Ăn vặt"],
            "cá viên": ["Ăn vặt"],
            "ca vien": ["Ăn vặt"],
            "khoai": ["Ăn vặt"],
            "cơm": ["Cơm trưa", "Đậm đà"],
            "com": ["Cơm trưa", "Đậm đà"],
            "văn phòng": ["Cơm trưa", "Healthy", "Cà phê"],
            "van phong": ["Cơm trưa", "Healthy", "Cà phê"],
            "office": ["Cơm trưa", "Healthy", "Cà phê"],
            "lunch": ["Cơm trưa", "Healthy"],
            "bento": ["Cơm trưa", "Healthy"],
            "xôi": ["Cơm trưa", "Bữa sáng"],
            "xoi": ["Cơm trưa", "Bữa sáng"],
            "bánh mì": ["Bữa sáng"],
            "banh mi": ["Bữa sáng"],
            "ăn sáng": ["Bữa sáng"],
            "an sang": ["Bữa sáng"],
            "mì": ["Mì trộn"],
            "mi ": ["Mì trộn"],
            "mì trộn": ["Mì trộn"],
            "udon": ["Mì trộn"],
            "healthy": ["Healthy", "Ít béo", "Rau xanh"],
            "salad": ["Healthy", "Rau xanh"],
            "eat clean": ["Healthy", "Ít béo", "Rau xanh"],
            "gạo lứt": ["Healthy", "Cơm trưa"],
            "gao lut": ["Healthy", "Cơm trưa"],
            "chay": ["Healthy"],
            "giải khát": ["Giải khát", "Chua ngọt"],
            "giai khat": ["Giải khát"],
            "uống": ["Giải khát", "Trà sữa", "Chua ngọt"],
            "uong": ["Giải khát", "Trà sữa"],
            "nước ép": ["Giải khát", "Healthy"],
            "nuoc ep": ["Giải khát", "Healthy"],
            "sinh tố": ["Giải khát", "Ngọt"],
            "sinh to": ["Giải khát", "Ngọt"],
            "detox": ["Healthy", "Giải khát"],
            "trà chanh": ["Chua ngọt", "Giải khát"],
            "tra chanh": ["Chua ngọt", "Giải khát"],
            "phở": ["Đậm đà", "Nóng", "Truyền thống"],
            "pho": ["Đậm đà", "Nóng", "Truyền thống"],
            "bún": ["Đậm đà", "Truyền thống"],
            "bun": ["Đậm đà", "Truyền thống"],
            "cháo": ["Nóng", "Truyền thống"],
            "chao": ["Nóng", "Truyền thống"],
            "miến": ["Nóng", "Truyền thống"],
            "mien": ["Nóng", "Truyền thống"],
            "gà": ["Giòn", "Cơm trưa"],
            "ga": ["Giòn"],
            "cà phê": ["Cà phê"],
            "ca phe": ["Cà phê"],
            "coffee": ["Cà phê"],
            "bạc xỉu": ["Cà phê"],
            "bac xiu": ["Cà phê"],
            "chè": ["Ngọt"],
            "che": ["Ngọt"],
            "dessert": ["Ngọt", "Ăn vặt"],
            "không cay": ["Không cay"],
            "khong cay": ["Không cay"],
            "rẻ": ["low"],
            "giá rẻ": ["low"],
            "gia re": ["low"],
        }

        tags: list[str] = []
        for keyword, values in keyword_mapping.items():
            if keyword in query:
                tags.extend(values)
        return tags

    def _score_food(
        self,
        food: dict,
        query: str,
        relevant_tags: list[str],
        preferred_tastes: list[str],
    ) -> float:
        score = 0.0
        food_tags = [t.lower() for t in food.get("taste_tags", [])]
        food_category = food.get("category", "").lower()
        food_name = food.get("name", "").lower()

        for tag in relevant_tags:
            tag_lower = tag.lower()
            if tag_lower in ("low", "medium", "high"):
                if food.get("budget_tier") == tag_lower:
                    score += 2.0
                continue
            if tag_lower in food_tags:
                score += 3.0
            if tag_lower in food_category:
                score += 1.5
            if tag_lower in food_name:
                score += 2.0

        for pref in preferred_tastes:
            pref_lower = pref.lower()
            if any(pref_lower in tag for tag in food_tags) or pref_lower in food_name or pref_lower in food_category:
                score += 1.2

        if "healthy" in query and food.get("is_healthy"):
            score += 3.0
        if any(keyword in query for keyword in ("ít dầu", "it dau", "eat clean")) and food.get("is_healthy"):
            score += 2.0
        if any(keyword in query for keyword in ("văn phòng", "van phong", "office", "lunch")):
            if "cơm trưa" in food_tags or "healthy" in food_tags or "cà phê" in food_tags:
                score += 1.5

        for word in query.split():
            if len(word) > 2 and word in food_name:
                score += 2.5

        if food.get("budget_tier") == "low":
            score += 0.6
        score += food.get("rating", 0) * 0.25
        score += max(0, 60000 - food.get("price", 0)) / 100000
        return score

    def _food_is_spicy(self, food: dict) -> bool:
        text = " ".join(
            [
                food.get("name", ""),
                food.get("description", ""),
                food.get("category", ""),
                " ".join(food.get("taste_tags", [])),
            ]
        ).lower()
        return ("cay" in text or "ớt" in text) and "không cay" not in text

    def _ensure_suggested_ids(
        self,
        suggested_ids: list[str],
        candidate_foods: list[dict],
        target_count: int = 3,
    ) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        candidate_ids = {food.get("id") for food in candidate_foods}

        for food_id in suggested_ids:
            if food_id in candidate_ids and food_id not in seen:
                seen.add(food_id)
                result.append(food_id)

        for food in candidate_foods:
            food_id = food.get("id")
            if food_id and food_id not in seen:
                seen.add(food_id)
                result.append(food_id)
            if len(result) >= target_count:
                break

        return result[:target_count]

    def _summarize_mock_data(self, full_mock_data: dict) -> dict:
        """Giảm context phụ để LLM tập trung vào FOOD_CANDIDATES."""
        return {
            "user_profile_count": len(full_mock_data.get("users", [])),
            "restaurant_count": len(full_mock_data.get("restaurants", [])),
            "available_banner_cohorts": list(full_mock_data.get("banners", {}).keys()),
            "available_push_notification_cohorts": list(full_mock_data.get("push_notifications", {}).keys()),
        }

    def _should_avoid_spicy(self, user_profile: dict, message: str) -> bool:
        """Nhận diện ràng buộc không cay từ query và hồ sơ user."""
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ("không cay", "khong cay", "ít cay", "it cay")):
            return True

        disliked = user_profile.get("taste_preferences", {}).get("disliked", [])
        if any("cay" in item.lower() for item in disliked):
            return True

        preferences = user_profile.get("preferences", {})
        if preferences.get("avoid_spicy"):
            return True

        llm_profile = user_profile.get("llm_mock_profile", {})
        llm_preferences = llm_profile.get("preferences", {})
        return bool(llm_preferences.get("avoid_spicy"))

    def _get_allergy_terms(self, user_profile: dict, message: str) -> list[str]:
        """Gom dị ứng từ profile mới/cũ và câu hỏi trực tiếp của user."""
        terms: list[str] = []

        def add(value: str) -> None:
            if value and value.lower() not in [term.lower() for term in terms]:
                terms.append(value)

        for allergy in user_profile.get("allergies", []):
            add(allergy)

        for allergy in user_profile.get("preferences", {}).get("allergies", []):
            add(allergy)

        for allergy in user_profile.get("llm_mock_profile", {}).get("preferences", {}).get("allergies", []):
            add(allergy)

        message_lower = message.lower()
        query_allergens = {
            "đậu phộng": ["đậu phộng", "dau phong", "peanut"],
            "đậu nành": ["đậu nành", "dau nanh", "soy"],
            "hải sản": ["hải sản", "hai san", "seafood", "tôm", "tép", "mực"],
            "sữa": ["sữa", "sua", "milk", "phô mai"],
            "trứng": ["trứng", "trung", "egg"],
        }
        if "dị ứng" in message_lower or "di ung" in message_lower:
            for label, keywords in query_allergens.items():
                if any(keyword in message_lower for keyword in keywords):
                    add(label)

        return terms

    def _food_matches_allergy(self, food: dict, allergies: list[str]) -> bool:
        haystack = " ".join(
            [
                food.get("name", ""),
                food.get("description", ""),
                " ".join(food.get("allergy_tags", [])),
                " ".join(food.get("taste_tags", [])),
            ]
        ).lower()

        aliases = {
            "đậu phộng": ["đậu phộng", "dau phong", "peanut"],
            "đậu nành": ["đậu nành", "dau nanh", "soy"],
            "soy": ["đậu nành", "soy"],
            "seafood": ["hải sản", "seafood", "tôm", "tép", "mực"],
            "hải sản": ["hải sản", "seafood", "tôm", "tép", "mực"],
            "sữa": ["sữa", "milk", "phô mai"],
            "trứng": ["trứng", "egg"],
        }

        for allergy in allergies:
            allergy_lower = allergy.lower()
            keywords = aliases.get(allergy_lower, [allergy_lower])
            if any(keyword in haystack for keyword in keywords):
                return True
        return False

    def _get_tone(
        self, cohort: str
    ) -> tuple[str, str, str]:
        """Trả về greeting, suggestion intro, closing phù hợp theo cohort"""

        if cohort == "pupil":
            return (
                "Ê cậu ơi! 🎒 Mình tìm được mấy món bao ngon cho cậu nè!",
                "Check ngay mấy món này nhen:",
                "Cậu thích món nào thì bảo mình nhen! 😋",
            )
        elif cohort == "student":
            return (
                "Yo đồng môn! 🎓 Hỏi đúng người rồi!",
                "Mấy món này vừa ngon vừa không lo ví khóc nè:",
                "Đồng môn chốt món nào không? Mình order liền! 🔥",
            )
        else:  # office
            return (
                "Chào anh/chị! 💼 Em có một vài gợi ý phù hợp ạ.",
                "Dưới đây là các món em gợi ý cho anh/chị:",
                "Anh/chị cần thêm gợi ý khác không ạ? 🙏",
            )

    def _generate_reason(
        self, food: dict, preferred_tastes: list[str], cohort: str
    ) -> str:
        """Tạo lý do gợi ý cá nhân hóa"""
        food_tags = food.get("taste_tags", [])
        price = food.get("price", 0)
        rating = food.get("rating", 0)

        # Tìm overlap giữa preferred và food tags
        matching_prefs = [
            pref for pref in preferred_tastes
            if any(pref.lower() in tag.lower() for tag in food_tags)
        ]

        reasons: list[str] = []

        if matching_prefs:
            reasons.append(f"Phù hợp với sở thích '{', '.join(matching_prefs[:2])}' của bạn")

        if rating >= 4.7:
            reasons.append(f"Được đánh giá rất cao ({rating}⭐)")

        if price <= 25000:
            if cohort in ("pupil", "student"):
                reasons.append("Giá hạt dẻ, hợp túi tiền")
        elif price <= 50000 and cohort == "student":
            reasons.append("Giá sinh viên, ăn no lâu")

        if not reasons:
            reasons.append(f"Món {food.get('category', 'ngon')} được nhiều người yêu thích")

        return ". ".join(reasons) + "."

    def _extract_food_ids(self, text: str) -> list[str]:
        """Trích xuất food/item id từ text response (format: [food_001] hoặc [item_xxx])."""
        pattern = r"\[?((?:food_\d{3})|(?:item_[a-zA-Z0-9_]+))\]?"
        matches = re.findall(pattern, text)
        # Loại bỏ trùng lặp, giữ thứ tự
        seen: set[str] = set()
        unique_ids: list[str] = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_ids.append(match)
        return unique_ids


# Singleton instance
gemini_service = GeminiService()

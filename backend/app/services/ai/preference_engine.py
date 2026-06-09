from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.preferences import UserPreference


class PreferenceEngine:
    DECAY = 0.92
    INITIAL_WEIGHT = 1.0
    POSITIVE_DELTA = 0.3
    NEGATIVE_DELTA = -0.2
    MIN_WEIGHT = 0.1
    TIME_HALF_LIFE_DAYS = 30

    FIELD_TO_TAG: dict[str, str] = {
        "mark": "brand",
        "body_type": "body_type",
        "engine_type": "fuel_type",
    }

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _time_factor(updated_at: datetime) -> float:
        dt = updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=UTC)
        elapsed_days = max((datetime.now(UTC) - dt).days, 0)
        return 0.5 ** (elapsed_days / PreferenceEngine.TIME_HALF_LIFE_DAYS)

    @staticmethod
    def _diminishing_delta(base_delta: float, count: int) -> float:
        return base_delta / (1.0 + math.log1p(count) * 0.4)

    async def get_preferences(
        self, user_id: uuid.UUID
    ) -> dict[str, dict[str, float]]:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        out: dict[str, dict[str, float]] = {}
        for p in result.scalars().all():
            effective = p.weight * self._time_factor(p.updated_at)
            if effective >= self.MIN_WEIGHT:
                out.setdefault(p.tag_type, {})[p.tag_value] = effective
        return out

    async def update_weights(
        self,
        user_id: uuid.UUID,
        tags: dict[str, str],
        feedback: str = "positive",
    ) -> None:
        base_delta = self.POSITIVE_DELTA if feedback == "positive" else self.NEGATIVE_DELTA
        now = datetime.now(UTC)

        for tag_type, tag_value in tags.items():
            if not tag_value:
                continue

            result = await self.session.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.tag_type == tag_type,
                    UserPreference.tag_value == str(tag_value),
                )
            )
            pref = result.scalars().first()

            if pref:
                delta = self._diminishing_delta(base_delta, pref.count)
                pref.weight = max(pref.weight * self.DECAY + delta, self.MIN_WEIGHT)
                pref.count += 1
                pref.updated_at = now
            else:
                self.session.add(UserPreference(
                    user_id=user_id,
                    tag_type=tag_type,
                    tag_value=str(tag_value),
                    weight=max(self.INITIAL_WEIGHT + base_delta, self.MIN_WEIGHT),
                    count=1,
                    updated_at=now,
                ))

        await self.session.flush()

    @staticmethod
    def rank_cars(
        cars: list[dict[str, Any]],
        preferences: dict[str, dict[str, float]],
    ) -> list[dict[str, Any]]:
        if not preferences:
            return cars

        max_per_type = {
            tag_type: max(vals.values(), default=1.0)
            for tag_type, vals in preferences.items()
        }

        def score(car: dict[str, Any]) -> float:
            total = 0.0
            for field, tag_type in PreferenceEngine.FIELD_TO_TAG.items():
                weight = preferences.get(tag_type, {}).get(str(car.get(field, "")), 0.0)
                if weight > 0:
                    total += weight / max(max_per_type.get(tag_type, 1.0), 1e-9)
            return total

        return sorted(cars, key=score, reverse=True)

    @staticmethod
    def top_preferences(
        preferences: dict[str, dict[str, float]],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        tags = [
            {"type": t, "value": v, "weight": w}
            for t, vals in preferences.items()
            for v, w in vals.items()
        ]
        tags.sort(key=lambda x: x["weight"], reverse=True)
        return tags[:limit]

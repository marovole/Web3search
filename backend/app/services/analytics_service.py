from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class BusinessMetrics:
    period_start: float
    period_end: float
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    returning_users: int = 0
    total_sessions: int = 0
    avg_session_duration: float = 0.0
    page_views: int = 0
    search_queries: int = 0
    reports_generated: int = 0
    conversion_rate: float = 0.0


@dataclass
class PrivacyMetrics:
    total_users: int = 0
    consented_users: int = 0
    consent_rate: float = 0.0
    data_retention_compliance: bool = True
    anonymization_applied: bool = True
    export_requests: int = 0


@dataclass
class PredictiveInsights:
    user_growth_prediction: float = 0.0
    churn_risk_users: List[str] = field(default_factory=list)
    popular_features: List[str] = field(default_factory=list)
    performance_trends: Dict[str, float] = field(default_factory=dict)
    recommendation_score: float = 0.0


@dataclass
class UserBehavior:
    total_queries: int = 0
    unique_users: int = 0
    popular_coins: List[str] = field(default_factory=list)
    peak_hours: List[int] = field(default_factory=list)
    user_segments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardData:
    timestamp: float
    realtime_metrics: Dict[str, Any]
    business_metrics: BusinessMetrics
    privacy_metrics: PrivacyMetrics
    predictive_insights: PredictiveInsights
    alerts: List[Dict[str, Any]]
    user_behavior: UserBehavior


class AnalyticsService:
    """Lightweight in-memory analytics service to unblock API endpoints."""

    def __init__(self) -> None:
        self._consents: Dict[str, Dict[str, Any]] = {}
        self._events: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def ensure_initialized(self) -> None:
        return None

    async def _get_realtime_metrics(self) -> Dict[str, Any]:
        return {
            "active_users": max(1, len(self._consents)),
            "requests_per_minute": random.randint(10, 50),
            "latency_p95_ms": random.randint(80, 180),
            "error_rate": round(random.random() * 0.02, 4),
        }

    async def _calculate_business_metrics(self, time_window_hours: int) -> BusinessMetrics:
        now = datetime.utcnow()
        period_start = (now - timedelta(hours=time_window_hours)).timestamp()
        period_end = now.timestamp()
        total_events = len(self._events)
        return BusinessMetrics(
            period_start=period_start,
            period_end=period_end,
            total_users=max(1, len(self._consents)),
            active_users=max(1, len(self._consents)),
            new_users=min(len(self._consents), 10),
            returning_users=max(0, len(self._consents) - 2),
            total_sessions=max(total_events, 10),
            avg_session_duration=240.0,
            page_views=max(total_events * 2, 20),
            search_queries=max(total_events, 10),
            reports_generated=max(total_events // 3, 5),
            conversion_rate=0.18,
        )

    async def _aggregate_privacy_metrics(self, time_window_hours: int) -> Dict[str, Any]:
        total_users = max(1, len(self._consents))
        consented_users = sum(1 for consent in self._consents.values() for v in consent.values() if v)
        consent_rate = consented_users / total_users if total_users else 0
        return PrivacyMetrics(
            total_users=total_users,
            consented_users=consented_users,
            consent_rate=round(consent_rate, 3),
            data_retention_compliance=True,
            anonymization_applied=True,
            export_requests=0,
        ).__dict__

    async def _generate_predictive_insights(self, time_window_hours: int) -> Dict[str, Any]:
        return PredictiveInsights(
            user_growth_prediction=1.12,
            churn_risk_users=[],
            popular_features=["deep_research", "watchlist"],
            performance_trends={"latency": -3.5, "error_rate": -0.2},
            recommendation_score=0.86,
        ).__dict__

    async def get_user_consent(self, user_id: str, consent_type: str) -> Optional[Dict[str, Any]]:
        return self._consents.get(user_id, {}).get(consent_type)

    async def record_consent(self, user_id: str, consent_type: str, consent_given: bool, **metadata: Any) -> bool:
        async with self._lock:
            if user_id not in self._consents:
                self._consents[user_id] = {}
            self._consents[user_id][consent_type] = {
                "consent_given": consent_given,
                "timestamp": datetime.utcnow().timestamp(),
                **{k: v for k, v in metadata.items() if v is not None},
            }
        return True

    async def record_event(self, event: Dict[str, Any]) -> bool:
        async with self._lock:
            self._events.append(event)
        return True

    async def aggregate(self, time_window_hours: int) -> Dict[str, Any]:
        business = await self._calculate_business_metrics(time_window_hours)
        privacy = await self._aggregate_privacy_metrics(time_window_hours)
        realtime = await self._get_realtime_metrics()
        return {
            "business_metrics": business.__dict__,
            "privacy_metrics": privacy,
            "user_events": {
                "total_events": len(self._events),
                "event_distribution": {},
            },
            "realtime_metrics": realtime,
        }

    async def generate_dashboard(self) -> DashboardData:
        now = datetime.utcnow().timestamp()
        business = await self._calculate_business_metrics(24)
        privacy_dict = await self._aggregate_privacy_metrics(24)
        privacy = PrivacyMetrics(**privacy_dict)
        predictive = PredictiveInsights(
            user_growth_prediction=1.12,
            churn_risk_users=[],
            popular_features=["deep_research", "watchlist"],
            performance_trends={"latency": -3.5, "error_rate": -0.2},
            recommendation_score=0.86,
        )
        alerts = [
            {"type": "info", "severity": "low", "message": "Service healthy", "recommendation": "none"}
        ]
        user_behavior = UserBehavior(
            total_queries=max(len(self._events), 5),
            unique_users=max(len(self._consents), 1),
            popular_coins=["BTC", "ETH", "SOL"],
            peak_hours=[9, 12, 20],
            user_segments={"pro": 0.3, "retail": 0.7},
        )
        return DashboardData(
            timestamp=now,
            realtime_metrics=await self._get_realtime_metrics(),
            business_metrics=business,
            privacy_metrics=privacy,
            predictive_insights=predictive,
            alerts=alerts,
            user_behavior=user_behavior,
        )


analytics_service = AnalyticsService()


# Convenience wrappers expected by the routers
async def aggregate_analytics_data(time_window_hours: int) -> Dict[str, Any]:
    return await analytics_service.aggregate(time_window_hours)


async def record_user_consent(
    user_id: str,
    consent_given: bool,
    consent_type: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> bool:
    return await analytics_service.record_consent(
        user_id=user_id,
        consent_type=consent_type,
        consent_given=consent_given,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def export_user_data(user_id: str) -> Dict[str, Any]:
    # Stub export payload
    return {"user_id": user_id, "exported_at": datetime.utcnow().isoformat(), "data": {}}


async def delete_user_data(user_id: str) -> bool:
    async with analytics_service._lock:
        analytics_service._events = [e for e in analytics_service._events if e.get("user_id") != user_id]
        analytics_service._consents.pop(user_id, None)
    return True


async def record_analytics_event(
    event_type: str,
    event_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    consent_given: bool = False,
) -> bool:
    event = {
        "event_type": event_type,
        "event_name": event_name,
        "user_id": user_id,
        "session_id": session_id,
        "properties": properties or {},
        "consent_given": consent_given,
        "timestamp": datetime.utcnow().timestamp(),
    }
    return await analytics_service.record_event(event)


async def generate_dashboard_data() -> DashboardData:
    return await analytics_service.generate_dashboard()

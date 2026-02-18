import io
import logging
from datetime import datetime, time, timedelta, timezone
from typing import List
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from stravalib import unit_helper

from ..auth import get_client
from ..config import TZ
from ..gear_image import create_gear_image

router = APIRouter()
logger = logging.getLogger(__name__)

tz = ZoneInfo(TZ)


class GearItem(BaseModel):
    id: str
    name: str


class GearList(BaseModel):
    gear: List[GearItem]


class GearStats(BaseModel):
    gear_id: str
    name: str
    brand_name: str
    last_30_days: dict
    this_week: dict
    distance_km: float
    timestamp: str


@router.get("/users/{user_id}/gear", response_model=GearList)
async def list_gear(user_id: str):
    """List all available gear for a specific user"""
    try:
        client = get_client(user_id)
        athlete = client.get_athlete()

        all_gear = []
        for bike in getattr(athlete, "bikes", []):
            all_gear.append({"id": bike.id, "name": bike.name})
        for shoe in getattr(athlete, "shoes", []):
            all_gear.append({"id": shoe.id, "name": shoe.name})

        return {"gear": all_gear}

    except HTTPException as he:
        # Pass through authentication-related exceptions
        raise he
    except Exception as e:
        logger.error(f"Error fetching gear list for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/gear/{gear_id}.jpg", response_class=StreamingResponse)
async def get_gear_image(user_id: str, gear_id: str):
    """Get stats for specific piece of gear for a specific user as a JPEG image"""
    try:
        stats = await get_gear_stats(user_id, gear_id)
        image = create_gear_image(stats)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality="maximum")
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="image/jpeg")

    except HTTPException as he:
        # Pass through authentication-related exceptions
        raise he
    except Exception as e:
        logger.error(
            f"Error generating gear image for user {user_id}, gear {gear_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/gear/{gear_id}", response_model=GearStats)
async def get_gear_stats(user_id: str, gear_id: str):
    """Get stats for specific piece of gear for a specific user"""
    try:
        client = get_client(user_id)
        gear = client.get_gear(gear_id)

        # Calculate start of this week (Monday)
        start_of_today = datetime.combine(datetime.now(tz=tz), time.min, tzinfo=tz)
        start_of_week = start_of_today - timedelta(
            days=start_of_today.weekday()
        )  # Monday is 0

        activities = client.get_activities(
            after=start_of_today - timedelta(days=30)
        )  # Fetch enough activities to cover both ranges

        gear_activities_30d = {
            "distance_m": 0,
            "moving_time": timedelta(seconds=0),
            "activities": [],
        }

        gear_activities_this_week = {
            "distance_m": 0,
            "moving_time": timedelta(seconds=0),
            "activities": [],
        }

        for activity in activities:
            if getattr(activity, "gear_id", None) == gear_id:
                # Accumulate for last 30 days
                if activity.start_date and activity.start_date >= (
                    start_of_today - timedelta(days=30)
                ):
                    gear_activities_30d["activities"].append(activity)
                    if activity.distance is not None:
                        gear_activities_30d["distance_m"] += unit_helper.meter(
                            activity.distance
                        ).magnitude
                    if activity.moving_time is not None:
                        gear_activities_30d["moving_time"] += (
                            activity.moving_time.timedelta()
                        )

                # Accumulate for this week
                if activity.start_date and activity.start_date >= start_of_week:
                    gear_activities_this_week["activities"].append(activity)
                    if activity.distance is not None:
                        gear_activities_this_week["distance_m"] += unit_helper.meter(
                            activity.distance
                        ).magnitude
                    if activity.moving_time is not None:
                        gear_activities_this_week["moving_time"] += (
                            activity.moving_time.timedelta()
                        )

        # Process 30d stats
        m_time_30d = gear_activities_30d["moving_time"]
        gear_activities_30d["moving_time_s"] = m_time_30d.seconds
        gear_activities_30d["moving_time_hh_mm"] = ":".join(
            str(m_time_30d).split(":")[:2]
        )

        # Process this week stats
        m_time_this_week = gear_activities_this_week["moving_time"]
        gear_activities_this_week["moving_time_s"] = m_time_this_week.seconds
        gear_activities_this_week["moving_time_hh_mm"] = ":".join(
            str(m_time_this_week).split(":")[:2]
        )

        return {
            "gear_id": gear_id,
            "name": gear.name,
            "brand_name": gear.brand_name,
            "model_name": gear.model_name,
            "last_30_days": {
                "distance_km": round(gear_activities_30d["distance_m"] / 1000, 1),
                "time_hh_mm": gear_activities_30d["moving_time_hh_mm"],
                "activity_count": len(gear_activities_30d["activities"]),
            },
            "this_week": {
                "distance_km": round(gear_activities_this_week["distance_m"] / 1000, 1),
                "time_hh_mm": gear_activities_this_week["moving_time_hh_mm"],
                "activity_count": len(gear_activities_this_week["activities"]),
            },
            "last_activity": {
                "distance_km": round(
                    unit_helper.meter(
                        gear_activities_30d["activities"][0].distance
                    ).magnitude
                    / 1000,
                    1,
                )
                if gear_activities_30d["activities"]
                else 0
            },
            "distance_km": round(unit_helper.meter(gear.distance).magnitude / 1000, 0)
            if gear.distance is not None
            else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException as he:
        # Pass through authentication-related exceptions
        raise he
    except Exception as e:
        logger.error(
            f"Error fetching gear stats for user {user_id}, gear {gear_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))

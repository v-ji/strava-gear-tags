from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import logging
from ..auth import get_client
from stravalib import unit_helper
from typing import List
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.get("/users/{user_id}/gear/{gear_id}", response_model=GearStats)
async def get_gear_stats(user_id: str, gear_id: str):
    """Get stats for specific piece of gear for a specific user"""
    try:
        client = get_client(user_id)
        gear = client.get_gear(gear_id)
        activities_30d = client.get_activities(
            after=datetime.now() - timedelta(days=30)
        )

        gear_activities_30d = {
            "distance_m": 0,
            "moving_time": timedelta(seconds=0),
            "activities": [],
        }

        for activity in activities_30d:
            if getattr(activity, "gear_id", None) == gear_id:
                gear_activities_30d["activities"].append(activity)
                # Check if distance exists and is not None
                if activity.distance is not None:
                    gear_activities_30d["distance_m"] += unit_helper.meter(
                        activity.distance
                    ).magnitude
                if activity.moving_time is not None:
                    gear_activities_30d["moving_time"] += (
                        activity.moving_time.timedelta()
                    )

        m_time = gear_activities_30d["moving_time"]
        gear_activities_30d["moving_time_s"] = m_time.seconds
        gear_activities_30d["moving_time_hh_mm"] = ":".join(str(m_time).split(":")[:2])

        return {
            "gear_id": gear_id,
            "name": gear.name,
            "brand_name": gear.brand_name,
            "last_30_days": {
                "distance_km": round(gear_activities_30d["distance_m"] / 1000, 1),
                "time_hh_mm": gear_activities_30d["moving_time_hh_mm"],
                "activity_count": len(gear_activities_30d["activities"]),
            },
            "last_activity": {
                "distance_km": round(
                    unit_helper.meter(
                        gear_activities_30d["activities"][0].distance
                    ).magnitude
                    / 1000,
                    1,
                )
            },
            "distance_km": round(unit_helper.meter(gear.distance).magnitude / 1000, 0)
            if gear.distance is not None
            else 0,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException as he:
        # Pass through authentication-related exceptions
        raise he
    except Exception as e:
        logger.error(
            f"Error fetching gear stats for user {user_id}, gear {gear_id}: {e}"
        )
        raise e
        raise HTTPException(status_code=500, detail=str(e))

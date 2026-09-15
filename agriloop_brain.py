"""
AgriLoop — Split 4: AI / Data Models
=====================================

This module is the "brain" of AgriLoop's virtual pooling system.
It intentionally avoids black-box ML — every score is explainable,
auditable, and defensible in a judging Q&A. Each of the four sub-models
described in the architecture is implemented as its own class, and
AgriLoopBrain wires them together into one callable service.

Pipeline:
    Bale Certificates + Zone Fire Data + Plant POs
            │
            ▼
    1. MoistureDensitySanityCheck   -> flags anomalous bales
    2. SatelliteRiskModel           -> per-zone burn-risk score
    3. GeoClusteringEngine          -> pools bales into truckloads,
                                        prioritized by risk score
    4. ReferencePricingEngine       -> transparent price per bale/pool
            │
            ▼
    PoolAssignment[]  (the demo deliverable)

Run this file directly to see a full synthetic demo end-to-end:
    python agriloop_brain.py
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────
# Shared data model (mirrors Split 3's DB schema — input/output shapes)
# ─────────────────────────────────────────────────────────────────────────

class CropType(str, Enum):
    PADDY_STRAW = "paddy_straw"
    WHEAT_STRAW = "wheat_straw"
    SUGARCANE_TRASH = "sugarcane_trash"
    COTTON_STALK = "cotton_stalk"
    MAIZE_STOVER = "maize_stover"


class Season(str, Enum):
    KHARIF = "kharif"   # monsoon-sown, autumn harvest
    RABI = "rabi"        # winter-sown, spring harvest
    ZAID = "zaid"         # summer, irrigated


# Expected moisture % bounds per crop type — used by the sanity checker.
# (Numbers are illustrative agronomic ranges for freshly baled residue.)
EXPECTED_MOISTURE_RANGE: dict[CropType, tuple[float, float]] = {
    CropType.PADDY_STRAW: (8.0, 18.0),
    CropType.WHEAT_STRAW: (6.0, 15.0),
    CropType.SUGARCANE_TRASH: (10.0, 22.0),
    CropType.COTTON_STALK: (8.0, 16.0),
    CropType.MAIZE_STOVER: (9.0, 20.0),
}

# Expected bale density bounds (kg/m^3) — loose vs over/under-compacted bales.
EXPECTED_DENSITY_RANGE: dict[CropType, tuple[float, float]] = {
    CropType.PADDY_STRAW: (80.0, 150.0),
    CropType.WHEAT_STRAW: (90.0, 160.0),
    CropType.SUGARCANE_TRASH: (100.0, 180.0),
    CropType.COTTON_STALK: (70.0, 140.0),
    CropType.MAIZE_STOVER: (85.0, 155.0),
}

# Reference base price (₹ per tonne), by crop type x season.
# Deliberately a flat lookup table, not a model — transparency beats cleverness here.
REFERENCE_PRICE_TABLE: dict[tuple[CropType, Season], float] = {
    (CropType.PADDY_STRAW, Season.KHARIF): 2200.0,
    (CropType.PADDY_STRAW, Season.RABI): 2400.0,
    (CropType.WHEAT_STRAW, Season.RABI): 2600.0,
    (CropType.SUGARCANE_TRASH, Season.ZAID): 1800.0,
    (CropType.COTTON_STALK, Season.KHARIF): 2000.0,
    (CropType.MAIZE_STOVER, Season.KHARIF): 2100.0,
    (CropType.MAIZE_STOVER, Season.RABI): 2150.0,
}

DEFAULT_BASE_PRICE = 1900.0  # fallback if crop/season combo not in table
DISTANCE_PENALTY_PER_KM = 4.0   # ₹ deducted per tonne per km from farm to plant
QUALITY_PENALTY_PER_FLAG = 150.0  # ₹ deducted per tonne per sanity-check flag


@dataclass
class BaleCertificate:
    """The 'birth certificate' created at the baler/CHC — one QR tag per bale."""
    bale_id: str
    farmer_id: str
    crop_type: CropType
    weight_kg: float
    moisture_pct: float
    density_kg_m3: float
    lat: float
    lon: float
    zone_id: str
    created_on: date
    season: Season


@dataclass
class Zone:
    """A geographic reporting unit (e.g., a block/taluk) used for fire-risk scoring."""
    zone_id: str
    recent_fire_count_7d: int      # NASA FIRMS hotspot count in the zone, last 7 days
    days_since_harvest_started: int
    days_left_in_harvest_window: int


@dataclass
class Plant:
    """A buyer facility with a confirmed PO and a daily intake slot."""
    plant_id: str
    lat: float
    lon: float
    accepted_crop_types: set[CropType]
    daily_intake_capacity_tonnes: float
    confirmed_po_tonnage_remaining: float


@dataclass
class SanityFlags:
    moisture_out_of_range: bool = False
    density_out_of_range: bool = False

    @property
    def flag_count(self) -> int:
        return int(self.moisture_out_of_range) + int(self.density_out_of_range)

    @property
    def any_flag(self) -> bool:
        return self.flag_count > 0


@dataclass
class PoolAssignment:
    """The final output object — one truckload pool, ready for a milk-run pickup."""
    pool_id: str
    plant_id: str
    zone_id: str
    bale_ids: list[str]
    total_weight_tonnes: float
    avg_distance_km: float
    zone_risk_score: float
    price_per_tonne: float
    total_pool_value: float
    flagged_bales: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────
# Module 4: Moisture / Density Sanity Check
# ─────────────────────────────────────────────────────────────────────────

class MoistureDensitySanityCheck:
    """
    Lightweight statistical bounds-check — NOT a predictive model.
    Flags a bale the instant its certificate is created, before it ever
    enters a pool, so bad data never contaminates pricing or clustering.
    """

    @staticmethod
    def check(bale: BaleCertificate) -> SanityFlags:
        flags = SanityFlags()

        moisture_lo, moisture_hi = EXPECTED_MOISTURE_RANGE[bale.crop_type]
        if not (moisture_lo <= bale.moisture_pct <= moisture_hi):
            flags.moisture_out_of_range = True

        density_lo, density_hi = EXPECTED_DENSITY_RANGE[bale.crop_type]
        if not (density_lo <= bale.density_kg_m3 <= density_hi):
            flags.density_out_of_range = True

        return flags


# ─────────────────────────────────────────────────────────────────────────
# Module 2: Satellite Risk Model
# ─────────────────────────────────────────────────────────────────────────

class SatelliteRiskModel:
    """
    Computes a per-zone burn-risk score from two explainable signals:
      1. Recent fire-hotspot density in the zone (proxy: NASA FIRMS feed)
      2. How close the zone is to the END of its harvest window
         (farmers are most likely to burn residue in the final days
          before the next sowing cycle, when time pressure is highest)

    Score is bounded 0-100 and built from a simple weighted sum —
    intentionally interpretable so it can be explained bale-by-bale.
    """

    FIRE_WEIGHT = 0.6
    TIME_PRESSURE_WEIGHT = 0.4
    FIRE_SATURATION_COUNT = 10  # fire count at/above which fire-risk component maxes out

    @classmethod
    def score_zone(cls, zone: Zone) -> float:
        # --- Fire signal: normalize recent hotspot count to 0-100 ---
        fire_component = min(
            zone.recent_fire_count_7d / cls.FIRE_SATURATION_COUNT, 1.0
        ) * 100

        # --- Time-pressure signal: how close to the end of the harvest window ---
        total_window = zone.days_since_harvest_started + zone.days_left_in_harvest_window
        if total_window <= 0:
            time_pressure_component = 0.0
        else:
            time_pressure_component = (
                zone.days_since_harvest_started / total_window
            ) * 100

        risk_score = (
            cls.FIRE_WEIGHT * fire_component
            + cls.TIME_PRESSURE_WEIGHT * time_pressure_component
        )
        return round(min(risk_score, 100.0), 2)

    @classmethod
    def score_all(cls, zones: list[Zone]) -> dict[str, float]:
        return {zone.zone_id: cls.score_zone(zone) for zone in zones}


# ─────────────────────────────────────────────────────────────────────────
# Module 3: Reference Pricing Engine
# ─────────────────────────────────────────────────────────────────────────

class ReferencePricingEngine:
    """
    Rule-based lookup: crop type x season x region -> base price/tonne,
    then transparently adjusted for distance and quality flags.
    No ML — every rupee of the final number is traceable to a rule,
    which is the whole point (price disputes are what this kills).
    """

    @staticmethod
    def base_price(crop_type: CropType, season: Season) -> float:
        return REFERENCE_PRICE_TABLE.get((crop_type, season), DEFAULT_BASE_PRICE)

    @staticmethod
    def compute_price_per_tonne(
        crop_type: CropType,
        season: Season,
        distance_km: float,
        flag_count: int,
    ) -> float:
        price = ReferencePricingEngine.base_price(crop_type, season)
        price -= distance_km * DISTANCE_PENALTY_PER_KM
        price -= flag_count * QUALITY_PENALTY_PER_FLAG
        return round(max(price, 0.0), 2)


# ─────────────────────────────────────────────────────────────────────────
# Module 1: Virtual Pooling / Geo-Clustering Model
# ─────────────────────────────────────────────────────────────────────────

class GeoClusteringEngine:
    """
    Groups bales within a radius into truckload-sized pools, matched to
    a plant with remaining PO tonnage and capacity for that crop type.
    Deliberately a greedy nearest-neighbor approach for MVP — not full
    vehicle-routing optimization, per the architecture spec.
    """

    def __init__(self, cluster_radius_km: float = 5.0, truck_capacity_tonnes: float = 9.0):
        self.cluster_radius_km = cluster_radius_km
        self.truck_capacity_tonnes = truck_capacity_tonnes

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance between two lat/lon points, in kilometers."""
        r = 6371.0  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        return 2 * r * math.asin(math.sqrt(a))

    def nearest_plant(self, bale: BaleCertificate, plants: list[Plant]) -> Optional[Plant]:
        eligible = [
            p for p in plants
            if bale.crop_type in p.accepted_crop_types
            and p.confirmed_po_tonnage_remaining > 0
        ]
        if not eligible:
            return None
        return min(
            eligible,
            key=lambda p: self.haversine_km(bale.lat, bale.lon, p.lat, p.lon),
        )

    def build_pools(
        self,
        bales: list[BaleCertificate],
        plants: list[Plant],
        zone_risk_scores: dict[str, float],
        sanity_results: dict[str, SanityFlags],
    ) -> list[PoolAssignment]:
        """
        Greedy algorithm:
          1. Sort bales by their zone's risk score, descending
             (highest fire-risk zones get pooled and picked up first).
          2. Walk the sorted list, greedily grouping bales that are
             within cluster_radius_km of the first bale in the forming
             pool AND heading to the same nearest plant.
          3. Close a pool once it hits truck_capacity_tonnes or no more
             nearby bales are left for that plant.
        """
        # Sort by risk (desc), so at-risk zones are processed first
        bales_sorted = sorted(
            bales,
            key=lambda b: zone_risk_scores.get(b.zone_id, 0.0),
            reverse=True,
        )

        remaining = bales_sorted.copy()
        pools: list[PoolAssignment] = []
        pool_counter = 1

        while remaining:
            seed = remaining.pop(0)
            plant = self.nearest_plant(seed, plants)
            if plant is None:
                continue  # no eligible buyer right now; would re-queue in production

            pool_bales = [seed]
            pool_weight_tonnes = seed.weight_kg / 1000.0
            distances = [self.haversine_km(seed.lat, seed.lon, plant.lat, plant.lon)]

            still_remaining = []
            for candidate in remaining:
                same_plant = self.nearest_plant(candidate, plants) is plant
                dist_to_seed = self.haversine_km(
                    seed.lat, seed.lon, candidate.lat, candidate.lon
                )
                fits_capacity = (
                    pool_weight_tonnes + candidate.weight_kg / 1000.0
                    <= min(self.truck_capacity_tonnes, plant.confirmed_po_tonnage_remaining)
                )

                if same_plant and dist_to_seed <= self.cluster_radius_km and fits_capacity:
                    pool_bales.append(candidate)
                    pool_weight_tonnes += candidate.weight_kg / 1000.0
                    distances.append(
                        self.haversine_km(candidate.lat, candidate.lon, plant.lat, plant.lon)
                    )
                else:
                    still_remaining.append(candidate)

            remaining = still_remaining
            plant.confirmed_po_tonnage_remaining -= pool_weight_tonnes

            zone_id = seed.zone_id
            zone_risk = zone_risk_scores.get(zone_id, 0.0)
            avg_distance = round(statistics.mean(distances), 2)

            flag_counts = [sanity_results[b.bale_id].flag_count for b in pool_bales]
            flagged_ids = [
                b.bale_id for b in pool_bales if sanity_results[b.bale_id].any_flag
            ]
            avg_flag_count = statistics.mean(flag_counts) if flag_counts else 0.0

            price_per_tonne = ReferencePricingEngine.compute_price_per_tonne(
                crop_type=seed.crop_type,
                season=seed.season,
                distance_km=avg_distance,
                flag_count=round(avg_flag_count),
            )

            pools.append(
                PoolAssignment(
                    pool_id=f"POOL-{pool_counter:03d}",
                    plant_id=plant.plant_id,
                    zone_id=zone_id,
                    bale_ids=[b.bale_id for b in pool_bales],
                    total_weight_tonnes=round(pool_weight_tonnes, 3),
                    avg_distance_km=avg_distance,
                    zone_risk_score=zone_risk,
                    price_per_tonne=price_per_tonne,
                    total_pool_value=round(price_per_tonne * pool_weight_tonnes, 2),
                    flagged_bales=flagged_ids,
                )
            )
            pool_counter += 1

        return pools


# ─────────────────────────────────────────────────────────────────────────
# Orchestrator: AgriLoopBrain
# ─────────────────────────────────────────────────────────────────────────

class AgriLoopBrain:
    """
    The single callable service described in the deliverable:
    takes bale certificates + zones + plants, returns pool assignments
    prioritized by burn risk, with transparent pricing and quality flags.
    """

    def __init__(self, cluster_radius_km: float = 5.0, truck_capacity_tonnes: float = 9.0):
        self.sanity_checker = MoistureDensitySanityCheck()
        self.risk_model = SatelliteRiskModel()
        self.clustering_engine = GeoClusteringEngine(cluster_radius_km, truck_capacity_tonnes)

    def process(
        self,
        bales: list[BaleCertificate],
        zones: list[Zone],
        plants: list[Plant],
    ) -> list[PoolAssignment]:
        # Step 1 — sanity-check every bale at certificate creation
        sanity_results = {b.bale_id: self.sanity_checker.check(b) for b in bales}

        # Step 2 — score every zone for fire/burn risk
        zone_risk_scores = self.risk_model.score_all(zones)

        # Step 3 & 4 — cluster into pools (risk-prioritized) and price each pool
        pools = self.clustering_engine.build_pools(
            bales, plants, zone_risk_scores, sanity_results
        )

        # Highest risk pools first in the final output too
        pools.sort(key=lambda p: p.zone_risk_score, reverse=True)
        return pools


# ─────────────────────────────────────────────────────────────────────────
# Demo — synthetic data, run end-to-end
# ─────────────────────────────────────────────────────────────────────────

def _demo() -> None:
    zones = [
        Zone(zone_id="Z1", recent_fire_count_7d=8, days_since_harvest_started=25, days_left_in_harvest_window=5),
        Zone(zone_id="Z2", recent_fire_count_7d=1, days_since_harvest_started=5, days_left_in_harvest_window=25),
        Zone(zone_id="Z3", recent_fire_count_7d=4, days_since_harvest_started=15, days_left_in_harvest_window=15),
    ]

    plants = [
        Plant(
            plant_id="PLANT-A",
            lat=11.02, lon=76.96,
            accepted_crop_types={CropType.PADDY_STRAW, CropType.MAIZE_STOVER},
            daily_intake_capacity_tonnes=40.0,
            confirmed_po_tonnage_remaining=30.0,
        ),
        Plant(
            plant_id="PLANT-B",
            lat=11.10, lon=77.05,
            accepted_crop_types={CropType.WHEAT_STRAW, CropType.COTTON_STALK},
            daily_intake_capacity_tonnes=25.0,
            confirmed_po_tonnage_remaining=20.0,
        ),
    ]

    bales = [
        BaleCertificate("B001", "F001", CropType.PADDY_STRAW, 350, 14.0, 110, 11.021, 76.958, "Z1", date(2026, 9, 10), Season.KHARIF),
        BaleCertificate("B002", "F002", CropType.PADDY_STRAW, 320, 30.0, 105, 11.023, 76.961, "Z1", date(2026, 9, 10), Season.KHARIF),  # moisture flag
        BaleCertificate("B003", "F003", CropType.PADDY_STRAW, 400, 15.5, 90, 11.019, 76.963, "Z1", date(2026, 9, 10), Season.KHARIF),
        BaleCertificate("B004", "F004", CropType.MAIZE_STOVER, 300, 18.0, 95, 11.030, 76.970, "Z1", date(2026, 9, 11), Season.KHARIF),
        BaleCertificate("B005", "F005", CropType.WHEAT_STRAW, 380, 10.0, 130, 11.101, 77.052, "Z2", date(2026, 9, 12), Season.RABI),
        BaleCertificate("B006", "F006", CropType.WHEAT_STRAW, 360, 22.0, 200, 11.104, 77.048, "Z2", date(2026, 9, 12), Season.RABI),  # moisture + density flag
        BaleCertificate("B007", "F007", CropType.COTTON_STALK, 290, 9.0, 100, 11.098, 77.055, "Z3", date(2026, 9, 13), Season.KHARIF),
    ]

    brain = AgriLoopBrain(cluster_radius_km=5.0, truck_capacity_tonnes=9.0)
    pools = brain.process(bales, zones, plants)

    print(f"{'=' * 70}\nAGRILOOP BRAIN — POOL ASSIGNMENTS (risk-prioritized)\n{'=' * 70}")
    for pool in pools:
        print(f"\n{pool.pool_id}  ->  {pool.plant_id}  (zone {pool.zone_id})")
        print(f"  Bales:            {pool.bale_ids}")
        print(f"  Weight:           {pool.total_weight_tonnes} t")
        print(f"  Avg distance:     {pool.avg_distance_km} km")
        print(f"  Zone risk score:  {pool.zone_risk_score} / 100")
        print(f"  Price/tonne:      Rs {pool.price_per_tonne}")
        print(f"  Total pool value: Rs {pool.total_pool_value}")
        if pool.flagged_bales:
            print(f"  ⚠ Flagged bales (quality anomaly): {pool.flagged_bales}")


if __name__ == "__main__":
    _demo()

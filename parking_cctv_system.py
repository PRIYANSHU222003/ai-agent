"""Parking CCTV security system.

This module provides a lightweight, extensible CCTV monitoring system for parking
areas. It models cameras, parking slots, occupancy events, and generated alerts.

The implementation is intentionally dependency-light so it can run in constrained
environments while still being practical to integrate with real CV pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Iterable, List, Optional, Set


class AlertLevel(str, Enum):
    """Severity level for generated alerts."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Camera:
    """Represents a CCTV camera installed in the parking area."""

    camera_id: str
    location: str
    monitored_slots: Set[str]
    is_online: bool = True
    last_heartbeat: Optional[datetime] = None

    def heartbeat(self, when: datetime) -> None:
        self.last_heartbeat = when
        self.is_online = True


@dataclass(slots=True)
class ParkingSlot:
    """Represents a parking slot and constraints tied to it."""

    slot_id: str
    zone: str
    reserved_for: Optional[str] = None
    max_stay_minutes: int = 240


@dataclass(slots=True)
class OccupancyEvent:
    """Input event from a detection pipeline.

    event_type should be either "ENTER" or "EXIT".
    """

    timestamp: datetime
    camera_id: str
    slot_id: str
    plate_number: str
    event_type: str


@dataclass(slots=True)
class Alert:
    """Generated security alert."""

    timestamp: datetime
    level: AlertLevel
    title: str
    description: str
    slot_id: Optional[str] = None
    camera_id: Optional[str] = None
    plate_number: Optional[str] = None


@dataclass(slots=True)
class ActiveParkingSession:
    plate_number: str
    slot_id: str
    camera_id: str
    started_at: datetime


@dataclass
class ParkingCCTVSystem:
    """Core parking CCTV security coordinator."""

    cameras: Dict[str, Camera] = field(default_factory=dict)
    slots: Dict[str, ParkingSlot] = field(default_factory=dict)
    authorized_plates: Set[str] = field(default_factory=set)
    active_sessions: Dict[str, ActiveParkingSession] = field(default_factory=dict)
    alerts: List[Alert] = field(default_factory=list)
    heartbeat_timeout_minutes: int = 5

    def register_camera(self, camera: Camera) -> None:
        self.cameras[camera.camera_id] = camera

    def register_slot(self, slot: ParkingSlot) -> None:
        self.slots[slot.slot_id] = slot

    def authorize_plate(self, plate_number: str) -> None:
        self.authorized_plates.add(plate_number.upper())

    def process_heartbeat(self, camera_id: str, when: datetime) -> None:
        camera = self.cameras.get(camera_id)
        if not camera:
            self._emit(
                Alert(
                    timestamp=when,
                    level=AlertLevel.WARNING,
                    title="Unknown Camera Heartbeat",
                    description=f"Heartbeat received from unknown camera '{camera_id}'.",
                    camera_id=camera_id,
                )
            )
            return
        camera.heartbeat(when)

    def process_event(self, event: OccupancyEvent) -> None:
        plate_number = event.plate_number.upper()
        camera = self.cameras.get(event.camera_id)
        slot = self.slots.get(event.slot_id)

        if not camera:
            self._emit(
                Alert(
                    timestamp=event.timestamp,
                    level=AlertLevel.CRITICAL,
                    title="Unknown Camera Event",
                    description=f"Occupancy event from unknown camera '{event.camera_id}'.",
                    camera_id=event.camera_id,
                    slot_id=event.slot_id,
                    plate_number=plate_number,
                )
            )
            return

        if not slot:
            self._emit(
                Alert(
                    timestamp=event.timestamp,
                    level=AlertLevel.WARNING,
                    title="Unknown Parking Slot",
                    description=f"Camera '{event.camera_id}' reported unknown slot '{event.slot_id}'.",
                    camera_id=event.camera_id,
                    slot_id=event.slot_id,
                    plate_number=plate_number,
                )
            )
            return

        if event.event_type == "ENTER":
            self.active_sessions[plate_number] = ActiveParkingSession(
                plate_number=plate_number,
                slot_id=event.slot_id,
                camera_id=event.camera_id,
                started_at=event.timestamp,
            )
            self._check_authorization(event.timestamp, slot, plate_number, event.camera_id)
        elif event.event_type == "EXIT":
            self.active_sessions.pop(plate_number, None)
        else:
            self._emit(
                Alert(
                    timestamp=event.timestamp,
                    level=AlertLevel.WARNING,
                    title="Invalid Event Type",
                    description=f"Unsupported event type '{event.event_type}'.",
                    camera_id=event.camera_id,
                    slot_id=event.slot_id,
                    plate_number=plate_number,
                )
            )

    def sweep(self, now: datetime) -> List[Alert]:
        """Run periodic checks for camera health and overstays.

        Returns alerts generated during this sweep.
        """

        generated_before = len(self.alerts)
        timeout = timedelta(minutes=self.heartbeat_timeout_minutes)

        for camera in self.cameras.values():
            if camera.last_heartbeat is None or now - camera.last_heartbeat > timeout:
                if camera.is_online:
                    camera.is_online = False
                    self._emit(
                        Alert(
                            timestamp=now,
                            level=AlertLevel.CRITICAL,
                            title="Camera Offline",
                            description=(
                                f"Camera '{camera.camera_id}' at {camera.location} missed heartbeat "
                                f"for over {self.heartbeat_timeout_minutes} minutes."
                            ),
                            camera_id=camera.camera_id,
                        )
                    )

        for plate, session in list(self.active_sessions.items()):
            slot = self.slots.get(session.slot_id)
            if not slot:
                continue
            parked_minutes = int((now - session.started_at).total_seconds() / 60)
            if parked_minutes > slot.max_stay_minutes:
                self._emit(
                    Alert(
                        timestamp=now,
                        level=AlertLevel.WARNING,
                        title="Overstay Detected",
                        description=(
                            f"Vehicle {plate} has exceeded max stay in slot {slot.slot_id} "
                            f"({parked_minutes} min > {slot.max_stay_minutes} min)."
                        ),
                        slot_id=slot.slot_id,
                        camera_id=session.camera_id,
                        plate_number=plate,
                    )
                )

        return self.alerts[generated_before:]

    def iter_alerts(self) -> Iterable[Alert]:
        return iter(self.alerts)

    def _check_authorization(
        self, timestamp: datetime, slot: ParkingSlot, plate_number: str, camera_id: str
    ) -> None:
        if slot.reserved_for and plate_number not in self.authorized_plates:
            self._emit(
                Alert(
                    timestamp=timestamp,
                    level=AlertLevel.WARNING,
                    title="Unauthorized Reserved Slot Usage",
                    description=(
                        f"Vehicle {plate_number} entered reserved slot {slot.slot_id} "
                        f"({slot.reserved_for})."
                    ),
                    slot_id=slot.slot_id,
                    camera_id=camera_id,
                    plate_number=plate_number,
                )
            )

    def _emit(self, alert: Alert) -> None:
        self.alerts.append(alert)


if __name__ == "__main__":
    system = ParkingCCTVSystem(heartbeat_timeout_minutes=3)

    system.register_camera(Camera("CAM-01", "Entry Gate", {"A1", "A2"}))
    system.register_camera(Camera("CAM-02", "VIP Zone", {"VIP-1"}))

    system.register_slot(ParkingSlot("A1", zone="General", max_stay_minutes=60))
    system.register_slot(ParkingSlot("A2", zone="General", max_stay_minutes=60))
    system.register_slot(
        ParkingSlot("VIP-1", zone="VIP", reserved_for="Management", max_stay_minutes=30)
    )

    system.authorize_plate("VIP-0001")

    t0 = datetime.now()
    system.process_heartbeat("CAM-01", t0)
    system.process_heartbeat("CAM-02", t0)

    system.process_event(
        OccupancyEvent(
            timestamp=t0,
            camera_id="CAM-02",
            slot_id="VIP-1",
            plate_number="XYZ-100",
            event_type="ENTER",
        )
    )

    sweep_alerts = system.sweep(t0 + timedelta(minutes=35))

    for alert in sweep_alerts:
        print(f"[{alert.level}] {alert.title}: {alert.description}")

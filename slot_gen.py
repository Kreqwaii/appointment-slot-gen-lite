#!/usr/bin/env python3
"""
appointment-slot-gen-lite (slot_gen.py)
Zero-dependency Python 3.9+ CLI utility for generating available appointment slots
given working hours, service duration, breaks, and existing bookings.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True, order=True)
class TimeInterval:
    start: int  # minutes since 00:00
    end: int    # minutes since 00:00

    def __post_init__(self) -> None:
        if not (0 <= self.start < self.end <= 24 * 60):
            raise ValueError(
                f"Invalid time interval: {minutes_to_hhmm(self.start)}-{minutes_to_hhmm(self.end)}"
            )

    def overlaps(self, other: "TimeInterval") -> bool:
        return self.start < other.end and other.start < self.end

    def format_hhmm(self) -> str:
        return f"{minutes_to_hhmm(self.start)}-{minutes_to_hhmm(self.end)}"


def hhmm_to_minutes(value: str) -> int:
    value = value.strip()
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format '{value}', expected HH:MM")
    h_str, m_str = parts
    if not (h_str.isdigit() and m_str.isdigit()):
        raise ValueError(f"Invalid time format '{value}', expected HH:MM")
    h, m = int(h_str), int(m_str)
    if h == 24 and m == 0:
        return 24 * 60
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Time out of range '{value}'")
    return h * 60 + m


def minutes_to_hhmm(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def parse_interval(spec: str) -> TimeInterval:
    spec = spec.strip()
    if "-" not in spec:
        raise ValueError(f"Invalid interval '{spec}', expected HH:MM-HH:MM")
    start_s, end_s = spec.split("-", 1)
    return TimeInterval(hhmm_to_minutes(start_s), hhmm_to_minutes(end_s))


def generate_slots(
    work_hours: TimeInterval,
    duration_min: int,
    step_min: Optional[int] = None,
    buffer_min: int = 0,
    breaks: Iterable[TimeInterval] = (),
    booked: Iterable[TimeInterval] = (),
    min_start_min: Optional[int] = None,
) -> List[TimeInterval]:
    """
    Generate available appointment slots within `work_hours`.

    - `duration_min`: length of the service in minutes (> 0).
    - `step_min`: grid step in minutes (defaults to `duration_min`).
    - `buffer_min`: extra buffer minutes after a slot before next booking/break (>= 0).
      Note: buffer is checked against `booked` / `breaks`? Standard behavior:
      a candidate slot [t, t + duration_min) is free if [t, t + duration_min) does not
      overlap any break, and [t, t + duration_min + buffer_min) does not overlap any
      existing booking (and existing bookings + buffer don't overlap candidate).
      Here we keep it clean: slot [t, t + duration_min) must not overlap any break or
      booked interval, and if `buffer_min > 0`, we also require `buffer_min` gap around
      booked intervals.
    - `min_start_min`: optional cutoff (e.g. current time + lead time).
    """
    if duration_min <= 0:
        raise ValueError("duration_min must be > 0")
    step = duration_min if step_min is None else step_min
    if step <= 0:
        raise ValueError("step_min must be > 0")
    if buffer_min < 0:
        raise ValueError("buffer_min must be >= 0")

    break_list = list(breaks)
    booked_list = list(booked)

    slots: List[TimeInterval] = []
    cursor = work_hours.start
    while cursor + duration_min <= work_hours.end:
        if min_start_min is not None and cursor < min_start_min:
            cursor += step
            continue

        candidate = TimeInterval(cursor, cursor + duration_min)

        # Check breaks (strictly no overlap with service duration)
        if any(candidate.overlaps(b) for b in break_list):
            cursor += step
            continue

        # Check booked intervals (including optional buffer around bookings)
        conflict = False
        for bk in booked_list:
            bk_start = max(0, bk.start - buffer_min)
            bk_end = min(24 * 60, bk.end + buffer_min)
            if candidate.overlaps(TimeInterval(bk_start, bk_end)):
                conflict = True
                break

        if not conflict:
            slots.append(candidate)

        cursor += step

    return slots


def _run_self_test() -> int:
    # 1. Basic generation without breaks/bookings
    wh = parse_interval("09:00-12:00")
    s1 = generate_slots(wh, duration_min=60)
    assert [x.format_hhmm() for x in s1] == ["09:00-10:00", "10:00-11:00", "11:00-12:00"], s1

    # 2. With lunch break and existing booking
    s2 = generate_slots(
        parse_interval("09:00-18:00"),
        duration_min=60,
        breaks=[parse_interval("13:00-14:00")],
        booked=[parse_interval("10:00-11:30"), parse_interval("15:00-16:00")],
    )
    assert [x.format_hhmm() for x in s2] == [
        "09:00-10:00",
        "12:00-13:00",
        "14:00-15:00",
        "16:00-17:00",
        "17:00-18:00",
    ], s2

    # 3. Custom step (30 min) with 60 min duration & 15 min buffer
    s3 = generate_slots(
        parse_interval("10:00-13:00"),
        duration_min=60,
        step_min=30,
        buffer_min=15,
        booked=[parse_interval("11:00-11:30")],
    )
    # 11:00-11:30 with 15m buffer blocks [10:45, 11:45).
    # 10:00-11:00 overlaps [10:45, 11:45) -> blocked
    # 12:00-13:00 does not overlap [10:45, 11:45) -> free
    assert [x.format_hhmm() for x in s3] == ["12:00-13:00"], s3

    # 4. Cutoff min_start_min
    s4 = generate_slots(
        parse_interval("09:00-12:00"),
        duration_min=45,
        step_min=45,
        min_start_min=hhmm_to_minutes("10:00"),
    )
    assert [x.format_hhmm() for x in s4] == ["10:30-11:15", "11:15-12:00"], s4

    # 5. Validation errors
    for bad in ("25:00-26:00", "12:00-11:00", "invalid"):
        try:
            parse_interval(bad)
            raise AssertionError(f"Expected ValueError for {bad}")
        except ValueError:
            pass

    print("SELF-TEST: 5/5 PASSED (100% PASS)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slot_gen.py",
        description="Zero-dependency appointment slot generator CLI.",
    )
    p.add_argument(
        "--work",
        default="09:00-18:00",
        help="Working hours as HH:MM-HH:MM (default: 09:00-18:00)",
    )
    p.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Service duration in minutes (default: 60)",
    )
    p.add_argument(
        "--step",
        type=int,
        default=None,
        help="Slot grid step in minutes (default: same as --duration)",
    )
    p.add_argument(
        "--buffer",
        type=int,
        default=0,
        help="Buffer minutes around existing bookings (default: 0)",
    )
    p.add_argument(
        "--break",
        dest="breaks",
        action="append",
        default=[],
        help="Break interval HH:MM-HH:MM (repeatable)",
    )
    p.add_argument(
        "--booked",
        action="append",
        default=[],
        help="Booked interval HH:MM-HH:MM (repeatable)",
    )
    p.add_argument(
        "--min-start",
        default=None,
        help="Earliest allowed start time HH:MM",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output slots as JSON",
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in self-tests and exit",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return _run_self_test()

    try:
        work_hours = parse_interval(args.work)
        breaks = [parse_interval(b) for b in args.breaks]
        booked = [parse_interval(b) for b in args.booked]
        min_start = hhmm_to_minutes(args.min_start) if args.min_start else None

        slots = generate_slots(
            work_hours=work_hours,
            duration_min=args.duration,
            step_min=args.step,
            buffer_min=args.buffer,
            breaks=breaks,
            booked=booked,
            min_start_min=min_start,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = [
            {
                "start": minutes_to_hhmm(s.start),
                "end": minutes_to_hhmm(s.end),
                "label": s.format_hhmm(),
            }
            for s in slots
        ]
        print(json.dumps(payload, indent=2))
    else:
        if not slots:
            print("No available slots.")
        else:
            for s in slots:
                print(s.format_hhmm())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

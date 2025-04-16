# tests/test_viewer_utils.py

import pytest
from datetime import datetime, timedelta
from viewer_utils import generate_timeline, closest_match

def test_generate_simple():
    start = datetime(2023,1,1,0,0,0)
    end   = datetime(2023,1,1,0,20,0)
    tl = generate_timeline(start, end, step_minutes=5)
    assert tl == [
        datetime(2023,1,1,0,0),
        datetime(2023,1,1,0,5),
        datetime(2023,1,1,0,10),
        datetime(2023,1,1,0,15),
        datetime(2023,1,1,0,20),
    ]

def test_generate_empty_when_end_before_start():
    assert generate_timeline(datetime(2023,1,1,1,0), datetime(2023,1,1,0,0), 5) == []

def test_closest_match_picks_nearest():
    base = datetime(2023,1,1,12,0)
    images = [
        {"timestamp": base + timedelta(minutes=10), "label":"later"},
        {"timestamp": base - timedelta(minutes=3),  "label":"earlier"},
    ]
    # if target 12:05, nearest is 12:10 vs 11:57 → 12:10 is closer (5 vs 3? actually 3 is smaller diff)
    # so for 12:05 target, 11:57 (earlier) is 8 minutes diff vs 5 minutes to 12:10, so picks "later"
    target = base + timedelta(minutes=5)
    match = closest_match(images, target)
    assert match["label"] == "later"

def test_closest_match_empty_returns_none():
    assert closest_match([], datetime.now()) is None
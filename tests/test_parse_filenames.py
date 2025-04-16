from datetime import datetime

import pytest

from parser.parse_filenames import parse_filename


def test_hi_res():
    fn = "ExperimentalG4_HiRest_180420UTC150040.jpg"
    res = parse_filename(fn)
    assert res["station"] == "ExperimentalG4"
    assert res["resolution"] == "HiRes"
    assert res["timestamp"] == datetime(2020, 4, 18, 15, 0, 40)


def test_lo_res():
    fn = "ExperimentalG4_LoRest_180420UTC0100.jpg"
    res = parse_filename(fn)
    assert res["station"] == "ExperimentalG4"
    assert res["resolution"] == "LoRes"
    assert res["timestamp"] == datetime(2020, 4, 18, 1, 0, 0)


def test_bad_name():
    assert parse_filename("foo_bar.jpg") is None

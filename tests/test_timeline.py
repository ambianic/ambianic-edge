import pytest
import os

from ambianic.webapp.server.samples import get_timeline

# logs size is 24 records long, splitted in 3 files of 8 events each


def test_get_timeline_overflow():
    data_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "./timeline"
    )
    res = get_timeline(before_datetime=None, page=7, data_dir=data_dir)
    assert len(res) == 0


def test_get_timelines():
    data_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "./timeline"
    )
    for page in range(1, 6):
        res = get_timeline(before_datetime=None, page=page, data_dir=data_dir)
        # print("page", page, "list", list(map(lambda r: r["id"], res)), "\n---")
        assert len(res) > 0
        assert res[0]["id"] == "page%d" % page

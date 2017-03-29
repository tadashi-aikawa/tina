# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from chalicelib.models import SpecialEvents, Event


class TestFindById:
    def test_normal(self):
        s = SpecialEvents.from_dict({
            "start_work": {"id": 1, "messages": ["a"]},
            "lunch_start": {"id": 2, "messages": ["b"]},
            "lunch_end": {"id": 3, "messages": ["c"]},
            "must_task_completed": {"id": 4, "messages": ["d"]},
            "leave_work": {"id": 5, "messages": ["e"]},
            "start_make_schedule": {"id": 6, "messages": ["f"]}
        })

        actual = s.find_by_id(3)  # type: Event

        assert actual.id == 3

    def test_not_found(self):
        s = SpecialEvents.from_dict({
            "start_work": {"id": 1, "messages": ["a"]},
            "lunch_start": {"id": 2, "messages": ["b"]},
            "lunch_end": {"id": 3, "messages": ["c"]},
            "must_task_completed": {"id": 4, "messages": ["d"]},
            "leave_work": {"id": 5, "messages": ["e"]},
            "start_make_schedule": {"id": 6, "messages": ["f"]}
        })

        actual = s.find_by_id(7)  # type: Event

        assert actual is None

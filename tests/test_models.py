# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from chalicelib.models import remove_emoji


class TestRemoveEmoji:
    def test_normal(self):
        assert remove_emoji(":emoji:hoge") == "hoge"
        assert remove_emoji(":emoji1::emoji2:hoge") == "hoge"
        assert remove_emoji(":emoji1::emoji2:hoge:emoji3:") == "hoge"

    def test_normal_with_space(self):
        assert remove_emoji(":emoji: hoge") == "hoge"
        assert remove_emoji(":emoji1: :emoji2: hoge") == "hoge"
        assert remove_emoji(":emoji1: :emoji2: hoge :emoji3:") == "hoge"

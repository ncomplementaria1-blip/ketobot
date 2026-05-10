from datetime import datetime, timezone
from unittest.mock import MagicMock

import fb_ads_scraper as scraper


def _ad(id_: str, start: str, stop: str | None = None, page="Keto CL"):
    return {
        "id": id_,
        "page_id": "1",
        "page_name": page,
        "ad_delivery_start_time": start,
        "ad_delivery_stop_time": stop,
        "ad_creative_bodies": [f"copy {id_}"],
        "ad_snapshot_url": f"https://fb.com/snap/{id_}",
        "languages": ["es"],
        "publisher_platforms": ["facebook"],
    }


def test_days_active_uses_now_for_active_ads(monkeypatch):
    fixed = datetime(2026, 5, 10, tzinfo=timezone.utc)

    class _DT(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(scraper, "datetime", _DT)
    days = scraper._days_active("2026-01-01T00:00:00+0000", None)
    assert days == 129


def test_days_active_uses_stop_when_present():
    days = scraper._days_active(
        "2024-01-01T00:00:00+0000", "2024-02-10T00:00:00+0000"
    )
    assert days == 40


def test_normalize_pulls_first_creative_body():
    ad = scraper._normalize(_ad("a1", "2025-01-01T00:00:00+0000"))
    assert ad.id == "a1"
    assert ad.creative_body == "copy a1"
    assert ad.page_name == "Keto CL"


def test_top_longest_running_sorts_and_truncates(monkeypatch):
    raws = [
        _ad("new", "2026-04-01T00:00:00+0000"),
        _ad("old", "2024-01-01T00:00:00+0000"),
        _ad("mid", "2025-09-01T00:00:00+0000"),
    ]
    monkeypatch.setattr(scraper, "fetch_ads", lambda *a, **kw: iter(raws))
    top = scraper.top_longest_running("token", limit=2)
    assert [a.id for a in top] == ["old", "mid"]


def test_fetch_ads_paginates_and_respects_max_pages():
    session = MagicMock()
    page1 = MagicMock()
    page1.json.return_value = {
        "data": [_ad("1", "2025-01-01T00:00:00+0000")],
        "paging": {"next": "https://graph.facebook.com/next"},
    }
    page1.raise_for_status = MagicMock()
    page2 = MagicMock()
    page2.json.return_value = {
        "data": [_ad("2", "2025-02-01T00:00:00+0000")],
        "paging": {},
    }
    page2.raise_for_status = MagicMock()
    session.get.side_effect = [page1, page2]

    out = list(
        scraper.fetch_ads(
            "tok",
            country="CL",
            search_terms="keto",
            page_size=50,
            max_pages=5,
            session=session,
        )
    )
    assert [r["id"] for r in out] == ["1", "2"]
    assert session.get.call_count == 2
    # First call carries params; the cursor URL must be followed unmodified.
    first_kwargs = session.get.call_args_list[0].kwargs
    assert first_kwargs["params"]["ad_active_status"] == "ACTIVE"
    assert first_kwargs["params"]["ad_reached_countries"] == '["CL"]'
    second_kwargs = session.get.call_args_list[1].kwargs
    assert second_kwargs["params"] is None


def test_main_errors_without_token(monkeypatch, capsys):
    monkeypatch.delenv("FB_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(scraper, "load_dotenv", lambda: None)
    rc = scraper.main([])
    assert rc == 2
    assert "FB_ACCESS_TOKEN" in capsys.readouterr().err

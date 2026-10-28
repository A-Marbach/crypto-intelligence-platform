
from app.services.candle_service import validate_candles


HOUR = 3_600_000


def make_candle(timestamp, close="100"):
    return {
        "timestamp": timestamp,
        "open": "100",
        "high": "110",
        "low": "90",
        "close": close,
        "volume": "10",
    }


def test_excludes_unfinished_candle():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=HOUR + 30 * 60 * 1000,
    )

    assert result["quality"]["valid_count"] == 1
    assert result["quality"]["unfinished_count"] == 1


def test_detects_missing_candles():
    candles = [
        make_candle(0),
        make_candle(2 * HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=3 * HOUR,
    )

    assert result["quality"]["missing_count"] == 1
    assert result["quality"]["has_gaps"] is True


def test_rejects_invalid_prices():
    candles = [
        make_candle(0, close="200"),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=HOUR,
    )

    assert result["quality"]["valid_count"] == 0
    assert result["quality"]["invalid_count"] == 1


def test_accepts_valid_candles():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=2 * HOUR,
    )

    assert result["quality"]["valid_count"] == 2
    assert result["quality"]["has_gaps"] is False



def test_detects_stale_candle_data():
    candles = [
        make_candle(0),
        make_candle(HOUR),
        make_candle(2 * HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=10 * HOUR,
    )

    quality = result["quality"]

    assert quality["valid_count"] == 3
    assert quality["is_fresh"] is False
    assert quality["last_candle_timestamp"] == 2 * HOUR


def test_accepts_latest_completed_candle():
    candles = [
        make_candle(0),
        make_candle(HOUR),
        make_candle(2 * HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=3 * HOUR + 30 * 60 * 1000,
    )

    quality = result["quality"]

    assert quality["is_fresh"] is True
    assert quality["last_candle_timestamp"] == 2 * HOUR


def test_reports_exact_missing_timestamps():
    candles = [
        make_candle(0),
        make_candle(3 * HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=4 * HOUR,
    )

    quality = result["quality"]

    assert quality["missing_count"] == 2
    assert quality["missing_timestamps"] == [
        HOUR,
        2 * HOUR,
    ]



def test_latest_completed_candle_at_exact_hour():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=2 * HOUR,
    )

    quality = result["quality"]

    assert quality["is_fresh"] is True
    assert quality["expected_last_timestamp"] == HOUR


def test_candle_is_not_finished_before_hour_end():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=2 * HOUR - 1,
    )

    quality = result["quality"]

    assert quality["unfinished_count"] == 1
    assert quality["is_fresh"] is True
    assert quality["expected_last_timestamp"] == 0


def test_daily_candle_boundary():
    day = 24 * HOUR

    candles = [
        make_candle(0),
        make_candle(day),
    ]

    result = validate_candles(
        candles,
        interval="1d",
        now_ms=2 * day,
    )

    assert result["quality"]["is_fresh"] is True
    assert result["quality"]["expected_last_timestamp"] == day


def test_four_hour_candle_boundary():
    four_hours = 4 * HOUR

    candles = [
        make_candle(0),
        make_candle(four_hours),
    ]

    result = validate_candles(
        candles,
        interval="4h",
        now_ms=2 * four_hours,
    )

    assert result["quality"]["is_fresh"] is True
    assert (
        result["quality"]["expected_last_timestamp"]
        == four_hours
    )

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from core.scheduler import run_once, run_scheduler
from ingest.providers.base import TradeRecord


# Helper function to build fake records
def make_rec(symbol="AAPL", price=100.0, size=1.0):
    return TradeRecord(
        symbol=symbol,
        ts=datetime.now(timezone.utc),
        price=price,
        size=size,
        source="finnhub"
    )


# ---------------------------------------------------------
# TEST 1 — run_once works end-to-end
# ---------------------------------------------------------
@patch("core.scheduler.write")
@patch("core.scheduler.validate")
@patch("core.scheduler.fetch_all")
def test_run_once_happy_path(mock_fetch, mock_validate, mock_write):
    # Setup mocked pipeline
    mock_fetch.return_value = [make_rec()]
    mock_validate.return_value = [make_rec()]
    mock_write.return_value = 1

    result = run_once()

    assert result == 1
    mock_fetch.assert_called_once()
    mock_validate.assert_called_once()
    mock_write.assert_called_once()


# ---------------------------------------------------------
# TEST 2 — run_once handles fetch errors
# ---------------------------------------------------------
@patch("core.scheduler.fetch_all")
def test_run_once_fetch_error(mock_fetch):
    mock_fetch.side_effect = Exception("fetch failed")

    with pytest.raises(Exception):
        run_once()


# ---------------------------------------------------------
# TEST 3 — run_once handles validation errors
# ---------------------------------------------------------
@patch("core.scheduler.fetch_all")
@patch("core.scheduler.validate")
def test_run_once_validation_error(mock_validate, mock_fetch):
    mock_fetch.return_value = [make_rec()]
    mock_validate.side_effect = Exception("validation error")

    with pytest.raises(Exception):
        run_once()


# ---------------------------------------------------------
# TEST 4 — run_once handles writer errors
# ---------------------------------------------------------
@patch("core.scheduler.fetch_all")
@patch("core.scheduler.validate")
@patch("core.scheduler.write")
def test_run_once_writer_error(mock_write, mock_validate, mock_fetch):
    mock_fetch.return_value = [make_rec()]
    mock_validate.return_value = [make_rec()]
    mock_write.side_effect = Exception("writer error")

    with pytest.raises(Exception):
        run_once()


# ---------------------------------------------------------
# TEST 5 — run_scheduler runs exactly 2 cycles then stops
# ---------------------------------------------------------
@patch("core.scheduler.Config")
@patch("core.scheduler.time.sleep")
@patch("core.scheduler.write")
@patch("core.scheduler.validate")
@patch("core.scheduler.fetch_all")
def test_run_scheduler_two_cycles(
    mock_fetch, mock_validate, mock_write, mock_sleep, mock_config
):
    # Run two cycles then force KeyboardInterrupt
    # First two cycles return records, third raises KeyboardInterrupt
    mock_fetch.side_effect = [[make_rec()], [make_rec()], KeyboardInterrupt()]
    mock_validate.return_value = [make_rec()]
    mock_write.return_value = 1

    mock_config.SCHEDULER_INTERVAL_SEC = 10

    run_scheduler()

    # Should have run exactly 2 cycles
    assert mock_fetch.call_count == 3  # 2 cycles + 1 for KeyboardInterrupt
    assert mock_validate.call_count == 2
    assert mock_write.call_count == 2

    # Scheduler should have slept at least once
    assert mock_sleep.called


# ---------------------------------------------------------
# TEST 6 — scheduler logs error but continues on failure
# ---------------------------------------------------------
@patch("core.scheduler.error")
@patch("core.scheduler.time.sleep")
@patch("core.scheduler.Config")
@patch("core.scheduler.fetch_all")
def test_scheduler_continues_after_error(mock_fetch, mock_config, mock_sleep, mock_error):
    # First cycle fails, second cycle stops scheduler
    mock_fetch.side_effect = [
        Exception("fetch failed"),   # first cycle
        KeyboardInterrupt()          # second cycle stops loop
    ]

    mock_config.SCHEDULER_INTERVAL_SEC = 5

    run_scheduler()

    # Should log the first error
    assert mock_error.called


# ---------------------------------------------------------
# TEST 7 — verify scheduler sleep time is computed properly
# ---------------------------------------------------------
@patch("core.scheduler.time.sleep")
@patch("core.scheduler.Config")
@patch("core.scheduler.write")
@patch("core.scheduler.validate")
@patch("core.scheduler.fetch_all")
def test_scheduler_sleep_timing(
    mock_fetch, mock_validate, mock_write, mock_config, mock_sleep
):
    mock_fetch.side_effect = [
        [make_rec()],
        KeyboardInterrupt()
    ]

    mock_validate.return_value = [make_rec()]
    mock_write.return_value = 1

    mock_config.SCHEDULER_INTERVAL_SEC = 10

    with patch("core.scheduler.datetime") as mock_dt:
        # Pretend cycle start is t=0
        mock_dt.now.side_effect = [
            datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # cycle start
            datetime(2025, 1, 1, 0, 0, 3, tzinfo=timezone.utc),  # after work: elapsed 3 sec
            datetime(2025, 1, 1, 0, 0, 3, tzinfo=timezone.utc)   # for next cycle (not used)
        ]

        run_scheduler()

    # Sleep should have been called with interval - elapsed
    mock_sleep.assert_called_with(7)

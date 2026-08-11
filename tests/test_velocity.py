import time
import pytest
import fakeredis.aioredis
from app.services.velocity_checker import VelocityChecker


@pytest.mark.asyncio
async def test_velocity_sliding_window_burst():
    # Initialize velocity checker with fake redis server
    checker = VelocityChecker()
    checker.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    card_id = "test_velocity_card_001"
    now = time.time()

    # 1. First transaction: low amount, baseline
    penalty1, reasons1, metrics1 = await checker.check_and_update(
        card_id=card_id,
        txn_id="t1",
        amount=50.0,
        timestamp=now
    )
    assert penalty1 == 0.0
    assert metrics1["txn_count_10m"] == 1
    assert metrics1["total_amount_1h"] == 50.0

    # 2. Simulate rapid burst of 5 transactions within 60 seconds
    for i in range(2, 6):
        penalty, reasons, metrics = await checker.check_and_update(
            card_id=card_id,
            txn_id=f"t{i}",
            amount=100.0,
            timestamp=now + i
        )

    # After 5th transaction, velocity burst penalty (+15 points) should trigger
    assert penalty >= 15.0
    assert "HIGH_VELOCITY_BURST" in reasons
    assert metrics["txn_count_10m"] == 5

    # 3. Simulate high spend exceeding $5,000 threshold
    penalty_high_spend, reasons_spend, metrics_spend = await checker.check_and_update(
        card_id=card_id,
        txn_id="t_big_spend",
        amount=5500.0,
        timestamp=now + 10
    )

    assert "HIGH_VOLUME_SPEND" in reasons_spend
    assert metrics_spend["total_amount_1h"] >= 5000.0

    await checker.close()

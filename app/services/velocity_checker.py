import time
from typing import List, Tuple
import redis.asyncio as aioredis
from app.config import settings


class VelocityChecker:
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            self.redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        else:
            self.redis_url = redis_url
        self.redis_client = None

    async def get_client(self) -> aioredis.Redis:
        if self.redis_client is None:
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def close(self):
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

    async def check_and_update(
        self,
        card_id: str,
        txn_id: str,
        amount: float,
        timestamp: float = None
    ) -> Tuple[float, List[str], dict]:
        """
        Executes sliding window check on Redis ZSETs:
        - Last 10 minutes count (600s window)
        - Last 1 hour amount sum (3600s window)
        Returns (velocity_penalty_score [0-30], reasons [List[str]], metrics [dict]).
        """
        if timestamp is None:
            timestamp = time.time()

        now = timestamp
        window_10m_start = now - 600
        window_1h_start = now - 3600

        key_count = f"velocity:count:{card_id}"
        key_amount = f"velocity:amount:{card_id}"

        reasons = []
        metrics = {}

        try:
            r = await self.get_client()
            async with r.pipeline(transaction=True) as pipe:
                # 1. Clean old entries
                pipe.zremrangebyscore(key_count, 0, window_10m_start)
                pipe.zremrangebyscore(key_amount, 0, window_1h_start)

                # 2. Add current transaction
                pipe.zadd(key_count, {txn_id: now})
                # Store amount in member string: "txn_id:amount"
                pipe.zadd(key_amount, {f"{txn_id}:{amount}": now})

                # 3. Set TTLs on keys (2 hours = 7200s)
                pipe.expire(key_count, 7200)
                pipe.expire(key_amount, 7200)

                # 4. Fetch 10-min count and 1-hr members
                pipe.zcard(key_count)
                pipe.zrangebyscore(key_amount, window_1h_start, "+inf")

                results = await pipe.execute()

            txn_count_10m = results[6]
            amount_members_1h = results[7]

            # Calculate total 1-hr spend
            total_amount_1h = 0.0
            for item in amount_members_1h:
                try:
                    amt_str = item.split(":")[-1]
                    total_amount_1h += float(amt_str)
                except (ValueError, IndexError):
                    pass

            metrics = {
                "txn_count_10m": txn_count_10m,
                "total_amount_1h": round(total_amount_1h, 2)
            }

            # Velocity Penalty Calculation (0 to 30 points)
            penalty = 0.0

            if txn_count_10m >= 10:
                penalty += 25.0
                reasons.append("HIGH_VELOCITY_BURST")
            elif txn_count_10m >= 5:
                penalty += 15.0
                reasons.append("HIGH_VELOCITY_BURST")
            elif txn_count_10m >= 3:
                penalty += 5.0

            if total_amount_1h >= 5000.0:
                penalty += 15.0
                reasons.append("HIGH_VOLUME_SPEND")
            elif total_amount_1h >= 2500.0:
                penalty += 10.0
                if "HIGH_VOLUME_SPEND" not in reasons:
                    reasons.append("HIGH_VOLUME_SPEND")

            final_penalty = float(min(30.0, penalty))
            return final_penalty, reasons, metrics

        except Exception as e:
            print(f"[VelocityChecker] Redis connection/operation error: {e}")
            # Fallback when Redis is unavailable
            return 0.0, [], {"error": str(e)}


velocity_checker = VelocityChecker()

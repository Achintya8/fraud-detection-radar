import time
from fastapi import APIRouter, HTTPException, status
from app.config import settings
from app.schemas import ActionEnum, ScoreResponse, TransactionPayload
from app.services.anomaly_detector import anomaly_detector
from app.services.velocity_checker import velocity_checker

router = APIRouter(tags=["Scoring"])


@router.post("/score", response_model=ScoreResponse, status_code=status.HTTP_200_OK)
async def score_transaction(payload: TransactionPayload) -> ScoreResponse:
    start_time = time.perf_counter()

    try:
        # 1. Evaluate base ML anomaly model score
        model_score, model_reasons = anomaly_detector.predict(
            features=payload.features,
            amount=payload.amount
        )

        # 2. Evaluate Redis velocity metrics & penalty
        velocity_score, velocity_reasons, _ = await velocity_checker.check_and_update(
            card_id=payload.card_id,
            txn_id=payload.transaction_id,
            amount=payload.amount,
            timestamp=payload.timestamp
        )

        # 3. Combine scores & cap at 100
        combined_score = int(round(min(100.0, model_score + velocity_score)))

        # Combine distinct reason flags
        all_reasons = list(dict.fromkeys(model_reasons + velocity_reasons))

        # 4. Map final score to action
        if combined_score < settings.ALLOW_THRESHOLD:
            action = ActionEnum.ALLOW
        elif combined_score <= settings.REVIEW_THRESHOLD:
            action = ActionEnum.MANUAL_REVIEW
        else:
            action = ActionEnum.BLOCK

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ScoreResponse(
            transaction_id=payload.transaction_id,
            card_id=payload.card_id,
            risk_score=combined_score,
            action=action,
            reasons=all_reasons,
            model_score=round(model_score, 2),
            velocity_score=round(velocity_score, 2),
            latency_ms=round(elapsed_ms, 2)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scoring transaction: {str(e)}"
        )

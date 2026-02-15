from typing import Dict, Optional


def compute_screenshot_accuracy(
    success: bool,
    duration_ms: Optional[int],
    size: Optional[int],
    attempts: int,
    error: Optional[str] = None,
) -> Dict[str, float]:
    score = 100.0
    if not success:
        score -= 40.0
    if duration_ms is not None:
        if duration_ms > 20000:
            score -= 20.0
        elif duration_ms > 3000:
            score -= min(20.0, (duration_ms - 3000) / 17000 * 20.0)
    if size is not None:
        if size < 5000:
            score -= 25.0
        elif size < 20000:
            score -= 15.0
        elif size < 50000:
            score -= 8.0
    if attempts > 1:
        score -= min(15.0, (attempts - 1) * 5.0)
    if error:
        score -= min(10.0, (len(error) / 50) * 5.0)
    score = max(0.0, min(100.0, score))
    return {"score": round(score, 2)}


def build_screenshot_metrics(
    success: bool,
    duration_ms: Optional[int],
    size: Optional[int],
    attempts: int,
    error: Optional[str] = None,
) -> Dict[str, float]:
    accuracy_info = compute_screenshot_accuracy(
        success=success,
        duration_ms=duration_ms,
        size=size,
        attempts=attempts,
        error=error,
    )
    return {
        "accuracy": accuracy_info["score"],
        "duration_ms": 0 if duration_ms is None else duration_ms,
        "image_size": 0 if size is None else size,
        "attempts": attempts,
    }

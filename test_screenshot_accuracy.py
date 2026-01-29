import unittest
from screenshot_accuracy import compute_screenshot_accuracy, build_screenshot_metrics


class ScreenshotAccuracyTests(unittest.TestCase):
    def test_high_quality_fast_capture_scores_high(self):
        result = compute_screenshot_accuracy(
            success=True,
            duration_ms=1200,
            size=150000,
            attempts=1,
        )
        self.assertGreaterEqual(result["score"], 90.0)

    def test_low_quality_slow_capture_scores_lower(self):
        result = compute_screenshot_accuracy(
            success=True,
            duration_ms=18000,
            size=8000,
            attempts=2,
        )
        self.assertLess(result["score"], 80.0)

    def test_failed_capture_scores_low(self):
        result = compute_screenshot_accuracy(
            success=False,
            duration_ms=10000,
            size=0,
            attempts=3,
            error="Timeout",
        )
        self.assertLess(result["score"], 50.0)

    def test_retry_penalty_applied(self):
        result_one_try = compute_screenshot_accuracy(
            success=True,
            duration_ms=2500,
            size=100000,
            attempts=1,
        )
        result_three_try = compute_screenshot_accuracy(
            success=True,
            duration_ms=2500,
            size=100000,
            attempts=3,
        )
        self.assertLess(result_three_try["score"], result_one_try["score"])

    def test_build_metrics_integration(self):
        metrics = build_screenshot_metrics(
            success=True,
            duration_ms=4200,
            size=90000,
            attempts=1,
        )
        self.assertIn("accuracy", metrics)
        self.assertIn("duration_ms", metrics)
        self.assertIn("image_size", metrics)
        self.assertIn("attempts", metrics)
        self.assertGreater(metrics["accuracy"], 0)


if __name__ == "__main__":
    unittest.main()

"""
Model Drift Detection Engine
Monitors prediction errors over time to detect accuracy deterioration and distribution shift.
(PRD Section 17)
"""
from typing import List, Dict, Any
import numpy as np


class DriftDetector:
    def __init__(self, drift_threshold_ratio: float = 1.35):
        """
        drift_threshold_ratio: If recent window MAE is greater than baseline_mae * drift_threshold_ratio,
        a drift alert is triggered.
        """
        self.drift_threshold_ratio = drift_threshold_ratio

    def evaluate_drift(
        self,
        baseline_mae: float,
        recent_feedbacks: List[Dict[str, Any]],
        window_size: int = 14
    ) -> Dict[str, Any]:
        """
        Calculates recent rolling MAE from feedback records (predicted vs actual)
        and evaluates if drift has occurred.
        """
        if not recent_feedbacks or len(recent_feedbacks) < 5:
            return {
                "drift_detected": False,
                "status": "INSUFFICIENT_DATA",
                "message": "Collecting more recent post-meal feedback records to evaluate drift (minimum 5 required).",
                "baseline_mae": round(baseline_mae, 2),
                "recent_mae": None,
                "sample_count": len(recent_feedbacks),
                "threshold_mae": round(baseline_mae * self.drift_threshold_ratio, 2) if baseline_mae else None,
                "bias": 0.0,
                "recommended_action": "Continue recording actual attendance after meals."
            }

        window_feedbacks = recent_feedbacks[-window_size:]
        errors = [abs(f["predicted_attendance"] - f["actual_attendance"]) for f in window_feedbacks]
        signed_errors = [f["predicted_attendance"] - f["actual_attendance"] for f in window_feedbacks]

        recent_mae = float(np.mean(errors))
        bias = float(np.mean(signed_errors))  # positive = tending to overpredict, negative = underpredict
        threshold_mae = baseline_mae * self.drift_threshold_ratio

        drift_detected = recent_mae > threshold_mae

        if drift_detected:
            status = "DRIFT_ALERT"
            severity = "HIGH" if recent_mae > (baseline_mae * 1.6) else "MODERATE"
            message = (
                f"Model drift detected! Recent error (MAE {round(recent_mae, 1)}) exceeds "
                f"threshold ({round(threshold_mae, 1)}). Attendance patterns have shifted."
            )
            action = "Trigger scheduled or manual model retraining with newly accumulated feedback records."
        else:
            status = "STABLE"
            severity = "NORMAL"
            message = f"Model performance is stable. Recent MAE ({round(recent_mae, 1)}) is within acceptable bounds."
            action = "No action required. Model is operating normally."

        return {
            "drift_detected": drift_detected,
            "status": status,
            "severity": severity,
            "message": message,
            "baseline_mae": round(baseline_mae, 2),
            "recent_mae": round(recent_mae, 2),
            "threshold_mae": round(threshold_mae, 2),
            "bias": round(bias, 2),
            "bias_direction": "OVERPREDICTION" if bias > 0 else "UNDERPREDICTION",
            "sample_count": len(window_feedbacks),
            "recommended_action": action
        }

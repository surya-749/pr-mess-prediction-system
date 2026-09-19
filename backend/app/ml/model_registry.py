"""
Model Registry & Version Management
Handles saving, loading, versioning, and safe promotion of Random Forest models.
(PRD Sections 8, 16)
"""
from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any, List, Tuple
import joblib
from datetime import datetime


REGISTRY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saved_models")
os.makedirs(REGISTRY_DIR, exist_ok=True)

METADATA_FILE = os.path.join(REGISTRY_DIR, "registry_metadata.json")


class ModelRegistry:
    def __init__(self, registry_dir: str = REGISTRY_DIR):
        self.registry_dir = registry_dir
        self.metadata_file = os.path.join(self.registry_dir, "registry_metadata.json")
        self._ensure_metadata()

    def _ensure_metadata(self):
        os.makedirs(self.registry_dir, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            initial_data = {
                "active_version": None,
                "versions": {}
            }
            with open(self.metadata_file, "w") as f:
                json.dump(initial_data, f, indent=2)

    def _read_metadata(self) -> Dict[str, Any]:
        self._ensure_metadata()
        with open(self.metadata_file, "r") as f:
            return json.load(f)

    def _write_metadata(self, data: Dict[str, Any]):
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_next_version_tag(self) -> str:
        metadata = self._read_metadata()
        versions = metadata.get("versions", {})
        if not versions:
            return "RF-v1.0"
        
        # Parse highest minor version number
        indices = []
        for tag in versions.keys():
            try:
                # Expected format: RF-v1.X
                part = tag.replace("RF-v", "").split(".")
                indices.append((int(part[0]), int(part[1])))
            except Exception:
                pass
        
        if not indices:
            return "RF-v1.0"
        indices.sort()
        major, minor = indices[-1]
        return f"RF-v{major}.{minor + 1}"

    def save_model(
        self,
        model: Any,
        version_tag: str,
        metrics: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        feature_importances: List[Dict[str, Any]],
        training_records_count: int,
        make_active: bool = False
    ) -> str:
        metadata = self._read_metadata()
        
        model_filename = f"{version_tag}.joblib"
        model_path = os.path.join(self.registry_dir, model_filename)
        joblib.dump(model, model_path)

        metadata["versions"][version_tag] = {
            "version_tag": version_tag,
            "created_at": datetime.now().isoformat(),
            "model_path": model_path,
            "metrics": metrics,
            "hyperparameters": hyperparameters,
            "feature_importances": feature_importances,
            "training_records_count": training_records_count,
            "is_active": make_active
        }

        if make_active or metadata.get("active_version") is None:
            # Demote previous active
            for v_tag in metadata["versions"]:
                metadata["versions"][v_tag]["is_active"] = (v_tag == version_tag)
            metadata["active_version"] = version_tag

        self._write_metadata(metadata)
        return version_tag

    def load_active_model(self) -> Tuple_Optional:
        metadata = self._read_metadata()
        active_tag = metadata.get("active_version")
        if not active_tag or active_tag not in metadata["versions"]:
            return None, None
        
        version_info = metadata["versions"][active_tag]
        model_path = version_info["model_path"]
        if not os.path.exists(model_path):
            return None, None

        model = joblib.load(model_path)
        return model, version_info

    def load_model_by_version(self, version_tag: str):
        metadata = self._read_metadata()
        if version_tag not in metadata["versions"]:
            return None, None
        version_info = metadata["versions"][version_tag]
        model = joblib.load(version_info["model_path"])
        return model, version_info

    def list_versions(self) -> List[Dict[str, Any]]:
        metadata = self._read_metadata()
        return list(metadata.get("versions", {}).values())

    def promote_version_safely(
        self,
        candidate_model: Any,
        candidate_metrics: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        feature_importances: List[Dict[str, Any]],
        training_records_count: int
    ) -> Dict[str, Any]:
        """
        PRD Section 16 requirement:
        'A poorly performing new model must not automatically replace the current production model.'
        Only promotes if candidate MAE is <= active MAE (or if no active model exists).
        """
        _, active_info = self.load_active_model()
        new_tag = self.get_next_version_tag()

        promote = False
        if active_info is None:
            promote = True
            reason = "Initial baseline model set as active production model."
        else:
            active_mae = active_info.get("metrics", {}).get("mae", float("inf"))
            candidate_mae = candidate_metrics.get("mae", float("inf"))
            if candidate_mae <= active_mae:
                promote = True
                reason = f"Candidate model MAE ({candidate_mae}) improved upon active model MAE ({active_mae})."
            else:
                promote = False
                reason = f"Candidate model MAE ({candidate_mae}) did not outperform active model MAE ({active_mae}). Retained current active model."

        self.save_model(
            model=candidate_model,
            version_tag=new_tag,
            metrics=candidate_metrics,
            hyperparameters=hyperparameters,
            feature_importances=feature_importances,
            training_records_count=training_records_count,
            make_active=promote
        )

        return {
            "version_tag": new_tag,
            "promoted": promote,
            "reason": reason,
            "candidate_metrics": candidate_metrics,
            "active_version": new_tag if promote else active_info.get("version_tag")
        }


# Type alias helper
Tuple_Optional = tuple[Optional[Any], Optional[Dict[str, Any]]]

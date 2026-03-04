import hashlib
import json
from difflib import SequenceMatcher
from typing import Any


class SyntaxAnalyzer:
    """
    Domain service to analyze structural and textual changes in dataset metadata.
    Helps in deciding whether a new AI evaluation is needed.
    """

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """
        Calculates similarity ratio between two strings (0.0 to 100.0).
        Uses difflib.SequenceMatcher.
        """
        if not text1 and not text2:
            return 100.0
        if not text1 or not text2:
            return 0.0
        
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio() * 100.0

    @staticmethod
    def get_structure_hash(data: dict[str, Any]) -> str:
        """
        Generates a SHA-256 hash of the dictionary keys (recursive).
        A change in keys represents a structural change (e.g., new field in ODS).
        """
        def extract_keys(d: Any) -> list[str]:
            keys = []
            if isinstance(d, dict):
                for k, v in sorted(d.items()):
                    keys.append(k)
                    keys.extend(extract_keys(v))
            elif isinstance(d, list):
                for item in d:
                    keys.extend(extract_keys(item))
            return keys

        keys_list = extract_keys(data)
        serialized_keys = json.dumps(keys_list)
        return hashlib.sha256(serialized_keys.encode("utf-8")).hexdigest()

    @classmethod
    def analyze_change(cls, old_raw: dict, new_raw: dict) -> dict[str, float | str]:
        """
        Performs a full analysis of changes between two metadata snapshots.
        """
        old_hash = cls.get_structure_hash(old_raw)
        new_hash = cls.get_structure_hash(new_raw)
        
        # Textual similarity on main fields
        old_title = old_raw.get("title", "") or ""
        new_title = new_raw.get("title", "") or ""
        title_similarity = cls.calculate_text_similarity(old_title, new_title)
        
        old_desc = old_raw.get("description", "") or ""
        new_desc = new_raw.get("description", "") or ""
        desc_similarity = cls.calculate_text_similarity(old_desc, new_desc)
        
        # Global Syntax Score (weighted average)
        # Structure change is heavy: if hash changes, we penalize
        structure_penalty = 0 if old_hash == new_hash else 30
        
        # Score = (TitleSim * 0.4 + DescSim * 0.6) - structure_penalty
        base_score = (title_similarity * 0.4) + (desc_similarity * 0.6)
        syntax_score = max(0, base_score - structure_penalty)
        
        return {
            "syntax_score": round(syntax_score, 2),
            "title_similarity": round(title_similarity, 2),
            "description_similarity": round(desc_similarity, 2),
            "structure_changed": old_hash != new_hash,
            "new_structure_hash": new_hash
        }

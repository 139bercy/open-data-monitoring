import pytest
from domain.datasets.services.syntax_analyzer import SyntaxAnalyzer

def test_calculate_text_similarity():
    # Perfect match
    assert SyntaxAnalyzer.calculate_text_similarity("Hello World", "Hello World") == 100.0
    # No match
    assert SyntaxAnalyzer.calculate_text_similarity("Hello", "World") < 50.0
    # Partial match
    sim = SyntaxAnalyzer.calculate_text_similarity("Open Data", "Opened Data Monitoring")
    assert 50.0 < sim < 100.0
    # Empty strings
    assert SyntaxAnalyzer.calculate_text_similarity("", "") == 100.0
    assert SyntaxAnalyzer.calculate_text_similarity("A", "") == 0.0

def test_get_structure_hash():
    data1 = {"title": "Test", "metas": {"default": {"desc": "v1"}}}
    data2 = {"title": "Test Changed", "metas": {"default": {"desc": "v2"}}}
    data3 = {"title": "Test", "metas": {"default": {"desc": "v1"}, "dcat": {"format": "csv"}}}
    
    hash1 = SyntaxAnalyzer.get_structure_hash(data1)
    hash2 = SyntaxAnalyzer.get_structure_hash(data2)
    hash3 = SyntaxAnalyzer.get_structure_hash(data3)
    
    # Same structure, different values -> same hash
    assert hash1 == hash2
    # Different structure (new key) -> different hash
    assert hash1 != hash3

def test_analyze_change():
    old_raw = {
        "title": "Budget 2023",
        "description": "Données budgétaires pour l'année 2023",
        "metas": {"default": {"lang": "fr"}}
    }
    
    # CASE 1: Minor changes (text only)
    new_raw_minor = {
        "title": "Budget 2023 - Rapport",
        "description": "Données budgétaires pour l'année 2023 (v2)",
        "metas": {"default": {"lang": "fr"}}
    }
    analysis_minor = SyntaxAnalyzer.analyze_change(old_raw, new_raw_minor)
    assert analysis_minor["syntax_score"] > 50.0
    assert analysis_minor["structure_changed"] is False
    
    # CASE 2: Structural change (new metadata field)
    new_raw_struct = {
        "title": "Budget 2023",
        "description": "Données budgétaires pour l'année 2023",
        "metas": {"default": {"lang": "fr"}, "dcat": {"issued": "2023-01-01"}}
    }
    analysis_struct = SyntaxAnalyzer.analyze_change(old_raw, new_raw_struct)
    assert analysis_struct["structure_changed"] is True
    # Syntax score should be lower due to structure penalty
    assert analysis_struct["syntax_score"] < analysis_minor["syntax_score"]

def test_empty_analyze_change():
    # Should not crash on empty/minimal dicts
    analysis = SyntaxAnalyzer.analyze_change({}, {"title": "New"})
    assert "syntax_score" in analysis
    assert analysis["structure_changed"] is True

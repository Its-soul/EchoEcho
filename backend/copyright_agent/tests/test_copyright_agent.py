from copyright_agent.agents.phrase_bag_agent import PhraseBagAgent
from copyright_agent.agents.repetition_agent import RepetitionAgent
from copyright_agent.agents.similarity_agent import SimilarityAgent
from copyright_agent.main import check_copyright
from copyright_agent.models.request_model import CopyrightCheckRequest
from copyright_agent.services.preprocessing import preprocess_lyrics


def test_preprocessing_lowercases_removes_punctuation_and_tokenizes():
    result = preprocess_lyrics("Hello,   WORLD!\nAgain.")

    assert result.cleaned == "hello world again"
    assert result.tokens == ["hello", "world", "again"]


def test_phrase_bag_agent_matches_known_phrase():
    result = PhraseBagAgent().run("A small song says happy birthday to you tonight")

    assert result == {"matched": True, "phrase": "happy birthday to you"}


def test_repetition_agent_flags_repeated_words():
    result = RepetitionAgent(threshold=0.25).run("love love love love tonight")

    assert result["is_repetitive"] is True
    assert result["repetition_score"] >= 0.25


def test_similarity_agent_returns_top_matches():
    import pytest

    pytest.importorskip("rapidfuzz")

    result = SimilarityAgent(top_k=5).run("jingle bells jingle bells jingle all the way")

    assert len(result["matches"]) <= 5
    assert result["matches"][0]["title"] == "Jingle Bells"
    assert result["matches"][0]["score"] >= 80


def test_pipeline_executes_all_stages_without_external_services():
    response = check_copyright(
        CopyrightCheckRequest(
            lyrics="twinkle twinkle little star how I wonder what you are",
            debug=True,
        )
    )

    assert response.risk in {"None", "Low", "Medium", "High"}
    assert response.developer_details is not None
    assert "phrase_bag" in response.developer_details
    assert "repetition" in response.developer_details
    assert "similarity" in response.developer_details
    assert "vector_search" in response.developer_details
    assert "llm_judge" in response.developer_details

from typing import Any

from fastapi import FastAPI

from .agents.generic_phrase_agent import GenericPhraseAgent
from .agents.llm_judge_agent import LLMJudgeAgent
from .agents.phrase_bag_agent import PhraseBagAgent
from .agents.public_domain_agent import PUBLIC_DOMAIN_SONGS, PublicDomainAgent
from .agents.repetition_agent import RepetitionAgent
from .agents.similarity_agent import SimilarityAgent
from .agents.vector_search_agent import VectorSearchAgent
from .models.request_model import CopyrightCheckRequest
from .models.response_model import CopyrightCheckResponse
from .services.preprocessing import preprocess_lyrics
from .utils.similarity_utils import highest_similarity_score, strongest_match


app = FastAPI(title="Copyright Agent", version="1.0.0")

PUBLIC_DOMAIN_TITLES = {title.lower() for title in PUBLIC_DOMAIN_SONGS}


def _normalise_llm_risk(llm_result: dict[str, Any]) -> str:
    raw_risk = str(
        llm_result.get("copyright_risk")
        or llm_result.get("risk")
        or llm_result.get("risk_level")
        or "unknown"
    ).lower()
    if "high" in raw_risk:
        return "High"
    if "suspicious" in raw_risk or "medium" in raw_risk or "moderate" in raw_risk:
        return "Medium"
    if "low" in raw_risk:
        return "Low"
    return "Unknown"


def _is_public_domain_title(title: str) -> bool:
    return title.lower() in PUBLIC_DOMAIN_TITLES


def _aggregate_risk(
    phrase_result: dict,
    generic_result: dict,
    public_domain_result: dict,
    repetition_result: dict,
    similarity_result: dict,
    vector_result: dict,
    llm_result: dict,
    top_match: dict,
) -> str:
    local_score = highest_similarity_score(similarity_result.get("matches", []))
    vector_score = highest_similarity_score(vector_result.get("matches", []))
    llm_risk = _normalise_llm_risk(llm_result)
    top_match_title = str(top_match.get("title", ""))
    is_public_domain = bool(public_domain_result.get("is_public_domain")) or (
        top_match_title and _is_public_domain_title(top_match_title)
    )
    is_generic = bool(generic_result.get("is_generic"))
    protected_phrase = bool(phrase_result.get("matched")) and not (
        is_generic or is_public_domain
    )

    if is_generic or is_public_domain:
        return "None"
    if protected_phrase and (local_score >= 80 or llm_risk == "High"):
        return "High"
    if top_match_title and not is_public_domain and local_score >= 95:
        return "High"
    if vector_score >= 0.90 or llm_risk == "High":
        return "High"
    if vector_score >= 0.80 or llm_risk == "Medium":
        return "Medium"
    if local_score >= 80 and top_match_title and not is_public_domain:
        return "Medium"
    if repetition_result.get("is_repetitive") or local_score >= 60 or vector_score >= 0.70:
        return "Low"
    return "None"


def _copyright_status(
    risk: str,
    generic_result: dict,
    public_domain_result: dict,
    top_match: dict,
) -> str:
    top_match_title = str(top_match.get("title", ""))
    if public_domain_result.get("is_public_domain") or _is_public_domain_title(
        top_match_title
    ):
        return "Public Domain"
    if generic_result.get("is_generic"):
        return "Common Phrase"
    if risk in {"Medium", "High"}:
        return "Protected"
    if risk == "None":
        return "No Concern"
    return "Low"


def _recommendation_for_risk(risk: str, copyright_status: str, llm_result: dict) -> str:
    llm_recommendation = llm_result.get("recommendation")
    if (
        risk in {"Medium", "High"}
        and "error" not in llm_result
        and isinstance(llm_recommendation, str)
        and llm_recommendation.strip()
    ):
        return llm_recommendation

    if copyright_status in {"Public Domain", "Common Phrase"} or risk == "None":
        return "Safe to use."
    recommendations = {
        "High": "Potential copyright infringement.",
        "Medium": "Review and revise similar sections before release.",
        "Low": "Low copyright concern based on available lyric checks.",
    }
    return recommendations.get(risk, "Review results manually.")


def _details_for_verdict(
    risk: str,
    copyright_status: str,
    generic_result: dict,
    public_domain_result: dict,
) -> str:
    if copyright_status == "Public Domain":
        return "Similarity comes from common public-domain expressions."
    if copyright_status == "Common Phrase":
        return "Lyrics contain common generic expressions that do not create a copyright concern."
    if risk == "High":
        return "Lyrics are nearly identical to an existing copyrighted song."
    if risk == "Medium":
        return "Lyrics have meaningful similarity signals and should be reviewed before release."
    if risk == "Low":
        return "Only weak similarity or repetition signals were found."
    if generic_result.get("is_generic") or public_domain_result.get("is_public_domain"):
        return "No copyright concern. Similarity is due to common or public-domain phrases."
    return "No meaningful copyright similarity signals were found."


def _pick_top_match(similarity_result: dict, vector_result: dict, llm_result: dict) -> dict:
    local_match = strongest_match(similarity_result.get("matches", []))
    vector_match = strongest_match(vector_result.get("matches", []))
    llm_title = llm_result.get("similar_song") or llm_result.get("song")
    llm_artist = llm_result.get("artist") or ""

    candidates = [match for match in [local_match, vector_match] if match]
    if candidates:
        return max(candidates, key=lambda match: float(match.get("score", 0.0)))
    if llm_title:
        return {"title": str(llm_title), "artist": str(llm_artist), "score": 0.0}
    return {"title": "", "artist": "", "score": 0.0}


@app.post(
    "/check-copyright",
    response_model=CopyrightCheckResponse,
    response_model_exclude_none=True,
)
def check_copyright(request: CopyrightCheckRequest) -> CopyrightCheckResponse:
    preprocessed = preprocess_lyrics(request.lyrics)

    phrase_result = PhraseBagAgent().run(preprocessed)
    generic_result = GenericPhraseAgent().run(preprocessed)
    public_domain_result = PublicDomainAgent().run(preprocessed)
    repetition_result = RepetitionAgent().run(preprocessed)
    similarity_result = SimilarityAgent().run(preprocessed)
    vector_result = VectorSearchAgent().run(preprocessed.cleaned)

    retrieved_songs = similarity_result.get("matches", []) + vector_result.get("matches", [])
    llm_result = LLMJudgeAgent().run(request.lyrics, retrieved_songs)

    top_match = _pick_top_match(similarity_result, vector_result, llm_result)
    risk = _aggregate_risk(
        phrase_result,
        generic_result,
        public_domain_result,
        repetition_result,
        similarity_result,
        vector_result,
        llm_result,
        top_match,
    )
    copyright_status = _copyright_status(
        risk,
        generic_result,
        public_domain_result,
        top_match,
    )
    recommendation = _recommendation_for_risk(risk, copyright_status, llm_result)
    details = _details_for_verdict(
        risk,
        copyright_status,
        generic_result,
        public_domain_result,
    )

    developer_details = None
    if request.debug:
        developer_details = {
            "preprocessing": {
                "cleaned": preprocessed.cleaned,
                "tokens": preprocessed.tokens,
            },
            "phrase_bag": phrase_result,
            "generic_phrase": generic_result,
            "public_domain": public_domain_result,
            "repetition": repetition_result,
            "similarity": similarity_result,
            "vector_search": vector_result,
            "llm_judge": llm_result,
        }

    return CopyrightCheckResponse(
        safe=risk in {"None", "Low"},
        risk=risk,
        copyright_status=copyright_status,
        top_match=top_match.get("title", ""),
        artist=top_match.get("artist", ""),
        similarity_score=round(float(top_match.get("score", 0.0)), 4),
        recommendation=recommendation,
        details=details,
        developer_details=developer_details,
    )


# Future integration note:
# Mount this app or include its route from the existing backend when ready, for example:
# from copyright_agent.main import app as copyright_agent_app
# parent_app.mount("/copyright", copyright_agent_app)

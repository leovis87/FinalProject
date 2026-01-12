from pydantic import BaseModel, field_validator

class TopicReq(BaseModel):
    user_query: str
    level: str
    subject: str
    diff_min: int = 1
    diff_max: int = 5
    allow_sensitive: bool = False
    top_k: int = 8
    n_topics: int = 5
    min_score: float = 0.55
    candidate_k: int = 80
    model_name: str | None = None

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        lowered = value.strip().lower()
        if lowered == "" or lowered == "string":
            return None
        return value

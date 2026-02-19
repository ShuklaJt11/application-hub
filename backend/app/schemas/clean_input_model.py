from pydantic import BaseModel, ConfigDict


class CleanInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

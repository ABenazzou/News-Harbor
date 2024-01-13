from typing import Optional
from pydantic import BaseModel


class SearchQuery(BaseModel):
    full_text_search: Optional[str] = None
from typing import List
from pydantic import BaseModel
from models import Article


class ArticleCollection(BaseModel):
    """
    A container holding a list of `Article` instances.
    """
    
    total: int
    articles: List[Article]
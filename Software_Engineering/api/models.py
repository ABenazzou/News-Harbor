from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class SearchQuery(BaseModel):
    full_text_search: Optional[str] = None
    
    
class Article(BaseModel):
    id: str
    uri: str 
    title: str 
    subtitle: Optional[str]
    authors: Optional[List[str]] 
    category: str 
    subcategory: Optional[str]
    date_posted: datetime 
    full_text: str 
    images: Optional[List[str]]
    topics: Optional[List[str]] 
    
    class Config:
        json_schema_extra = {
            "example": {
                "uri": "https://www.bbc.co.uk/news/example",
                "title": "Example title",
                "subtitle": "Example subtitle",
                "authors": ["Author 1", "Author 2"],
                "category": "Example Category",
                "subcategory": "Example SubCategory",
                "date_posted": "2024-01-13",
                "full_text": "Example fulltext",
                "images": ["example.com/images/resource.jpg"],
                "topics": ["Example Topic"],
            }
        }
    
    

class ArticleCollection(BaseModel):
    """
    A container holding a list of `Article` instances.
    """
    
    total: int
    articles: List[Article]
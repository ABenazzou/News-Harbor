from fastapi import APIRouter, Request, Query, Body, HTTPException
from typing import Optional, List
from models import SearchQuery

router = APIRouter()


@router.post("/authors", response_description="List all unique authors options narrowed down by queries")
async def list_authors(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    categories: List[str] = Query(None),
                    subcategories: List[str] = Query(None),
                    topics: List[str] = Query(None),
                    ):
    
    query = {}

    if categories: query["category"] = {"$in": categories}
    
    if subcategories: query["subcategory"] = {"$in": subcategories}
    
    if topics: query["topics"] = {"$in": topics}
    
    pipeline = []
    
    if search_query and search_query.full_text_search:
        pipeline.append({"$search": f'\"{search_query.full_text_search}\"'})
    
    steps = [
        {
            "$match": query
        },
        {
            "$unwind": "$authors"
        },
        {
            "$group": {
                "_id": 0,
                "authors": {"$addToSet": "$authors"}
            }
        },
        {
            '$project': {
                '_id': 0,
                'authors': 1
            }
        }
    ]
    
    for step in steps: pipeline.append(step)
           
    try:
        authors = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return authors[0] if authors else []

from fastapi import APIRouter, Request, Query, Body, HTTPException
from typing import Optional, List
from models import SearchQuery

router = APIRouter()


@router.post("/categories", response_description="List all unique categories options narrowed down by queries")
async def list_categories(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    topics: List[str] = Query(None),
                    subcategories: List[str] = Query(None),
                    authors: List[str] = Query(None),
                    ):
    
    query = {}

    if topics: query["topics"] = {"$in": topics}
    
    if subcategories: query["subcategory"] = {"$in": subcategories}
    
    if authors: query["authors"] = {"$in": authors}
    
    pipeline = []
    
    if search_query and search_query.full_text_search:
        pipeline.append({"$search": f'\"{search_query.full_text_search}\"'})
    
    steps = [
        {
            "$match": query
        },
        {
            "$group": {
                "_id": 0,
                "category": {"$addToSet": "$category"}
            }
        },
        {
            '$project': {
                '_id': 0,
                'category': 1
            }
        }
    ]
    
    for step in steps: pipeline.append(step)
           
    try:
        categories = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return categories[0] if categories else []
from fastapi import APIRouter, Request, Query, Body, HTTPException
from typing import Optional, List
from models import SearchQuery

router = APIRouter()


@router.post("/subcategories", response_description="List all unique subcategories options narrowed down by queries")
async def list_subcategories(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    categories: List[str] = Query(None),
                    topics: List[str] = Query(None),
                    authors: List[str] = Query(None),
                    ):
    
    query = {}

    if categories: query["category"] = {"$in": categories}
    
    if topics: query["topics"] = {"$in": topics}
    
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
                "topics": {"$addToSet": "$topics"}
            }
        },
        {
            '$project': {
                '_id': 0,
                'subcategory': 1
            }
        }
    ]
    
    for step in steps: pipeline.append(step)
           
    try:
        subcategories = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return subcategories[0] if subcategories else []

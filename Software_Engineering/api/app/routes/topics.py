from fastapi import APIRouter, Request, Query, Body, HTTPException
from typing import Optional, List
from models import SearchQuery

router = APIRouter()


@router.post("/topics", response_description="List all unique topic options narrowed down by queries")
async def list_topics(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    categories: List[str] = Query(None),
                    subcategories: List[str] = Query(None),
                    authors: List[str] = Query(None),
                    ):
    
    query = {}

    if categories: query["category"] = {"$in": categories}
    
    if subcategories: query["subcategory"] = {"$in": subcategories}
    
    if authors: query["authors"] = {"$in": authors}
    
    if search_query and search_query.full_text_search:
        query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}
    
    pipeline = [
        {
            "$match": query
        },
        {
            "$unwind": "$topics"
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
                'topics': 1
            }
        }
    ]
    
    try:
        topics = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    if topics[0]:
        topics[0]["topics"].sort()
        return topics[0]
    
    return {"topics": []}

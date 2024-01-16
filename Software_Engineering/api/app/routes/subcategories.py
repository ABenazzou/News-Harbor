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
    
    if search_query and search_query.full_text_search:
        query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}
    
    pipeline = [
        {
            "$match": query
        },
        {
            "$group": {
                "_id": 0,
                "subcategory": {"$addToSet": "$subcategory"}
            }
        },
        {
            '$project': {
                '_id': 0,
                'subcategory': 1
            }
        }
    ]
    
    try:
        subcategories = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    if subcategories:
        subcategories[0]["subcategory"].sort()
        return subcategories[0]
    
    return {"subcategory": []}


@router.post("/subcategories/frequency", response_description="List the frequency of the top 10 subcategories options narrowed down by queries")
async def list_subcategories_frequency(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    categories: List[str] = Query(None),
                    topics: List[str] = Query(None),
                    authors: List[str] = Query(None),
                    ):
    
    query = {}

    if categories: query["category"] = {"$in": categories}
    
    if topics: query["topics"] = {"$in": topics}
    
    if authors: query["authors"] = {"$in": authors}
    
    if search_query and search_query.full_text_search:
        query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}
    
    pipeline = [
        {
            "$match": query
        },
        {
            "$group": {
                "_id": "$subcategory",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
        "$project": {
            "subcategory": "$_id",
            "_id": 0,  # exclude the grouping _id
            "count": 1
        }
    }
    ]
    
    try:
        subcategories = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(10)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return subcategories
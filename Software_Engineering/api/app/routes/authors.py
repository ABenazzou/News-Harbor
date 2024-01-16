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
    
    if search_query and search_query.full_text_search:
        query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}
    
    pipeline = [
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
           
    try:
        authors = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    if authors:
        authors[0]["authors"].sort()
        return authors[0]
    
    return {"authors": []}


@router.post("/authors/frequency", response_description="List the frequency of the top 10 authors options narrowed down by queries")
async def list_authors_frequency(request: Request,
                    search_query: Optional[SearchQuery] = Body(default=None),
                    categories: List[str] = Query(None),
                    subcategories: List[str] = Query(None),
                    topics: List[str] = Query(None),
                    ):
    
    query = {}

    if categories: query["category"] = {"$in": categories}
    
    if subcategories: query["subcategory"] = {"$in": subcategories}
    
    if topics: query["topics"] = {"$in": topics}
    
    if search_query and search_query.full_text_search:
        query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}
    
    pipeline = [
        {
            "$match": query
        },
        {
            "$unwind": "$authors"
        },
        {
            "$group": {
                "_id": "$authors",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
        "$project": {
            "author": "$_id",
            "_id": 0,  # exclude the grouping _id
            "count": 1
        }
    }
    ]
           
    try:
        authors = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(10)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return authors
   
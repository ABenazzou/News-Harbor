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

    if topics:
        topics[0]["topics"].sort()
        return topics[0]
    
    return {"topics": []}


@router.post("/topics/frequency", response_description="Lists the frequency of the top 10 topics options narrowed down by queries")
async def list_topics_frequency(request: Request,
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
                "_id": "$topics",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
        "$project": {
            "topic": "$_id",
            "_id": 0,  # exclude the grouping _id
            "count": 1
        }
    }
    ]
    
    try:
        topics = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(10)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return topics


@router.post("/topics/trends", response_description="Lists the trends of the top 10 topics options narrowed down by queries")
async def list_topics_trends(request: Request,
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
    
    
    topics_pipeline = [
        {
            "$match": query
        },
        {
            "$unwind": "$topics"
        },
        {
            "$group": {
                "_id": "$topics",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$project": {
                "topic": "$_id",
                "_id": 0,  # exclude the grouping _id
                "count": 1
            }
        }
    ]
    
    top_10_topics = await request.app.database["bbc-articles"].aggregate(topics_pipeline).to_list(10)
    top_10_topics = [topic["topic"] for topic in top_10_topics]
        
    pipeline = [
        {
            "$unwind": "$topics"
        },
        {
            "$match": {
                "topics": {"$in": top_10_topics}
            }
        },
        {
            '$group': {
                '_id': {
                    'month': {'$month': '$date_posted'},
                    'year': {'$year': '$date_posted'},
                    'topic': '$topics'
                },
                'count': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': {
                    'month': '$_id.month',
                    'year': '$_id.year'
                },
                'topics': {
                    '$push': {
                        'topic': '$_id.topic',
                        'count': '$count'
                    }
                }
            }
        },
        {
            '$project': {
                '_id': 0,
                'date': {
                    '$dateToString': {
                        'format': '%Y-%m',
                        'date': {
                            '$dateFromParts': {
                                'year': '$_id.year',
                                'month': '$_id.month'
                            }
                        }
                    }
                },
                'topics': 1
            }
        },
        {
            '$sort': {'date': 1}
        }
    ]

    
    try:
        topics_trends = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return topics_trends

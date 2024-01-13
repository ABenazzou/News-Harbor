from fastapi import APIRouter, Request, Query, Body, HTTPException
from models import ArticleCollection, Article, SearchQuery
from typing import Optional
from bson import ObjectId
from datetime import datetime, date

router = APIRouter()


@router.post("/articles",
            response_description="List limit articles starting from given offset. If a sort key is not provided, articles will be sorted by latest article date. If categories or subcategories are specified, filtering will be applied",
            response_model=ArticleCollection)
async def list_articles(request: Request,
                        search_query: Optional[SearchQuery] = Body(default=None),
                        skip: int = Query(0, alias="offset"),
                        limit: int = Query(10, alias="limit"),
                        sort_by: str = Query("date_posted"),
                        sort_order: str = Query("desc"),
                        category: str = Query(None),
                        subcategory: str = Query(None),
                        author: str = Query(None),
                        topic: str = Query(None),
                        date_posted: date = Query(None),
                        ):
    
    if limit < 1 or skip < 0:
        raise HTTPException(status_code=400, detail="Invalid 'limit' or 'offset' values")
    
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid 'sort_order' value")
    
    sort_order = 1 if sort_order == "asc" else -1
    query = {}
    
    if category: query["category"] = category
    
    if subcategory: query["subcategory"] = subcategory
    
    if author: query["authors"] = author
    
    if topic: query["topics"] = topic
    
    if date_posted: query["date_posted"] = datetime.combine(date_posted, datetime.min.time())
    
    if search_query and search_query.full_text_search: query["$text"] = {"$search": f'\"{search_query.full_text_search}\"'}  
    
    articles = []
    try:
        total = await request.app.database["bbc-articles"].count_documents(query)
        docs = await request.app.database["bbc-articles"].find(query).sort([
                (sort_by, sort_order), 
                ("_id", 1)  # Secondary sort by _id in ascending order
            ]).skip(skip).limit(limit).to_list(length=limit)
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    for doc in docs:
        article = Article(
            id = str(doc["_id"]),
            uri = doc["uri"],
            title = doc["title"],
            subtitle = doc["subtitle"] if "subtitle" in doc else None,
            authors = doc["authors"] if "authors" in doc else None,
            category = doc["category"],
            subcategory = doc["subcategory"] if "subcategory" in doc else None,
            date_posted = doc["date_posted"],
            full_text = doc["full_text"],
            images = doc["images"] if "images" in doc else None,
            topics = doc["topics"] if "topics" in doc else None,
        )
        articles.append(article)
        
    return ArticleCollection(articles=articles, total=total)


@router.get("/categories", response_description="List all unique categories and their subcategories")
async def list_categories(request: Request):
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "subcategories": {
                    "$addToSet": "$subcategory"  # getting unique subcategoriesi in a set
                }
            }
        },
        {
            "$project": {
                "category": "$_id", # set id from group pipeline stage to category
                "subcategories": 1, # include subcats only
                "_id": 0
            }
        }
    ]

    try:
        categories = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
        categories.sort(key=lambda x: x["category"])
    
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return categories


@router.get("/articles/{id}", response_description="Get a single article by ID", response_model=Article)
async def find_article_by_id(request: Request, id: str):
    
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail=f"Invalid ID: {id}")

    try:
        doc = await request.app.database["bbc-articles"].find_one({"_id": ObjectId(id)})

    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    if doc is None:
        raise HTTPException(status_code=404, detail=f"Article with ID {id} not found")

    article = Article(
            id = str(doc["_id"]),
            uri = doc["uri"],
            title = doc["title"],
            subtitle = doc["subtitle"] if "subtitle" in doc else None,
            authors = doc["authors"] if "authors" in doc else None,
            category = doc["category"],
            subcategory = doc["subcategory"] if "subcategory" in doc else None,
            date_posted = doc["date_posted"],
            full_text = doc["full_text"],
            images = doc["images"] if "images" in doc else None,
            topics = doc["topics"] if "topics" in doc else None,
        )
    return article
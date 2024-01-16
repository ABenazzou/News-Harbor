from fastapi import APIRouter, Request, Query, Body, HTTPException
from typing import Optional, List
from models import SearchQuery
from itertools import combinations

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


@router.get("/authors/network", response_description="Return the network data layer with the authors, their degrees and the combinations of collaborations")
async def get_authors_network(request: Request):
    
    authors_arrays_query = {
        "authors.1": {
            "$exists": True
        }
    }

    project = {
        'authors': 1, 
        '_id': 0
    }
    
    authors_unique_combinations = set()
    
    
    links = []
    author_count = {} # count degrees
        
    try:
        authors_arrays = await request.app.database["bbc-articles"].find(filter=authors_arrays_query, projection=project).to_list(None)
        
        for array in authors_arrays:
            author_group = array["authors"]
            authors_combinations = list(combinations(author_group, 2))
            for duo in authors_combinations:
                authors_unique_combinations.add(tuple(sorted(duo)))
                
        for author_duo in authors_unique_combinations:
            author_count[author_duo[0]] = author_count.get(author_duo[0], 0) + 1
            author_count[author_duo[1]] = author_count.get(author_duo[1], 0) + 1
            
            links.append({
                "source": author_duo[0],
                "target": author_duo[1]
            })

        sorted_authors = sorted(author_count.items(), key=lambda record: record[1], reverse=True)
        
        pipeline = [
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
           
        top_authors = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(10)
        top_10_frequent_authors = [author["author"] for author in top_authors] # count & author dict here
        
        nodes = []
        count_so_far = 1
        
        for author, degree in sorted_authors:
            
            group = "irrelevant authors"
            
            if author in top_10_frequent_authors and count_so_far < 11:
                group = "top authors" # big degrees and big articles number
                
            elif count_so_far < 11:
                group = "collaborative authors" # big degrees
            
            elif author in top_10_frequent_authors:
                group = "consistent authors" # big articles number
            
            if count_so_far < 11:
                count_so_far += 1
            
            nodes.append({
                "id": author,
                "degree": degree,
                "group": group
            })
        network_data = {"nodes": nodes, "links": links}
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return network_data
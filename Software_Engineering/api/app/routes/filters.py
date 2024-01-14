from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/filters", response_description="List all unique filters options")
async def list_filters(request: Request):
    pipeline = [
        {
            "$group": {
                "_id": None,
                "categories": {"$addToSet": "$category"},
                "subcategories": {"$addToSet": "$subcategory"},
                "topics": {"$addToSet": "$topics"},
                "authors": {"$addToSet": "$authors"}
            }
        },
        {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "categories": 1,
                "subcategories": 1,
                "topics": 1,
                "authors": 1
            }
        }
    ]
   
    try:
        filters = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return filters[0]

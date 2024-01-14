from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/filters", response_description="List all unique filters options")
async def list_filters(request: Request):
    pipeline = [
        {
            "$unwind": "$topics"
        },
        {
            "$group": {
                "_id": None,
                "uniqueCategories": {"$addToSet": "$category"},
                "uniqueSubcategories": {"$addToSet": "$subcategory"},
                "uniqueTopics": {"$addToSet": "$topics"},
            }
        },
        {
            "$unwind": "$authors"
        },
        {
            "$group": {
                "_id": None,
                "uniqueCategories": {"$first": "$uniqueCategories"},
                "uniqueSubcategories": {"$first": "$uniqueSubcategories"},
                "uniqueTopics": {"$first": "$uniqueTopics"},
                "uniqueAuthors": {"$addToSet": "$authors"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "categories": "$uniqueCategories",
                "subcategories": "$uniqueSubcategories",
                "topics": "$uniqueTopics",
                "authors": "$uniqueAuthors"
            }
        }
    ]
   
    try:
        filters = await request.app.database["bbc-articles"].aggregate(pipeline).to_list(None)
        
    except Exception as e:
        print(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the request")

    return filters[0]

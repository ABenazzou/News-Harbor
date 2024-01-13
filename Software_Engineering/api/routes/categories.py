from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    is_offer: bool | None = None

app = FastAPI()
items = []
names = set()

@app.get("/")
def read_root():
    return {"Hola": "Mundo"}

@app.post("/items/")
def create_item(item: Item):
    item.name = item.name.lower()
    if "spam" in item.name:
        raise HTTPException(status_code=403, detail="Spam")
    if item.name in names:
        raise HTTPException(status_code=409, detail="item already exists")
    # In a real app, you would save this item to a database
    items.append(item)
    names.add(item.name)
    print(f"Received item: {item.name}")
    return {"item_name": item.name, "item_price": item.price}

@app.get("/items/{item_name}")
def read_item(item_name: str, q: str | None = None):
    # 'q' is an optional query parameter
    for item in items:
        if item_name == item.name:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/admin/")
def access_admin():
    raise HTTPException(status_code=401, detail="No admin privileges")

@app.get("/oldresource/")
def read_old_resource():
    raise HTTPException(status_code=410, detail="Resource no longer exists")

@app.get("/illegal/")
def open_illegal():
    raise HTTPException(status_code=451, detail="Content unavailable in your region")
from fastapi import FastAPI
# from pydantic import BaseModel

# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     is_offer: bool | None = None

app = FastAPI()
# items = []

@app.get("/")
def read_root():
    return {"Hola": "Mundo"}

# # 3. Define a POST endpoint to create an item
# @app.post("/items/")
# def create_item(item: Item):
#     # In a real app, you would save this item to a database
#     items.append(item)
#     print(f"Received item: {item.name}")
#     return {"item_name": item.name, "item_price": item.price}
#
# # 4. Define a GET endpoint with a path parameter
# @app.get("/items/{item_name}")
# def read_item(item_name: str, q: str | None = None):
#     # 'q' is an optional query parameter
#     for item in items:
#         if item_name == item.name:
#             return item
#     return "Item not found"

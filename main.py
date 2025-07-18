from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory=".")

orders: List["Order"] = []
stock: Dict[str, int] = {"Meal": 0, "Chai": 0, "Snack": 0}  # Default stock

class Order(BaseModel):
    student_name: str
    roll_number: str
    item: str
    quantity: int
    timestamp: datetime = Field(default_factory=datetime.now)
    paid: bool = False
    eta_minutes: float = 0  # Calculated and added during placing order

@app.get("/", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("student_order.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/place-order")
def place_order(order: Order):
    # Validate stock
    if order.item not in stock or stock[order.item] < order.quantity:
        raise HTTPException(status_code=400, detail=f"Not enough {order.item} in stock")

    # Reduce stock
    stock[order.item] -= order.quantity

    # Calculate ETA based on pending orders
    eta = 0
    for o in orders:
        if not o.paid:
            if o.item == "Meal":
                eta += 1.5 * o.quantity
            elif o.item == "Chai":
                eta += 0.5 * o.quantity
            elif o.item == "Snack":
                eta += 1.0 * o.quantity
    order.eta_minutes = round(eta, 1)

    orders.append(order)
    return {"message": "Order placed", "eta_minutes": order.eta_minutes, "remaining_stock": stock, "order": order}

@app.get("/get-orders")
def get_orders():
    return orders

@app.post("/mark-paid/{index}")
def mark_order_paid(index: int):
    if 0 <= index < len(orders):
        orders[index].paid = True
        return {"message": "Marked as paid"}
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/set-stock")
def set_stock(new_stock: Dict[str, int]):
    for item in ["Meal", "Chai", "Snack"]:
        if item in new_stock:
            stock[item] = new_stock[item]
    return {"message": "Stock updated", "stock": stock}

@app.get("/get-stock")
def get_stock():
    return stock
@app.get("/get-estimated-wait/{roll_number}")
def get_estimated_wait(roll_number: str):
    unpaid_orders_before = 0
    for order in orders:
        if order.roll_number == roll_number:
            break
        if not order.paid:
            unpaid_orders_before += 1

    wait_minutes = unpaid_orders_before * 2  # 🕐 Assume 2 mins per order
    return {"wait_minutes": wait_minutes}


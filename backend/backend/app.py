from fastapi import FastAPI, Request
import stripe
import os

app = FastAPI()


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    email = data.get("email")

    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            line_items=[{
                "price": "price_1SXzBsD9hkGY8XoHD5yLibWP",
                "quantity": 1
            }],
            mode="subscription",
            success_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?success=true",
            cancel_url="https://vida-secure-ai-7enddksqy2c8zpeeudblth.streamlit.app/?cancel=true"
        )
        return {"url": session.url}
    except Exception as e:
        return {"error": str(e)}

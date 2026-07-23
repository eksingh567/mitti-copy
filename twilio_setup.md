# 📞 Twilio Setup Guide for Mitti

This guide explains how to set up Twilio Voice calling for the Mitti soil intelligence project to call the farmer and speak the advisory messages in Hindi using Amazon Polly.

---

## Step 1: Create a Twilio Account
1. Go to [Twilio](https://www.twilio.com) and sign up for a free trial account (or log in if you already have one).
2. Go to the Twilio Console Dashboard.

## Step 2: Get a Twilio Phone Number
1. On your Twilio Console home page, click **Get a trial phone number** (or purchase a number if using a paid account).
2. Copy this phone number (it will look like `+1XXXXXXXXXX` or similar).

## Step 3: Find Credentials
In your Twilio Console home page under **Account Info**, copy:
- **Account SID**: Unique identifier for your account (starts with `AC...`)
- **Auth Token**: Security credential token

## Step 4: Verify Caller ID (For Free Accounts)
Because you are on a Twilio trial/free account, you can only make calls to **verified phone numbers**.
1. In the console sidebar, go to **Phone Numbers** > **Manage** > **Verified Caller IDs**.
2. Click **Add a new caller ID** and add the farmer's phone number (e.g., `+91XXXXXXXXXX`).
3. Verify it using the SMS verification code sent to that phone.

## Step 5: Update Backend Configuration
Open `C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\app.py` and update the config block at the top:

```python
# ─── Twilio Config ────────────────────────────────────
TWILIO_SID   = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Your Account SID
TWILIO_TOKEN = "your_auth_token_here"               # Your Auth Token
TWILIO_FROM  = "+1XXXXXXXXXX"                       # Your Twilio phone number
FARMER_PHONE = "+91XXXXXXXXXX"                      # The verified farmer's phone number
```

---

## Testing the Voice Call
1. Start the backend: `python app.py`
2. Go to `http://localhost:5000`
3. Click the green **📞 Call Farmer Now** button.
4. Your phone should ring, and you will hear **Aditi** (a premium Amazon Polly Hindi text-to-speech voice) speak the advisory message in clear Hindi!

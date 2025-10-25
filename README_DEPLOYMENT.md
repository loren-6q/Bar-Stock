# Free Deployment Guide - Bar Stock Management

Deploy your bar stock management app completely FREE using:
- **Frontend**: Vercel (free)
- **Backend**: Render (free tier)
- **Database**: MongoDB Atlas (free tier)

## Quick Setup Steps:

### 1. MongoDB Atlas (Free Database)
1. Go to https://cloud.mongodb.com/
2. Create free account
3. Create free cluster (M0 Sandbox - 512MB)
4. Create database user
5. Get connection string

### 2. Render Backend (Free API)
1. Go to https://render.com/
2. Connect your GitHub account
3. Create new "Web Service"
4. Connect to your backend repository
5. Use these settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Add Environment Variable**: `MONGO_URL=your_mongodb_atlas_connection_string`

### 3. Vercel Frontend (Free Static Hosting)
1. Go to https://vercel.com/
2. Import your frontend repository
3. Add environment variable: `REACT_APP_BACKEND_URL=your_render_backend_url`
4. Deploy automatically

## File Structure for Free Deployment:
```
├── backend/               # Deploy to Render
│   ├── server.py
│   ├── requirements.txt
│   └── .env
├── frontend/              # Deploy to Vercel
│   ├── src/
│   ├── package.json
│   └── .env
└── README_DEPLOYMENT.md   # This file
```

## Costs:
- MongoDB Atlas: **FREE** (512MB limit)
- Render Backend: **FREE** (sleeps after 15min inactivity)
- Vercel Frontend: **FREE** (unlimited static sites)

**Total Monthly Cost: $0**

Your app will work exactly the same as the Emergent version, just hosted on free services like your other projects.
# Free Deployment Setup - Step by Step

## You Need These Accounts (All Free):
1. **GitHub** (to store code)
2. **MongoDB Atlas** (free database)
3. **Render** (free backend hosting)
4. **Vercel** (free frontend hosting)

---

## Step 1: MongoDB Atlas Setup
1. Go to https://mongodb.com/cloud/atlas
2. Sign up for free
3. Choose "Build a Database" → "FREE" (M0)
4. Choose AWS, any region
5. Create cluster name: `bar-stock-db`
6. Create database user (username/password)
7. Add IP: `0.0.0.0/0` (allow all)
8. Get connection string (replace `<password>` with your password)

**Save this connection string for Step 3!**

---

## Step 2: Push Code to GitHub
1. Create new GitHub repository: `bar-stock-management`
2. Upload these folders:
   - `backend/` (all files)
   - `frontend/` (all files)
3. Make repository public

---

## Step 3: Deploy Backend to Render
1. Go to https://render.com/
2. Sign up and connect GitHub
3. Click "New +" → "Web Service"
4. Connect your `bar-stock-management` repository
5. Settings:
   - **Name**: `bar-stock-backend`
   - **Environment**: `Python 3`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. **Environment Variables**:
   - `MONGO_URL`: (your MongoDB Atlas connection string)
   - `CORS_ORIGINS`: `*`
7. Click "Deploy Web Service"

**Copy your Render URL for Step 4!** (like https://bar-stock-backend.onrender.com)

---

## Step 4: Deploy Frontend to Vercel
1. Go to https://vercel.com/
2. Sign up and connect GitHub
3. Click "Import Project"
4. Select your `bar-stock-management` repository
5. Settings:
   - **Framework Preset**: `Create React App`
   - **Root Directory**: `frontend`
6. **Environment Variables**:
   - `REACT_APP_BACKEND_URL`: (your Render backend URL)
7. Click "Deploy"

---

## Step 5: Initialize Your Data
1. Go to your Vercel frontend URL
2. The app should load normally
3. Go to Manage tab
4. Your 79 items will auto-initialize
5. Start using your bar stock system!

---

## Troubleshooting:
- **Backend won't start**: Check MongoDB connection string
- **Frontend can't reach backend**: Check REACT_APP_BACKEND_URL
- **CORS errors**: Make sure CORS_ORIGINS is set to `*`

**Total Setup Time: 20-30 minutes**
**Monthly Cost: $0** 🎉
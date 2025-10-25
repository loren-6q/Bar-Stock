# Complete Bar Stock Management Code

## File Structure to Create:
```
bar-stock-management/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── render.yaml
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.js
    │   ├── App.css
    │   ├── index.js
    │   └── index.css
    ├── public/
    │   └── index.html
    ├── vercel.json
    └── tailwind.config.js
```

## Step 1: Create Backend Files

### backend/requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pymongo[srv]==4.6.0
python-multipart==0.0.6
cors==1.0.1
fastapi-cors==0.0.6
pydantic==2.5.0
python-dateutil==2.8.2
```

### backend/render.yaml
```
services:
  - type: web
    name: bar-stock-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: MONGO_URL
        sync: false
      - key: CORS_ORIGINS
        value: "*"
```

## Step 2: Create Frontend Files

### frontend/package.json
```json
{
  "name": "bar-stock-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "axios": "^1.6.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "lucide-react": "^0.294.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "react-scripts": "5.0.1",
    "tailwind-merge": "^2.1.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### frontend/vercel.json
```json
{
  "framework": "create-react-app",
  "env": {
    "REACT_APP_BACKEND_URL": "@backend-url"
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### frontend/tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## Step 3: Your MongoDB Connection
Your connection string: `mongodb+srv://6Q:6QWETBarStock@bar-stock-db.6ffaqnd.mongodb.net/?appName=bar-stock-db`

## Step 4: Deploy Instructions
1. Upload to GitHub
2. Deploy backend to Render with your MongoDB connection
3. Deploy frontend to Vercel with backend URL
4. Total cost: $0/month

I'll provide the main code files in separate messages due to size limits.
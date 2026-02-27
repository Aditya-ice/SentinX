import os
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis

app = FastAPI(title="SentinX API", description="Headless API for Network Threats")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's a local mock, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis
redis_host = os.environ.get('REDIS_HOST', 'localhost')
r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SentinX API"}

@app.get("/threats/active")
def get_active_threats():
    """
    Fetches all currently active threats (blocked IPs) from the Redis cache.
    These are the IPs that the ML model has flagged in the last 5 minutes.
    """
    try:
        # Scan for all keys starting with 'threat:'
        keys = r.keys("threat:*")
        
        threats = []
        if keys:
            # Fetch all values corresponding to the keys
            values = r.mget(keys)
            for val in values:
                if val:
                    threats.append(json.loads(val))
                    
        return JSONResponse(content={
            "count": len(threats),
            "threats": threats
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/threats/active/ips")
def get_active_blocked_ips():
    """
    Returns just a flat list of IPs that are currently blocked.
    Useful for quick Firewall/WAF integrations.
    """
    try:
        keys = r.keys("threat:*")
        
        ips = []
        if keys:
            values = r.mget(keys)
            for val in values:
                if val:
                    data = json.loads(val)
                    ips.append(data.get("source_ip"))
                    
        return JSONResponse(content={"blocked_ips": ips})
    except Exception as e:
         return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

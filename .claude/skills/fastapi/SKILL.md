---
name: fastapi
description: Build production-ready FastAPI applications with best practices. Use when creating REST APIs, backend services, or when the user mentions FastAPI, API endpoints, Pydantic models, or async Python web services.
---

# FastAPI Framework Skill

When building FastAPI applications, follow these patterns and best practices:

## 1. Project Structure

Use a clean, scalable structure:

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization
│   ├── config.py         # Settings & configuration
│   ├── dependencies.py   # Shared dependencies
│   ├── models/          # Pydantic models
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── routers/         # API route handlers
│   │   ├── __init__.py
│   │   └── items.py
│   ├── services/        # Business logic
│   │   ├── __init__.py
│   │   └── item_service.py
│   └── database.py      # Database connection
├── tests/
├── requirements.txt
└── .env
```

## 2. Core App Setup (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import items
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## 3. Configuration with Pydantic Settings (config.py)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI App"
    VERSION: str = "1.0.0"
    DATABASE_URL: str
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 4. Pydantic Models (models/schemas.py)

Always use Pydantic for request/response validation:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
```

## 5. Router Pattern (routers/items.py)

Separate routes into routers for organization:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.services.item_service import ItemService
from app.dependencies import get_item_service

router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    service: ItemService = Depends(get_item_service)
):
    """Create a new item"""
    return await service.create_item(item)

@router.get("/", response_model=List[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    service: ItemService = Depends(get_item_service)
):
    """List all items with pagination"""
    return await service.list_items(skip=skip, limit=limit)

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service)
):
    """Get a specific item by ID"""
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    service: ItemService = Depends(get_item_service)
):
    """Update an existing item"""
    item = await service.update_item(item_id, item_update)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service)
):
    """Delete an item"""
    success = await service.delete_item(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
```

## 6. Dependency Injection (dependencies.py)

Use dependencies for reusable logic:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.item_service import ItemService
from app.database import get_db

security = HTTPBearer()

async def get_item_service(db = Depends(get_db)) -> ItemService:
    """Dependency to get item service"""
    return ItemService(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify JWT token and return current user"""
    token = credentials.credentials
    # Implement JWT verification logic here
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user
```

## 7. Service Layer Pattern (services/item_service.py)

Separate business logic from routes:

```python
from typing import List, Optional
from app.models.schemas import ItemCreate, ItemUpdate

class ItemService:
    def __init__(self, db):
        self.db = db
    
    async def create_item(self, item: ItemCreate):
        """Create a new item"""
        # Business logic here
        db_item = Item(**item.dict())
        self.db.add(db_item)
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item
    
    async def list_items(self, skip: int = 0, limit: int = 100) -> List:
        """List items with pagination"""
        result = await self.db.execute(
            select(Item).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_item(self, item_id: int) -> Optional:
        """Get item by ID"""
        result = await self.db.execute(
            select(Item).filter(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def update_item(self, item_id: int, item_update: ItemUpdate):
        """Update an existing item"""
        item = await self.get_item(item_id)
        if not item:
            return None
        
        update_data = item_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def delete_item(self, item_id: int) -> bool:
        """Delete an item"""
        item = await self.get_item(item_id)
        if not item:
            return False
        
        await self.db.delete(item)
        await self.db.commit()
        return True
```

## 8. Database Setup (database.py)

For SQLAlchemy async:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

## 9. Error Handling

Create custom exception handlers:

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

class CustomException(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.name, "message": exc.message}
    )
```

## 10. Testing

Write tests using pytest and httpx:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/items/",
            json={"name": "Test Item", "price": 10.99}
        )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99
```

## Key Best Practices

1. **Always use async/await**: FastAPI is built for async - use it consistently
2. **Separate concerns**: Routes → Services → Database/External APIs
3. **Type everything**: Use Pydantic models and type hints everywhere
4. **Use dependency injection**: For database sessions, authentication, etc.
5. **Validate at the edge**: Let Pydantic validate all inputs
6. **Return proper status codes**: 200, 201, 204, 400, 401, 404, 500
7. **Document automatically**: FastAPI generates OpenAPI docs - add descriptions
8. **Handle errors gracefully**: Use HTTPException and custom exception handlers
9. **Use environment variables**: Never hardcode secrets
10. **Test thoroughly**: Write tests for all endpoints

## Common Patterns

### Background Tasks
```python
from fastapi import BackgroundTasks

@router.post("/send-email/")
async def send_email(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_task, "user@example.com")
    return {"message": "Email will be sent"}
```

### File Uploads
```python
from fastapi import UploadFile, File

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Process file
    return {"filename": file.filename}
```

### WebSockets
```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")
```

## Performance Tips

1. **Use async database drivers**: asyncpg for PostgreSQL, motor for MongoDB
2. **Enable response caching**: Use Redis for frequently accessed data
3. **Connection pooling**: Configure proper pool sizes
4. **Pagination**: Always paginate list endpoints
5. **Rate limiting**: Use slowapi or custom middleware
6. **Compression**: Enable gzip middleware for responses

Remember: FastAPI is fast by default, but good architecture makes it maintainable!

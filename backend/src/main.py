"""FastAPI application for Sales Management System with multi-select filters"""
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from typing import List, Optional
from datetime import date
import os

from .database import get_db, engine, Base
from .models import SalesTransaction

# Create tables
Base.metadata.create_all(bind=engine)

# Create helpful indexes for faster filtering/search
def ensure_indexes():
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_sales_customer_region ON sales_transactions(customer_region)",
        "CREATE INDEX IF NOT EXISTS idx_sales_gender ON sales_transactions(gender)",
        "CREATE INDEX IF NOT EXISTS idx_sales_age ON sales_transactions(age)",
        "CREATE INDEX IF NOT EXISTS idx_sales_product_category ON sales_transactions(product_category)",
        "CREATE INDEX IF NOT EXISTS idx_sales_payment_method ON sales_transactions(payment_method)",
        "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_transactions(date)",
        "CREATE INDEX IF NOT EXISTS idx_sales_customer_name ON sales_transactions(customer_name)",
        "CREATE INDEX IF NOT EXISTS idx_sales_phone_number ON sales_transactions(phone_number)",
        "CREATE INDEX IF NOT EXISTS idx_sales_tags ON sales_transactions(tags)"
    ]
    with engine.connect() as conn:
        for stmt in index_statements:
            conn.execute(text(stmt))
        conn.commit()

ensure_indexes()

app = FastAPI(title="Sales Management System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve frontend paths (frontend/public)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "public"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"
STATIC_DIR = FRONTEND_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse(str(FRONTEND_INDEX))

@app.get("/api/filters/options")
async def get_filter_options(db: Session = Depends(get_db)):
    """Get all available filter options for multi-select dropdowns"""
    try:
        # Get distinct values for each filter
        regions = db.query(SalesTransaction.customer_region).distinct().filter(
            SalesTransaction.customer_region.isnot(None)
        ).all()
        
        genders = db.query(SalesTransaction.gender).distinct().filter(
            SalesTransaction.gender.isnot(None)
        ).all()
        
        categories = db.query(SalesTransaction.product_category).distinct().filter(
            SalesTransaction.product_category.isnot(None)
        ).all()
        
        payment_methods = db.query(SalesTransaction.payment_method).distinct().filter(
            SalesTransaction.payment_method.isnot(None)
        ).all()
        
        # Get all unique tags (tags stored as TEXT in PostgreSQL array format)
        all_tags = db.query(SalesTransaction.tags).filter(
            SalesTransaction.tags.isnot(None),
            SalesTransaction.tags != '',
            SalesTransaction.tags != '{}'
        ).all()
        unique_tags = set()
        for tag_tuple in all_tags:
            if tag_tuple[0]:
                # Parse PostgreSQL array format: {tag1,tag2}
                tags_str = tag_tuple[0].strip('{}')
                if tags_str:
                    tags = [t.strip('"').strip() for t in tags_str.split(',') if t.strip()]
                    unique_tags.update(tags)
        
        # Get age range
        min_age = db.query(func.min(SalesTransaction.age)).scalar() or 0
        max_age = db.query(func.max(SalesTransaction.age)).scalar() or 100
        
        # Create age ranges
        age_ranges = []
        for start in range(min_age, max_age, 10):
            age_ranges.append(f"{start}-{start+9}")
        
        return {
            "customer_regions": sorted([r[0] for r in regions if r[0]]),
            "genders": sorted([g[0] for g in genders if g[0]]),
            "age_ranges": age_ranges,
            "product_categories": sorted([c[0] for c in categories if c[0]]),
            "tags": sorted(list(unique_tags)),
            "payment_methods": sorted([p[0] for p in payment_methods if p[0]])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions")
async def get_transactions(
    customer_regions: Optional[List[str]] = Query(None),
    genders: Optional[List[str]] = Query(None),
    age_ranges: Optional[List[str]] = Query(None),
    product_categories: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    payment_methods: Optional[List[str]] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "customer_name",
    sort_order: Optional[str] = "asc",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get transactions with multi-select filters
    All filters are optional and can be combined
    """
    try:
        # Clamp limit for performance
        safe_limit = max(10, min(limit, 200))
        
        query = db.query(SalesTransaction)
        
        # Apply multi-select filters
        if customer_regions:
            query = query.filter(SalesTransaction.customer_region.in_(customer_regions))
        
        if genders:
            query = query.filter(SalesTransaction.gender.in_(genders))
        
        if age_ranges:
            # Parse age ranges and filter
            age_conditions = []
            for age_range in age_ranges:
                if "-" in age_range:
                    start, end = map(int, age_range.split("-"))
                    age_conditions.append(
                        and_(SalesTransaction.age >= start, SalesTransaction.age <= end)
                    )
            if age_conditions:
                query = query.filter(or_(*age_conditions))
        
        if product_categories:
            query = query.filter(SalesTransaction.product_category.in_(product_categories))
        
        if tags:
            # Filter by tags (stored as TEXT in format: {tag1,tag2})
            tag_conditions = []
            for tag in tags:
                # Match tag within the PostgreSQL array string
                tag_conditions.append(SalesTransaction.tags.like(f'%{tag}%'))
            if tag_conditions:
                query = query.filter(or_(*tag_conditions))
        
        if payment_methods:
            query = query.filter(SalesTransaction.payment_method.in_(payment_methods))
        
        # Date range filter
        if start_date:
            query = query.filter(SalesTransaction.date >= start_date)
        if end_date:
            query = query.filter(SalesTransaction.date <= end_date)
        
        # Search filter (name or phone)
        if search:
            trimmed = search.strip()
            if trimmed:
                query = query.filter(
                    or_(
                        func.lower(SalesTransaction.customer_name) == trimmed.lower(),
                        SalesTransaction.phone_number == trimmed
                    )
                )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Sorting
        if sort_by:
            column = getattr(SalesTransaction, sort_by, None)
            if column:
                if sort_order == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
        
        # Pagination
        transactions = query.offset(offset).limit(safe_limit).all()
        
        return {
            "total": total_count,
            "limit": safe_limit,
            "offset": offset,
            "data": [t.to_dict() for t in transactions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics(
    customer_regions: Optional[List[str]] = Query(None),
    genders: Optional[List[str]] = Query(None),
    age_ranges: Optional[List[str]] = Query(None),
    product_categories: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    payment_methods: Optional[List[str]] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics (total units, amount, discount) based on applied filters
    """
    try:
        query = db.query(SalesTransaction)
        
        # Apply same filters as transactions endpoint
        if customer_regions:
            query = query.filter(SalesTransaction.customer_region.in_(customer_regions))
        
        if genders:
            query = query.filter(SalesTransaction.gender.in_(genders))
        
        if age_ranges:
            age_conditions = []
            for age_range in age_ranges:
                if "-" in age_range:
                    start, end = map(int, age_range.split("-"))
                    age_conditions.append(
                        and_(SalesTransaction.age >= start, SalesTransaction.age <= end)
                    )
            if age_conditions:
                query = query.filter(or_(*age_conditions))
        
        if product_categories:
            query = query.filter(SalesTransaction.product_category.in_(product_categories))
        
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(SalesTransaction.tags.like(f'%{tag}%'))
            if tag_conditions:
                query = query.filter(or_(*tag_conditions))
        
        if payment_methods:
            query = query.filter(SalesTransaction.payment_method.in_(payment_methods))
        
        if start_date:
            query = query.filter(SalesTransaction.date >= start_date)
        if end_date:
            query = query.filter(SalesTransaction.date <= end_date)
        
        if search:
            trimmed = search.strip()
            if trimmed:
                query = query.filter(
                    or_(
                        func.lower(SalesTransaction.customer_name) == trimmed.lower(),
                        SalesTransaction.phone_number == trimmed
                    )
                )
        
        # Calculate statistics
        stats = query.with_entities(
            func.sum(SalesTransaction.quantity).label("total_units"),
            func.sum(SalesTransaction.total_amount).label("total_amount"),
            func.sum(SalesTransaction.discount).label("total_discount"),
            func.count(SalesTransaction.transaction_id).label("total_transactions")
        ).first()
        
        return {
            "total_units": int(stats.total_units or 0),
            "total_amount": float(stats.total_amount or 0),
            "total_discount": float(stats.total_discount or 0),
            "total_transactions": int(stats.total_transactions or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

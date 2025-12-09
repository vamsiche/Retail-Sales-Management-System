"""Database models for Sales Management System"""
from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class SalesTransaction(Base):
    __tablename__ = "sales_transactions"
    __table_args__ = {'extend_existing': True}
    
    transaction_id = Column(String, primary_key=True)  # Use transaction_id as primary key
    date = Column(Date)
    customer_id = Column(String)
    customer_name = Column(String)
    phone_number = Column(String)
    gender = Column(String)
    age = Column(Integer)
    customer_region = Column(String)
    product_category = Column(String)
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    total_amount = Column(Float)
    discount = Column(Float)
    payment_method = Column(String)
    tags = Column(String)  # Stored as TEXT in database
    
    def to_dict(self):
        """Convert model to dictionary"""
        # Parse tags from PostgreSQL array format {tag1,tag2} to Python list
        tags_list = []
        if self.tags:
            tags_str = self.tags.strip('{}')
            if tags_str:
                tags_list = [t.strip('"').strip() for t in tags_str.split(',') if t.strip()]
        
        return {
            "transaction_id": self.transaction_id,
            "date": self.date.isoformat() if self.date else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "phone_number": self.phone_number,
            "gender": self.gender,
            "age": self.age,
            "customer_region": self.customer_region,
            "product_category": self.product_category,
            "quantity": self.quantity,
            "price_per_unit": float(self.price_per_unit) if self.price_per_unit else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "discount": float(self.discount) if self.discount else 0,
            "payment_method": self.payment_method,
            "tags": tags_list
        }

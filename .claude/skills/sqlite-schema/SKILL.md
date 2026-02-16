---
name: sqlite-schema
description: Design and implement SQLite database schemas with best practices. Use when creating databases, designing tables, writing SQL queries, implementing migrations, or when user mentions SQLite, database schema, SQL, tables, indexes, or data modeling.
---

# SQLite Database Schema Skill

When designing and implementing SQLite databases, follow these patterns:

## 1. Database Schema Design Principles

### A. Naming Conventions
```sql
-- Use lowercase with underscores
-- Tables: plural nouns (users, orders, products)
-- Columns: singular descriptive names (user_id, email, created_at)
-- Indexes: idx_tablename_columnname
-- Foreign keys: fk_tablename_columnname

-- Good Examples:
users, order_items, product_categories
user_id, first_name, created_at, is_active

-- Avoid:
Users, OrderItems, ProductCategories (mixed case)
uid, fn, crt (abbreviations)
```

### B. Core Table Structure Pattern
```sql
CREATE TABLE users (
    -- Primary key (always use INTEGER PRIMARY KEY)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Required fields
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    
    -- Optional fields
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    
    -- Status/flags
    is_active INTEGER DEFAULT 1,
    is_verified INTEGER DEFAULT 0,
    
    -- Timestamps (always include these)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Constraints
    CHECK (email LIKE '%@%'),
    CHECK (is_active IN (0, 1)),
    CHECK (is_verified IN (0, 1))
);

-- Create indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
```

## 2. Common Table Patterns

### A. User/Account Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    is_active INTEGER DEFAULT 1,
    email_verified INTEGER DEFAULT 0,
    last_login_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### B. Product/Item Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    price REAL NOT NULL CHECK (price >= 0),
    compare_at_price REAL CHECK (compare_at_price >= price),
    cost REAL CHECK (cost >= 0),
    sku TEXT UNIQUE,
    barcode TEXT,
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    weight REAL,
    is_active INTEGER DEFAULT 1,
    is_featured INTEGER DEFAULT 0,
    category_id INTEGER,
    vendor_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
);

CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_is_active ON products(is_active);
```

### C. Order Table
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
    ),
    subtotal REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    shipping REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    
    -- Shipping info
    shipping_name TEXT,
    shipping_address TEXT,
    shipping_city TEXT,
    shipping_state TEXT,
    shipping_zip TEXT,
    shipping_country TEXT,
    
    -- Tracking
    tracking_number TEXT,
    shipped_at TEXT,
    delivered_at TEXT,
    
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_number ON orders(order_number);
```

### D. Junction/Many-to-Many Table
```sql
-- Order items (junction between orders and products)
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price REAL NOT NULL CHECK (price >= 0),
    subtotal REAL NOT NULL CHECK (subtotal >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    
    -- Ensure unique product per order
    UNIQUE (order_id, product_id)
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
```

## 3. Relationships & Foreign Keys

```sql
-- One-to-Many: User has many Posts
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Many-to-Many: Posts and Tags (requires junction table)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE post_tags (
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Self-referential: User follows User
CREATE TABLE user_follows (
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (follower_id != following_id)
);
```

## 4. Indexes for Performance

```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Multi-column index (order matters!)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial index (for specific queries)
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = 1;

-- Unique index
CREATE UNIQUE INDEX idx_users_username_lower ON users(LOWER(username));

-- Full-text search index
CREATE VIRTUAL TABLE posts_fts USING fts5(title, content);
```

## 5. Triggers for Automation

```sql
-- Auto-update updated_at timestamp
CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users 
    SET updated_at = datetime('now') 
    WHERE id = OLD.id;
END;

-- Calculate order total automatically
CREATE TRIGGER calculate_order_total
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total = (
        SELECT SUM(subtotal) 
        FROM order_items 
        WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
END;

-- Soft delete (move to archive instead of delete)
CREATE TRIGGER soft_delete_user
INSTEAD OF DELETE ON users
FOR EACH ROW
BEGIN
    UPDATE users 
    SET is_active = 0, 
        updated_at = datetime('now')
    WHERE id = OLD.id;
END;

-- Audit log trigger
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_values TEXT,
    new_values TEXT,
    user_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER audit_users_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values)
    VALUES (
        'users',
        OLD.id,
        'UPDATE',
        json_object('email', OLD.email, 'username', OLD.username),
        json_object('email', NEW.email, 'username', NEW.username)
    );
END;
```

## 6. Views for Common Queries

```sql
-- User profile with stats
CREATE VIEW user_profiles AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT p.id) as post_count,
    COUNT(DISTINCT f.follower_id) as follower_count,
    COUNT(DISTINCT ff.following_id) as following_count,
    u.created_at
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
LEFT JOIN user_follows f ON u.id = f.following_id
LEFT JOIN user_follows ff ON u.id = ff.follower_id
GROUP BY u.id;

-- Active products with category
CREATE VIEW active_products AS
SELECT 
    p.id,
    p.name,
    p.slug,
    p.price,
    p.quantity,
    c.name as category_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.is_active = 1;

-- Order summary
CREATE VIEW order_summaries AS
SELECT 
    o.id,
    o.order_number,
    o.status,
    o.total,
    u.email as customer_email,
    COUNT(oi.id) as item_count,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id;
```

## 7. Full-Text Search

```sql
-- Create FTS5 table
CREATE VIRTUAL TABLE products_fts USING fts5(
    name,
    description,
    content=products,
    content_rowid=id
);

-- Populate FTS table
INSERT INTO products_fts(rowid, name, description)
SELECT id, name, description FROM products;

-- Keep FTS in sync with triggers
CREATE TRIGGER products_fts_insert AFTER INSERT ON products
BEGIN
    INSERT INTO products_fts(rowid, name, description)
    VALUES (NEW.id, NEW.name, NEW.description);
END;

CREATE TRIGGER products_fts_update AFTER UPDATE ON products
BEGIN
    UPDATE products_fts 
    SET name = NEW.name, description = NEW.description
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER products_fts_delete AFTER DELETE ON products
BEGIN
    DELETE FROM products_fts WHERE rowid = OLD.id;
END;

-- Search query
SELECT p.* FROM products p
JOIN products_fts fts ON p.id = fts.rowid
WHERE products_fts MATCH 'wireless bluetooth'
ORDER BY rank;
```

## 8. JSON Support

```sql
-- Store JSON data
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    preferences TEXT NOT NULL DEFAULT '{}',
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (json_valid(preferences)),
    CHECK (json_valid(metadata))
);

-- Query JSON data
SELECT 
    user_id,
    json_extract(preferences, '$.theme') as theme,
    json_extract(preferences, '$.notifications.email') as email_notifications
FROM user_settings
WHERE json_extract(preferences, '$.language') = 'en';

-- Update JSON field
UPDATE user_settings
SET preferences = json_set(
    preferences,
    '$.theme',
    'dark',
    '$.notifications.email',
    true
)
WHERE user_id = 1;
```

## 9. Database Initialization Script

```sql
-- init_db.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Performance settings
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;

-- Create tables in dependency order
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    parent_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0),
    category_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Insert default data
INSERT OR IGNORE INTO categories (id, name, slug) VALUES 
    (1, 'Electronics', 'electronics'),
    (2, 'Clothing', 'clothing'),
    (3, 'Books', 'books');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = 1;

-- Create triggers
CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    UPDATE products 
    SET updated_at = datetime('now') 
    WHERE id = OLD.id;
END;
```

## 10. Python Integration Example

```python
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email);
            """)
    
    def create_user(self, email: str, username: str) -> int:
        """Create a new user"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, username) VALUES (?, ?)",
                (email, username)
            )
            return cursor.lastrowid
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_users(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get paginated list of users"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_user(
        self, 
        user_id: int, 
        email: Optional[str] = None,
        username: Optional[str] = None
    ) -> bool:
        """Update user fields"""
        updates = []
        params = []
        
        if email:
            updates.append("email = ?")
            params.append(email)
        if username:
            updates.append("username = ?")
            params.append(username)
        
        if not updates:
            return False
        
        params.append(user_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params
            )
            return cursor.rowcount > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )
            return cursor.rowcount > 0

# Usage
db = Database("app.db")

# Create
user_id = db.create_user("alice@example.com", "alice")

# Read
user = db.get_user(user_id)
users = db.get_users(limit=10, offset=0)

# Update
db.update_user(user_id, email="newemail@example.com")

# Delete
db.delete_user(user_id)
```

## Best Practices

1. **Always use INTEGER PRIMARY KEY**: For auto-incrementing IDs
2. **Enable foreign keys**: `PRAGMA foreign_keys = ON`
3. **Add timestamps**: Include `created_at` and `updated_at` on all tables
4. **Use CHECK constraints**: Validate data at the database level
5. **Index foreign keys**: Always create indexes on foreign key columns
6. **Use transactions**: Wrap multiple operations in transactions
7. **Normalize data**: Follow normalization rules (avoid redundancy)
8. **Use meaningful names**: Clear, descriptive table and column names
9. **Add NOT NULL**: Be explicit about nullable columns
10. **Document schema**: Add comments explaining complex constraints

## Performance Optimization

```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Increase cache size (in KB, negative = KB)
PRAGMA cache_size = -64000;  -- 64MB

-- Analyze query performance
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE user_id = 1;

-- Vacuum database periodically
VACUUM;

-- Analyze tables for query optimizer
ANALYZE;
```

## Common Queries

```sql
-- Pagination
SELECT * FROM products 
ORDER BY created_at DESC 
LIMIT 10 OFFSET 20;

-- Search with LIKE
SELECT * FROM products 
WHERE name LIKE '%phone%' 
OR description LIKE '%phone%';

-- Aggregate functions
SELECT 
    category_id,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products
GROUP BY category_id
HAVING COUNT(*) > 5;

-- Join multiple tables
SELECT 
    o.order_number,
    u.email,
    p.name as product_name,
    oi.quantity,
    oi.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'pending';
```

Remember: Good schema design is the foundation of a reliable application. Plan your schema carefully and always use foreign keys and constraints!

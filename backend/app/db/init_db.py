"""
Database initialization script.
Creates all tables and seeds predefined capabilities.
"""
import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from app.config import settings
from app.db.models import Base, Capability
from app.db.session import get_engine, get_session_factory, init_database


# Predefined capabilities from data-model.md
PREDEFINED_CAPABILITIES = [
    {
        "name": "navigate",
        "display_name": "Navigate to URL",
        "description": "Navigate the browser to a specified URL",
        "category": "navigation",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "wait_until": {"type": "string", "enum": ["load", "domcontentloaded", "networkidle"]},
                "timeout_ms": {"type": "integer", "minimum": 0, "maximum": 30000}
            },
            "required": ["url"]
        }
    },
    {
        "name": "click_element",
        "display_name": "Click Element",
        "description": "Click on a page element by selector or text",
        "category": "interaction",
        "risk_level": "medium",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "index": {"type": "integer", "minimum": 0},
                "wait_for_navigation": {"type": "boolean"}
            }
        }
    },
    {
        "name": "type_text",
        "display_name": "Type Text",
        "description": "Type text into an input field",
        "category": "interaction",
        "risk_level": "medium",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "clear_first": {"type": "boolean"},
                "press_enter": {"type": "boolean"}
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "extract_text",
        "display_name": "Extract Text",
        "description": "Extract text content from page elements",
        "category": "extraction",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "all": {"type": "boolean"},
                "trim": {"type": "boolean"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "extract_links",
        "display_name": "Extract Links",
        "description": "Extract all links from the page or a specific section",
        "category": "extraction",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "filter_pattern": {"type": "string"}
            }
        }
    },
    {
        "name": "extract_tables",
        "display_name": "Extract Tables",
        "description": "Extract table data from the page",
        "category": "extraction",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "include_headers": {"type": "boolean"}
            }
        }
    },
    {
        "name": "scroll",
        "display_name": "Scroll Page",
        "description": "Scroll the page in a specified direction",
        "category": "navigation",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "top", "bottom"]},
                "amount": {"type": "integer", "minimum": 0},
                "smooth": {"type": "boolean"}
            },
            "required": ["direction"]
        }
    },
    {
        "name": "screenshot",
        "display_name": "Take Screenshot",
        "description": "Capture a screenshot of the page or element",
        "category": "utility",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "full_page": {"type": "boolean"},
                "format": {"type": "string", "enum": ["png", "jpeg"]}
            }
        }
    },
    {
        "name": "get_dom",
        "display_name": "Get DOM Structure",
        "description": "Get the DOM structure of the page or element",
        "category": "extraction",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "depth": {"type": "integer", "minimum": 1, "maximum": 10}
            }
        }
    },
    {
        "name": "highlight_element",
        "display_name": "Highlight Element",
        "description": "Visually highlight an element on the page",
        "category": "utility",
        "risk_level": "low",
        "schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "duration_ms": {"type": "integer", "minimum": 0, "maximum": 10000}
            },
            "required": ["selector"]
        }
    }
]


def create_tables() -> None:
    """
    Create all database tables from SQLAlchemy models.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")


def seed_capabilities() -> None:
    """
    Seed predefined capabilities into the database.
    Skips capabilities that already exist.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        for cap_data in PREDEFINED_CAPABILITIES:
            # Check if capability already exists
            existing = db.query(Capability).filter(Capability.name == cap_data["name"]).first()
            if existing:
                print(f"  - Capability '{cap_data['name']}' already exists, skipping")
                continue

            # Create new capability
            capability = Capability(
                id=str(uuid4()),
                name=cap_data["name"],
                display_name=cap_data["display_name"],
                description=cap_data["description"],
                category=cap_data["category"],
                risk_level=cap_data["risk_level"],
                schema=json.dumps(cap_data["schema"]),
                enabled=True
            )
            db.add(capability)
            print(f"  + Seeded capability: {cap_data['name']}")

        db.commit()
        print("[OK] Capabilities seeded successfully")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding capabilities: {e}")
        raise
    finally:
        db.close()


def verify_database() -> None:
    """
    Verify database setup by checking table existence and capability count.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        # Check capabilities
        cap_count = db.query(Capability).count()
        print(f"[OK] Database verification: {cap_count} capabilities available")

        if cap_count < 10:
            print(f"[WARNING] Expected 10 capabilities, found {cap_count}")

    finally:
        db.close()


def init_db() -> None:
    """
    Main initialization function.
    Initializes database connection, creates tables, and seeds data.
    """
    print("Initializing BrowserMind database...")
    print(f"Database URL: {settings.database_url}")

    # Initialize database connection
    init_database()
    print("[OK] Database connection initialized")

    # Create tables
    create_tables()

    # Seed capabilities
    print("Seeding predefined capabilities...")
    seed_capabilities()

    # Verify setup
    verify_database()

    print("\n[OK] Database initialization complete!")


if __name__ == "__main__":
    init_db()

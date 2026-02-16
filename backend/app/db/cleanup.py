"""
90-day retention cleanup job infrastructure.
Provides scheduled job framework and database cleanup utilities.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Message, Session as SessionModel, ToolLog
from app.db.session import get_db_session


class CleanupJob:
    """
    Scheduled cleanup job for expired sessions and old data.
    Runs periodically to enforce 90-day retention policy.
    """

    def __init__(self):
        self.is_running = False
        self.last_run: datetime = None
        self.next_run: datetime = None

    async def start(self) -> None:
        """
        Start the cleanup job scheduler.
        Runs every 24 hours at 2 AM local time.
        """
        if not settings.enable_cleanup_job:
            print("Cleanup job disabled in configuration")
            return

        self.is_running = True
        print(f"Cleanup job started (interval: {settings.cleanup_interval_hours}h)")

        while self.is_running:
            try:
                # Calculate next run time
                now = datetime.now()
                if self.next_run is None or now >= self.next_run:
                    await self.run_cleanup()
                    self.last_run = now
                    self.next_run = now + timedelta(hours=settings.cleanup_interval_hours)
                    print(f"Next cleanup scheduled for: {self.next_run}")

                # Sleep until next run (check every hour)
                await asyncio.sleep(3600)

            except Exception as e:
                print(f"Error in cleanup job: {e}")
                # Continue running even if cleanup fails
                await asyncio.sleep(3600)

    async def stop(self) -> None:
        """Stop the cleanup job scheduler."""
        self.is_running = False
        print("Cleanup job stopped")

    async def run_cleanup(self) -> None:
        """
        Execute cleanup operations.
        Deletes expired sessions and associated data.
        """
        print(f"Running cleanup job at {datetime.now()}")

        with get_db_session() as db:
            # Find expired sessions (not archived, past expiration date)
            expired_count = await self.cleanup_expired_sessions(db)

            # Clean up orphaned tool logs (optional)
            orphaned_logs = await self.cleanup_orphaned_logs(db)

            print(f"Cleanup complete: {expired_count} sessions, {orphaned_logs} orphaned logs")

    async def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Archive expired sessions (older than 90 days).

        Args:
            db: Database session

        Returns:
            Number of sessions archived
        """
        from app.db.session_manager import SessionManager

        session_manager = SessionManager(db)
        expired_sessions = session_manager.find_expired_sessions(days=90)

        count = len(expired_sessions)
        if count == 0:
            return 0

        # Archive sessions
        for session in expired_sessions:
            print(f"  Archiving expired session: {session.id} (last updated: {session.updated_at})")
            session.archived_at = datetime.utcnow()

        db.commit()
        return count

    async def cleanup_orphaned_logs(self, db: Session) -> int:
        """
        Clean up tool logs with null session_id that are older than retention period.

        Args:
            db: Database session

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=settings.session_retention_days)

        # Find orphaned logs older than retention period
        orphaned_logs = db.query(ToolLog).filter(
            and_(
                ToolLog.session_id.is_(None),
                ToolLog.timestamp < cutoff_date
            )
        ).all()

        count = len(orphaned_logs)
        if count == 0:
            return 0

        # Delete orphaned logs
        for log in orphaned_logs:
            db.delete(log)

        db.commit()
        return count

    def get_status(self) -> dict:
        """
        Get current cleanup job status.

        Returns:
            Dictionary with job status information
        """
        return {
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "interval_hours": settings.cleanup_interval_hours,
            "retention_days": settings.session_retention_days,
            "enabled": settings.enable_cleanup_job
        }


# Global cleanup job instance
_cleanup_job: CleanupJob = None


def get_cleanup_job() -> CleanupJob:
    """
    Get or create the global cleanup job instance.

    Returns:
        CleanupJob instance
    """
    global _cleanup_job
    if _cleanup_job is None:
        _cleanup_job = CleanupJob()
    return _cleanup_job


async def start_cleanup_job() -> None:
    """
    Start the global cleanup job.
    Should be called on application startup.
    """
    job = get_cleanup_job()
    await job.start()


async def stop_cleanup_job() -> None:
    """
    Stop the global cleanup job.
    Should be called on application shutdown.
    """
    job = get_cleanup_job()
    await job.stop()

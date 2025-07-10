"""
Enhanced Crawl Status Service for Real-time Monitoring
Provides detailed status tracking for manual and scheduled crawls
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


class CrawlStatus(Enum):
    """Enhanced crawl status enumeration"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlType(Enum):
    """Type of crawl operation"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"


@dataclass
class CrawlProgress:
    """Detailed crawl progress information"""
    crawl_id: str
    store_name: str
    status: CrawlStatus
    crawl_type: CrawlType
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: str = "Initializing"
    products_found: int = 0
    products_processed: int = 0
    errors_count: int = 0
    estimated_completion: Optional[datetime] = None
    postal_code: str = "10115"
    triggered_by: str = "system"
    error_details: Optional[str] = None
    session_id: Optional[int] = None


class CrawlStatusService:
    """Service for tracking and monitoring crawl operations in real-time"""
    
    def __init__(self):
        self._active_crawls: Dict[str, CrawlProgress] = {}
        self._completed_crawls: List[CrawlProgress] = []
        self._max_completed_history = 50
        self._last_crawl_attempts: Dict[str, datetime] = {}
        self._min_crawl_interval = timedelta(minutes=5)  # Rate limiting
    
    def start_crawl(
        self, 
        store_name: str, 
        crawl_type: CrawlType = CrawlType.MANUAL,
        postal_code: str = "10115",
        triggered_by: str = "admin",
        session_id: Optional[int] = None
    ) -> str:
        """
        Start tracking a new crawl operation
        
        Args:
            store_name: Name of the store being crawled
            crawl_type: Type of crawl operation
            postal_code: Postal code for location-specific crawling
            triggered_by: Who triggered this crawl
            session_id: Database session ID
            
        Returns:
            Unique crawl ID for tracking
            
        Raises:
            ValueError: If rate limiting prevents new crawl
        """
        # Rate limiting check
        if self._is_rate_limited(store_name):
            last_crawl = self._last_crawl_attempts.get(store_name)
            next_allowed = last_crawl + self._min_crawl_interval
            raise ValueError(
                f"Rate limit exceeded for {store_name}. "
                f"Next crawl allowed at {next_allowed.strftime('%H:%M:%S')}"
            )
        
        # Check if store is already being crawled
        for crawl in self._active_crawls.values():
            if crawl.store_name == store_name and crawl.status in [CrawlStatus.CRAWLING, CrawlStatus.PROCESSING]:
                raise ValueError(f"Store {store_name} is already being crawled")
        
        crawl_id = str(uuid.uuid4())
        progress = CrawlProgress(
            crawl_id=crawl_id,
            store_name=store_name,
            status=CrawlStatus.PENDING,
            crawl_type=crawl_type,
            started_at=datetime.utcnow(),
            postal_code=postal_code,
            triggered_by=triggered_by,
            session_id=session_id
        )
        
        self._active_crawls[crawl_id] = progress
        self._last_crawl_attempts[store_name] = datetime.utcnow()
        
        logger.info(f"Started tracking crawl {crawl_id} for {store_name}")
        return crawl_id
    
    def update_crawl_progress(
        self, 
        crawl_id: str, 
        status: Optional[CrawlStatus] = None,
        current_step: Optional[str] = None,
        progress_percentage: Optional[float] = None,
        products_found: Optional[int] = None,
        products_processed: Optional[int] = None,
        errors_count: Optional[int] = None,
        estimated_completion: Optional[datetime] = None
    ) -> bool:
        """
        Update progress information for an active crawl
        
        Returns:
            True if update was successful, False if crawl not found
        """
        if crawl_id not in self._active_crawls:
            logger.warning(f"Attempted to update non-existent crawl {crawl_id}")
            return False
        
        crawl = self._active_crawls[crawl_id]
        
        if status:
            crawl.status = status
        if current_step:
            crawl.current_step = current_step
        if progress_percentage is not None:
            crawl.progress_percentage = min(100.0, max(0.0, progress_percentage))
        if products_found is not None:
            crawl.products_found = products_found
        if products_processed is not None:
            crawl.products_processed = products_processed
        if errors_count is not None:
            crawl.errors_count = errors_count
        if estimated_completion:
            crawl.estimated_completion = estimated_completion
        
        logger.debug(f"Updated crawl {crawl_id}: {status} - {current_step} ({progress_percentage}%)")
        return True
    
    def complete_crawl(
        self, 
        crawl_id: str, 
        status: CrawlStatus = CrawlStatus.COMPLETED,
        final_products_count: Optional[int] = None,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Mark a crawl as completed and move to history
        
        Returns:
            True if completion was successful, False if crawl not found
        """
        if crawl_id not in self._active_crawls:
            logger.warning(f"Attempted to complete non-existent crawl {crawl_id}")
            return False
        
        crawl = self._active_crawls[crawl_id]
        crawl.status = status
        crawl.completed_at = datetime.utcnow()
        crawl.progress_percentage = 100.0
        crawl.current_step = "Completed"
        
        if final_products_count is not None:
            crawl.products_processed = final_products_count
        if error_details:
            crawl.error_details = error_details
        
        # Move to completed history
        self._completed_crawls.append(crawl)
        del self._active_crawls[crawl_id]
        
        # Maintain history size
        if len(self._completed_crawls) > self._max_completed_history:
            self._completed_crawls = self._completed_crawls[-self._max_completed_history:]
        
        duration = crawl.completed_at - crawl.started_at
        logger.info(
            f"Completed crawl {crawl_id} for {crawl.store_name} in {duration.total_seconds():.1f}s. "
            f"Status: {status.value}, Products: {crawl.products_processed}, Errors: {crawl.errors_count}"
        )
        return True
    
    def get_crawl_status(self, crawl_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a specific crawl"""
        if crawl_id in self._active_crawls:
            return asdict(self._active_crawls[crawl_id])
        
        # Check completed crawls
        for crawl in self._completed_crawls:
            if crawl.crawl_id == crawl_id:
                return asdict(crawl)
        
        return None
    
    def get_active_crawls(self) -> List[Dict[str, Any]]:
        """Get all currently active crawls"""
        return [asdict(crawl) for crawl in self._active_crawls.values()]
    
    def get_crawl_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent crawl history"""
        return [asdict(crawl) for crawl in self._completed_crawls[-limit:]]
    
    def get_store_status(self, store_name: str) -> Dict[str, Any]:
        """Get comprehensive status for a specific store"""
        # Check if currently crawling
        active_crawl = None
        for crawl in self._active_crawls.values():
            if crawl.store_name == store_name:
                active_crawl = asdict(crawl)
                break
        
        # Get recent history for this store
        recent_crawls = [
            asdict(crawl) for crawl in self._completed_crawls 
            if crawl.store_name == store_name
        ][-5:]  # Last 5 crawls
        
        # Rate limiting info
        last_crawl = self._last_crawl_attempts.get(store_name)
        next_allowed_crawl = None
        if last_crawl:
            next_allowed_crawl = last_crawl + self._min_crawl_interval
            if next_allowed_crawl <= datetime.utcnow():
                next_allowed_crawl = None
        
        return {
            "store_name": store_name,
            "active_crawl": active_crawl,
            "recent_crawls": recent_crawls,
            "can_crawl_now": not self._is_rate_limited(store_name),
            "next_allowed_crawl": next_allowed_crawl.isoformat() if next_allowed_crawl else None,
            "last_crawl": last_crawl.isoformat() if last_crawl else None
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        active_count = len(self._active_crawls)
        total_completed = len(self._completed_crawls)
        
        # Calculate success rate from recent crawls
        recent_crawls = self._completed_crawls[-20:] if self._completed_crawls else []
        successful_crawls = sum(1 for crawl in recent_crawls if crawl.status == CrawlStatus.COMPLETED)
        success_rate = (successful_crawls / len(recent_crawls) * 100) if recent_crawls else 0
        
        # Active stores
        active_stores = [crawl.store_name for crawl in self._active_crawls.values()]
        
        return {
            "active_crawls": active_count,
            "active_stores": active_stores,
            "completed_crawls_today": len([
                crawl for crawl in self._completed_crawls 
                if crawl.started_at.date() == datetime.utcnow().date()
            ]),
            "total_completed": total_completed,
            "success_rate_percent": round(success_rate, 1),
            "rate_limited_stores": [
                store for store in self._last_crawl_attempts.keys()
                if self._is_rate_limited(store)
            ]
        }
    
    def cancel_crawl(self, crawl_id: str, reason: str = "Manual cancellation") -> bool:
        """Cancel an active crawl"""
        if crawl_id not in self._active_crawls:
            return False
        
        self.complete_crawl(crawl_id, CrawlStatus.CANCELLED, error_details=reason)
        logger.info(f"Cancelled crawl {crawl_id}: {reason}")
        return True
    
    def _is_rate_limited(self, store_name: str) -> bool:
        """Check if a store is currently rate limited"""
        last_crawl = self._last_crawl_attempts.get(store_name)
        if not last_crawl:
            return False
        
        return datetime.utcnow() - last_crawl < self._min_crawl_interval
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old tracking data"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean completed crawls
        self._completed_crawls = [
            crawl for crawl in self._completed_crawls 
            if crawl.started_at > cutoff
        ]
        
        # Clean rate limiting data
        self._last_crawl_attempts = {
            store: last_attempt for store, last_attempt in self._last_crawl_attempts.items()
            if last_attempt > cutoff
        }
        
        logger.info(f"Cleaned up crawl tracking data older than {max_age_hours} hours")


# Global instance
crawl_status_service = CrawlStatusService() 
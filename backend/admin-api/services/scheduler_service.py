import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from shared.core.config import settings
from shared.core.database import async_session_maker_rw
from shared.services.database_service import DatabaseService
from .crawler_service import CrawlerService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled crawling jobs"""
    
    def __init__(self):
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': settings.max_concurrent_crawls,
            'misfire_grace_time': 3600  # 1 hour grace period
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Europe/Berlin'
        )
        
        self.is_running = False
    
    async def start(self):
        """Start the scheduler"""
        if not self.is_running and settings.enable_scheduler:
            logger.info("Starting scheduler service...")
            
            # Schedule weekly crawling
            self._schedule_weekly_crawl()
            
            # Schedule cleanup jobs
            self._schedule_cleanup_jobs()
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Scheduler service started successfully")
        else:
            logger.info("Scheduler is disabled or already running")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            logger.info("Stopping scheduler service...")
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler service stopped")
    
    def _schedule_weekly_crawl(self):
        """Schedule weekly crawling for all enabled stores"""
        if not settings.enable_scheduler:
            return
        
        # Parse day of week
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        day_of_week = day_mapping.get(settings.weekly_crawl_day_of_week.lower(), 6)  # Default to Sunday
        
        # Create cron trigger for weekly crawling
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=settings.weekly_crawl_hour,
            minute=0
        )
        
        self.scheduler.add_job(
            func=self._run_weekly_crawl,
            trigger=trigger,
            id='weekly_crawl',
            name='Weekly Product Crawl',
            replace_existing=True
        )
        
        logger.info(
            f"Scheduled weekly crawl for {settings.weekly_crawl_day_of_week} "
            f"at {settings.weekly_crawl_hour}:00"
        )
    
    def _schedule_cleanup_jobs(self):
        """Schedule cleanup jobs"""
        
        # Schedule daily cleanup at 3 AM
        self.scheduler.add_job(
            func=self._run_cleanup,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_cleanup',
            name='Daily Database Cleanup',
            replace_existing=True
        )
        
        logger.info("Scheduled daily cleanup at 3:00 AM")
    
    async def _run_weekly_crawl(self):
        """Execute weekly crawl for all enabled stores"""
        logger.info("Starting weekly crawl job...")
        
        try:
            async with async_session_maker_rw() as session:
                db_service = DatabaseService(session)
                crawler_service = CrawlerService(db_service)
                
                # Get all enabled stores
                stores = await db_service.stores.get_all_enabled()
                
                if not stores:
                    logger.warning("No enabled stores found for crawling")
                    return
                
                # Crawl each store
                total_success = 0
                total_errors = 0
                
                for store in stores:
                    try:
                        logger.info(f"Starting crawl for store: {store.name}")
                        
                        # Start crawl session
                        crawl_session = await db_service.crawl_sessions.create(store.id)
                        await db_service.commit()
                        
                        # Run crawler
                        success_count, error_count = await crawler_service.crawl_store(
                            store_name=store.name,
                            postal_code="10115",  # Default postal code
                            crawl_session_id=crawl_session.id
                        )
                        
                        # Update session
                        await db_service.crawl_sessions.complete(
                            session_id=crawl_session.id,
                            total_products=success_count + error_count,
                            success_count=success_count,
                            error_count=error_count,
                            notes=f"Weekly automated crawl"
                        )
                        
                        total_success += success_count
                        total_errors += error_count
                        
                        logger.info(
                            f"Completed crawl for {store.name}: "
                            f"{success_count} products, {error_count} errors"
                        )
                        
                    except Exception as e:
                        logger.error(f"Error crawling store {store.name}: {str(e)}")
                        
                        # Mark session as failed
                        if 'crawl_session' in locals():
                            await db_service.crawl_sessions.fail(
                                crawl_session.id,
                                f"Crawler error: {str(e)}"
                            )
                        
                        total_errors += 1
                    
                    await db_service.commit()
                
                logger.info(
                    f"Weekly crawl completed: {total_success} products crawled, "
                    f"{total_errors} errors"
                )
                
        except Exception as e:
            logger.error(f"Weekly crawl job failed: {str(e)}")
    
    async def _run_cleanup(self):
        """Execute daily cleanup tasks"""
        logger.info("Starting daily cleanup job...")
        
        try:
            async with async_session_maker_rw() as session:
                db_service = DatabaseService(session)
                
                # Hard delete old soft-deleted products (older than 30 days)
                deleted_count = await db_service.products.hard_delete_old_products(days_old=30)
                await db_service.commit()
                
                logger.info(f"Cleanup completed: {deleted_count} old products permanently deleted")
                
        except Exception as e:
            logger.error(f"Daily cleanup job failed: {str(e)}")
    
    # Manual trigger methods for admin endpoints
    
    async def trigger_crawl_now(self, store_name: str = None, postal_code: str = "10115"):
        """Manually trigger crawl for a specific store or all stores with enhanced tracking"""
        logger.info(f"Manual crawl triggered for store: {store_name or 'all stores'}")
        
        try:
            async with async_session_maker() as session:
                db_service = DatabaseService(session)
                crawler_service = CrawlerService(db_service)
                
                if store_name:
                    # Crawl specific store
                    store = await db_service.stores.get_by_name(store_name)
                    if not store:
                        raise ValueError(f"Store '{store_name}' not found")
                    
                    if not store.enabled:
                        raise ValueError(f"Store '{store_name}' is disabled")
                    
                    stores = [store]
                else:
                    # Crawl all enabled stores
                    stores = await db_service.stores.get_all_enabled()
                
                results = []
                
                for store in stores:
                    try:
                        # Start crawl session
                        crawl_session = await db_service.crawl_sessions.create(store.id)
                        await db_service.commit()
                        
                        # Start tracking with crawl status service - this will be handled by the admin router
                        # The crawl_id will be passed from the enhanced admin endpoint
                        
                        # Run crawler with enhanced tracking
                        success_count, error_count = await crawler_service.crawl_store(
                            store_name=store.name,
                            postal_code=postal_code,
                            crawl_session_id=crawl_session.id,
                            crawl_id=None  # Will be set by enhanced admin endpoint
                        )
                        
                        # Update session
                        await db_service.crawl_sessions.complete(
                            session_id=crawl_session.id,
                            total_products=success_count + error_count,
                            success_count=success_count,
                            error_count=error_count,
                            notes="Manual crawl triggered"
                        )
                        
                        results.append({
                            "store": store.name,
                            "success": True,
                            "products_crawled": success_count,
                            "errors": error_count
                        })
                        
                    except Exception as e:
                        logger.error(f"Error in manual crawl for {store.name}: {str(e)}")
                        
                        # Mark session as failed if it exists
                        if 'crawl_session' in locals():
                            await db_service.crawl_sessions.fail(
                                crawl_session.id,
                                f"Manual crawl error: {str(e)}"
                            )
                        
                        results.append({
                            "store": store.name,
                            "success": False,
                            "error": str(e)
                        })
                    
                    await db_service.commit()
                
                return results
                
        except Exception as e:
            logger.error(f"Manual crawl trigger failed: {str(e)}")
            raise
    
    async def trigger_cleanup_now(self):
        """Manually trigger cleanup tasks"""
        logger.info("Manual cleanup triggered")
        
        try:
            async with async_session_maker() as session:
                db_service = DatabaseService(session)
                
                # Hard delete old soft-deleted products
                deleted_count = await db_service.products.hard_delete_old_products(days_old=30)
                await db_service.commit()
                
                return {
                    "success": True,
                    "products_deleted": deleted_count
                }
                
        except Exception as e:
            logger.error(f"Manual cleanup trigger failed: {str(e)}")
            raise
    
    def get_job_status(self):
        """Get status of scheduled jobs"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "scheduler_running": self.is_running,
            "jobs": jobs
        }


# Global scheduler instance
scheduler_service = SchedulerService() 
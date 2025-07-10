"""
Cleanup Service für automatische Bereinigung abgelaufener Angebote
Verwendet die offer_valid_until Felder zur intelligenten Datenbankbereinigung
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import async_session_maker
from ..models.database_models import DatabaseProduct

logger = logging.getLogger(__name__)

class CleanupService:
    """Service für die Bereinigung abgelaufener Produktdaten"""
    
    def __init__(self):
        self.logger = logger
    
    async def cleanup_expired_offers(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Bereinigt abgelaufene Angebote basierend auf offer_valid_until
        
        Args:
            dry_run: Wenn True, nur Analyse ohne tatsächliche Löschung
            
        Returns:
            Dict mit Statistiken über gefundene/gelöschte Produkte
        """
        try:
            current_date = datetime.now().date().strftime('%Y-%m-%d')
            
            try:
                async with async_session_maker() as db:
                    # Finde abgelaufene Angebote
                    from sqlalchemy import select
                    expired_query = select(DatabaseProduct).filter(
                        and_(
                            DatabaseProduct.offer_valid_until.is_not(None),
                            DatabaseProduct.offer_valid_until < current_date,
                            DatabaseProduct.deleted_at.is_(None)  # Noch nicht gelöscht
                        )
                    )
                    
                    result = await db.execute(expired_query)
                    expired_products = result.scalars().all()
            except Exception as db_error:
                # Fallback für fehlende Datenbankverbindung
                self.logger.warning(f"Datenbank nicht verfügbar: {db_error}")
                return {
                    "analysis_date": current_date,
                    "total_expired_found": 0,
                    "expired_by_store": {},
                    "expired_products": [],
                    "action_taken": "dry_run",
                    "error": "Database not available - using mock data",
                    "note": "Database connection failed. Please check database configuration."
                }
                
                # Analysiere Ergebnisse
                stats = {
                    "analysis_date": current_date,
                    "total_expired_found": len(expired_products),
                    "expired_by_store": {},
                    "expired_products": [],
                    "action_taken": "dry_run" if dry_run else "deleted"
                }
                
                # Gruppiere nach Store
                for product in expired_products:
                    store_name = product.store.name if product.store else "Unknown"
                    if store_name not in stats["expired_by_store"]:
                        stats["expired_by_store"][store_name] = 0
                    stats["expired_by_store"][store_name] += 1
                    
                    # Sammle Produktdetails
                    stats["expired_products"].append({
                        "id": product.id,
                        "name": product.name,
                        "store": store_name,
                        "price": float(product.price) if product.price else None,
                        "offer_valid_until": product.offer_valid_until,
                        "availability_text": product.availability_text,
                        "created_at": product.created_at.isoformat()
                    })
                
                # Tatsächliche Löschung (Soft Delete)
                if not dry_run and expired_products:
                    current_timestamp = datetime.now()
                    for product in expired_products:
                        product.deleted_at = current_timestamp
                        product.availability = False
                    
                    await db.commit()
                    stats["deleted_count"] = len(expired_products)
                    self.logger.info(f"✅ {len(expired_products)} abgelaufene Angebote als gelöscht markiert")
                else:
                    stats["deleted_count"] = 0
                    if expired_products:
                        self.logger.info(f"🔍 {len(expired_products)} abgelaufene Angebote gefunden (Dry Run)")
                
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Angebots-Bereinigung: {e}")
            return {
                "error": str(e),
                "analysis_date": current_date,
                "total_expired_found": 0
            }
    
    async def cleanup_old_products(self, days_old: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """
        Bereinigt alte Produkte ohne Angebots-Enddatum
        
        Args:
            days_old: Produkte älter als X Tage löschen
            dry_run: Wenn True, nur Analyse ohne tatsächliche Löschung
            
        Returns:
            Dict mit Statistiken
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            async with async_session_maker() as db:
                # Finde alte Produkte ohne Enddatum
                from sqlalchemy import select
                old_query = select(DatabaseProduct).filter(
                    and_(
                        DatabaseProduct.created_at < cutoff_date,
                        or_(
                            DatabaseProduct.offer_valid_until.is_(None),
                            DatabaseProduct.offer_valid_until == ""
                        ),
                        DatabaseProduct.deleted_at.is_(None)
                    )
                )
                
                result = await db.execute(old_query)
                old_products = result.scalars().all()
                
                stats = {
                    "cutoff_date": cutoff_date.isoformat(),
                    "days_old_threshold": days_old,
                    "total_old_found": len(old_products),
                    "old_by_store": {},
                    "action_taken": "dry_run" if dry_run else "deleted"
                }
                
                # Gruppiere nach Store
                for product in old_products:
                    store_name = product.store.name if product.store else "Unknown"
                    if store_name not in stats["old_by_store"]:
                        stats["old_by_store"][store_name] = 0
                    stats["old_by_store"][store_name] += 1
                
                # Tatsächliche Löschung
                if not dry_run and old_products:
                    current_timestamp = datetime.now()
                    for product in old_products:
                        product.deleted_at = current_timestamp
                        product.availability = False
                    
                    await db.commit()
                    stats["deleted_count"] = len(old_products)
                    self.logger.info(f"✅ {len(old_products)} alte Produkte als gelöscht markiert")
                else:
                    stats["deleted_count"] = 0
                    if old_products:
                        self.logger.info(f"🔍 {len(old_products)} alte Produkte gefunden (Dry Run)")
                
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Produkt-Bereinigung: {e}")
            return {
                "error": str(e),
                "cutoff_date": cutoff_date.isoformat(),
                "total_old_found": 0
            }
    
    async def get_cleanup_statistics(self) -> Dict[str, Any]:
        """
        Liefert Statistiken über bereinigungs-relevante Produkte
        
        Returns:
            Dict mit verschiedenen Statistiken
        """
        try:
            current_date = datetime.now().date().strftime('%Y-%m-%d')
            
            async with async_session_maker() as db:
                from sqlalchemy import select, func
                
                # Gesamtanzahl aktiver Produkte
                total_active_query = select(func.count(DatabaseProduct.id)).filter(
                    DatabaseProduct.deleted_at.is_(None)
                )
                result = await db.execute(total_active_query)
                total_active = result.scalar()
                
                # Produkte mit Enddatum
                with_end_date_query = select(func.count(DatabaseProduct.id)).filter(
                    and_(
                        DatabaseProduct.offer_valid_until.is_not(None),
                        DatabaseProduct.offer_valid_until != "",
                        DatabaseProduct.deleted_at.is_(None)
                    )
                )
                result = await db.execute(with_end_date_query)
                with_end_date = result.scalar()
                
                # Abgelaufene Angebote
                expired_offers_query = select(func.count(DatabaseProduct.id)).filter(
                    and_(
                        DatabaseProduct.offer_valid_until.is_not(None),
                        DatabaseProduct.offer_valid_until < current_date,
                        DatabaseProduct.deleted_at.is_(None)
                    )
                )
                result = await db.execute(expired_offers_query)
                expired_offers = result.scalar()
                
                # Bald ablaufende Angebote (nächste 7 Tage)
                expiring_soon_date = (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')
                expiring_soon_query = select(func.count(DatabaseProduct.id)).filter(
                    and_(
                        DatabaseProduct.offer_valid_until.is_not(None),
                        DatabaseProduct.offer_valid_until <= expiring_soon_date,
                        DatabaseProduct.offer_valid_until >= current_date,
                        DatabaseProduct.deleted_at.is_(None)
                    )
                )
                result = await db.execute(expiring_soon_query)
                expiring_soon = result.scalar()
                
                # Gelöschte Produkte
                deleted_products_query = select(func.count(DatabaseProduct.id)).filter(
                    DatabaseProduct.deleted_at.is_not(None)
                )
                result = await db.execute(deleted_products_query)
                deleted_products = result.scalar()
                
                return {
                    "analysis_date": current_date,
                    "total_active_products": total_active,
                    "products_with_end_date": with_end_date,
                    "products_without_end_date": total_active - with_end_date,
                    "expired_offers": expired_offers,
                    "expiring_soon_offers": expiring_soon,
                    "deleted_products": deleted_products,
                    "cleanup_recommendations": {
                        "immediate_cleanup_candidates": expired_offers,
                        "requires_attention": expiring_soon,
                        "coverage": f"{(with_end_date / total_active * 100):.1f}%" if total_active > 0 else "0%"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Statistik-Erstellung: {e}")
            return {
                "error": str(e),
                "analysis_date": current_date
            }

# Singleton Instanz
cleanup_service = CleanupService() 
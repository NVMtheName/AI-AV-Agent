"""
Asset mapping and enrichment layer.

Enriches events with additional asset information from:
- Asset database/CSV
- IP -> Room mappings
- Hostname -> Room mappings
- Historical asset data

This is a deterministic code-based enrichment (no AI inference).
"""

import json
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from ingestion_models import UnifiedEvent, AssetInfo


logger = logging.getLogger(__name__)


class AssetEnricher:
    """
    Enriches events with asset information from various sources.

    Sources:
    1. Asset database (CSV or JSON)
    2. IP -> Room mapping
    3. Hostname -> Location mapping
    4. In-memory cache for performance
    """

    def __init__(self, asset_db_path: Optional[Path] = None, ip_room_map_path: Optional[Path] = None):
        """
        Initialize asset enricher.

        Args:
            asset_db_path: Path to asset database (CSV or JSON)
            ip_room_map_path: Path to IP -> Room mapping file (CSV)
        """
        self.asset_db: Dict[str, Dict[str, Any]] = {}
        self.ip_to_room: Dict[str, str] = {}
        self.hostname_to_asset: Dict[str, Dict[str, Any]] = {}

        if asset_db_path and asset_db_path.exists():
            self._load_asset_db(asset_db_path)

        if ip_room_map_path and ip_room_map_path.exists():
            self._load_ip_room_map(ip_room_map_path)

    def _load_asset_db(self, path: Path):
        """
        Load asset database from CSV or JSON.

        Expected CSV columns:
        - asset_id
        - asset_type
        - make
        - model
        - serial
        - ip
        - mac
        - hostname
        - room
        - building
        - floor
        - site
        - firmware_version
        """
        logger.info(f"Loading asset database from {path}")

        if path.suffix.lower() == '.json':
            self._load_asset_json(path)
        elif path.suffix.lower() == '.csv':
            self._load_asset_csv(path)
        else:
            logger.warning(f"Unsupported asset database format: {path.suffix}")

    def _load_asset_json(self, path: Path):
        """Load asset DB from JSON"""
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                for asset in data:
                    asset_id = asset.get('asset_id')
                    if asset_id:
                        self.asset_db[asset_id] = asset
                        # Index by IP and hostname too
                        if asset.get('ip'):
                            self.asset_db[asset['ip']] = asset
                        if asset.get('hostname'):
                            self.hostname_to_asset[asset['hostname'].lower()] = asset
            else:
                self.asset_db = data

        logger.info(f"Loaded {len(self.asset_db)} assets from JSON")

    def _load_asset_csv(self, path: Path):
        """Load asset DB from CSV"""
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset_id = row.get('asset_id')
                if asset_id:
                    self.asset_db[asset_id] = dict(row)
                    # Index by IP and hostname
                    if row.get('ip'):
                        self.asset_db[row['ip']] = dict(row)
                    if row.get('hostname'):
                        self.hostname_to_asset[row['hostname'].lower()] = dict(row)

        logger.info(f"Loaded {len(self.asset_db)} assets from CSV")

    def _load_ip_room_map(self, path: Path):
        """
        Load IP -> Room mapping from CSV.

        Expected columns: ip, room
        """
        logger.info(f"Loading IP->Room mapping from {path}")

        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip = row.get('ip')
                room = row.get('room')
                if ip and room:
                    self.ip_to_room[ip] = room

        logger.info(f"Loaded {len(self.ip_to_room)} IP->Room mappings")

    def enrich_event(self, event: UnifiedEvent) -> UnifiedEvent:
        """
        Enrich an event with asset information.

        Looks up asset by:
        1. event.asset.asset_id
        2. event.asset.ip
        3. event.asset.hostname

        Adds/updates:
        - Room, building, floor, site (if missing)
        - Asset details (make, model, serial)

        Args:
            event: Event to enrich

        Returns:
            Enriched event (modifies in place and returns)
        """

        # Try to find asset information
        asset_data = None

        # 1. Look up by asset_id
        if event.asset and event.asset.asset_id:
            asset_data = self.asset_db.get(event.asset.asset_id)

        # 2. Look up by IP
        if not asset_data and event.asset and event.asset.ip:
            asset_data = self.asset_db.get(event.asset.ip)

        # 3. Look up by hostname
        if not asset_data and event.asset and event.asset.hostname:
            asset_data = self.hostname_to_asset.get(event.asset.hostname.lower())

        # Enrich asset information
        if asset_data:
            if not event.asset:
                event.asset = AssetInfo()

            # Update asset fields if they're missing
            if not event.asset.make and asset_data.get('make'):
                event.asset.make = asset_data['make']
            if not event.asset.model and asset_data.get('model'):
                event.asset.model = asset_data['model']
            if not event.asset.serial and asset_data.get('serial'):
                event.asset.serial = asset_data['serial']
            if not event.asset.asset_type and asset_data.get('asset_type'):
                event.asset.asset_type = asset_data['asset_type']
            if not event.asset.firmware_version and asset_data.get('firmware_version'):
                event.asset.firmware_version = asset_data['firmware_version']

            # Update location if missing
            if not event.room and asset_data.get('room'):
                event.room = asset_data['room']
            if not event.building and asset_data.get('building'):
                event.building = asset_data['building']
            if not event.floor and asset_data.get('floor'):
                event.floor = asset_data['floor']
            if not event.site and asset_data.get('site'):
                event.site = asset_data['site']

        # IP -> Room mapping (if room still missing)
        if not event.room and event.asset and event.asset.ip:
            room = self.ip_to_room.get(event.asset.ip)
            if room:
                event.room = room

        return event

    def enrich_events(self, events: List[UnifiedEvent]) -> List[UnifiedEvent]:
        """
        Enrich a batch of events.

        Args:
            events: List of events

        Returns:
            List of enriched events
        """
        enriched = []
        for event in events:
            enriched.append(self.enrich_event(event))
        return enriched

    def add_asset(self, asset_id: str, asset_data: Dict[str, Any]):
        """
        Add or update an asset in the in-memory database.

        Args:
            asset_id: Asset identifier
            asset_data: Asset information dict
        """
        self.asset_db[asset_id] = asset_data

        # Index by IP and hostname
        if asset_data.get('ip'):
            self.asset_db[asset_data['ip']] = asset_data
        if asset_data.get('hostname'):
            self.hostname_to_asset[asset_data['hostname'].lower()] = asset_data

        logger.debug(f"Added asset {asset_id} to enrichment database")

    def get_asset(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Look up asset by ID, IP, or hostname.

        Args:
            identifier: Asset ID, IP, or hostname

        Returns:
            Asset data dict or None
        """
        # Try direct lookup
        asset = self.asset_db.get(identifier)
        if asset:
            return asset

        # Try hostname lookup
        asset = self.hostname_to_asset.get(identifier.lower())
        return asset

    def get_room_assets(self, room: str) -> List[Dict[str, Any]]:
        """
        Get all assets in a specific room.

        Args:
            room: Room identifier

        Returns:
            List of asset data dicts
        """
        assets = []
        for asset in self.asset_db.values():
            if isinstance(asset, dict) and asset.get('room') == room:
                # Avoid duplicates (since we index by multiple keys)
                if asset not in assets:
                    assets.append(asset)
        return assets

    def stats(self) -> Dict[str, int]:
        """Get enrichment statistics"""
        return {
            'total_assets': len(set(
                asset.get('asset_id') for asset in self.asset_db.values()
                if isinstance(asset, dict) and asset.get('asset_id')
            )),
            'ip_mappings': len(self.ip_to_room),
            'hostname_mappings': len(self.hostname_to_asset),
        }

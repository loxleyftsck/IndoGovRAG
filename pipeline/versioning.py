"""
Document Versioning Utility

Tracks document versions and handles version-related operations:
  - Detect new versions of existing documents
  - Mark old versions as superseded
  - Provide version history for documents
  - Add superseding warnings to search results
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Data Classes
# ------------------------------------------------------------------------------

@dataclass
class DocumentVersion:
    """Represents a single version of a document."""
    version: str
    hash: str
    processed_at: str
    doc_id: str
    status: str = "active"  # "active" | "superseded"
    superseded_by: Optional[str] = None
    superseded_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "hash": self.hash,
            "processed_at": self.processed_at,
            "doc_id": self.doc_id,
            "status": self.status,
            "superseded_by": self.superseded_by,
            "superseded_at": self.superseded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DocumentVersion":
        return cls(
            version=d["version"],
            hash=d["hash"],
            processed_at=d["processed_at"],
            doc_id=d.get("doc_id", ""),
            status=d.get("status", "active"),
            superseded_by=d.get("superseded_by"),
            superseded_at=d.get("superseded_at"),
        )


@dataclass
class VersionRegistry:
    """Registry tracking all versions of all documents."""
    versions: dict[str, list[DocumentVersion]] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def add_version(self, doc_id: str, version: DocumentVersion):
        """Add a new version for a document."""
        if doc_id not in self.versions:
            self.versions[doc_id] = []
        self.versions[doc_id].append(version)

    def get_latest(self, doc_id: str) -> Optional[DocumentVersion]:
        """Get the latest version of a document."""
        if doc_id not in self.versions or not self.versions[doc_id]:
            return None
        return self.versions[doc_id][-1]

    def get_all_versions(self, doc_id: str) -> list[DocumentVersion]:
        """Get all versions of a document."""
        return self.versions.get(doc_id, [])

    def mark_superseded(self, doc_id: str, superseded_by: str):
        """Mark the latest version of a document as superseded."""
        if doc_id not in self.versions or not self.versions[doc_id]:
            return

        latest = self.versions[doc_id][-1]
        latest.status = "superseded"
        latest.superseded_by = superseded_by
        latest.superseded_at = datetime.utcnow().isoformat() + "Z"

    def is_superseded(self, doc_id: str) -> bool:
        """Check if the latest version of a document is superseded."""
        latest = self.get_latest(doc_id)
        return latest is not None and latest.status == "superseded"


# ------------------------------------------------------------------------------
# Version Manager
# ------------------------------------------------------------------------------

class VersionManager:
    """
    Manages document versions across the pipeline.

    Features:
      - Detect when a new version of a document is available
      - Mark old versions as superseded
      - Provide version metadata for search results
      - Persist version history to disk
    """

    def __init__(self, registry_path: str = "data/pipeline/version_registry.json"):
        """
        Initialize version manager.

        Args:
            registry_path: Path to persist version registry
        """
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.registry = self._load_registry()

        logger.info("[INIT] Version manager ready")
        logger.info("  Tracked documents: %d", len(self.registry.versions))

    def _load_registry(self) -> VersionRegistry:
        """Load version registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)

                registry = VersionRegistry(updated_at=data.get("updated_at", ""))

                for doc_id, version_list in data.get("versions", {}).items():
                    for v in version_list:
                        registry.versions.setdefault(doc_id, [])
                        registry.versions[doc_id].append(DocumentVersion.from_dict(v))

                return registry
            except Exception as e:
                logger.warning("[WARN] Could not load version registry: %s", e)

        return VersionRegistry()

    def save(self):
        """Persist version registry to disk."""
        data = {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "versions": {
                doc_id: [v.to_dict() for v in versions]
                for doc_id, versions in self.registry.versions.items()
            },
        }

        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.debug("[SAVE] Version registry saved")

    def register_document(
        self,
        doc_id: str,
        content_hash: str,
        metadata: Optional[dict] = None,
    ) -> tuple[str, bool]:
        """
        Register a document and determine if it's new or an update.

        Args:
            doc_id: Document identifier
            content_hash: Hash of document content
            metadata: Optional document metadata

        Returns:
            (version_string, is_new_document) tuple.
            is_new_document is True only for brand-new documents (not updates).
        """
        existing = self.registry.get_latest(doc_id)

        if existing is None:
            # New document
            version = DocumentVersion(
                version="1.0",
                hash=content_hash,
                processed_at=datetime.utcnow().isoformat() + "Z",
                doc_id=doc_id,
                status="active",
            )
            self.registry.add_version(doc_id, version)
            self.save()
            return "1.0", True  # is_new=True

        if existing.hash == content_hash:
            # No change (same content already indexed)
            return existing.version, False  # is_new=False (not new)

        # Content changed — this is an update/new version
        try:
            new_version_num = str(float(existing.version) + 0.1)
        except ValueError:
            new_version_num = "1.1"

        # Mark old version as superseded
        self.registry.mark_superseded(doc_id, f"{doc_id}_v{new_version_num}")

        # Add new version
        new_version = DocumentVersion(
            version=new_version_num,
            hash=content_hash,
            processed_at=datetime.utcnow().isoformat() + "Z",
            doc_id=doc_id,
            status="active",
        )
        self.registry.add_version(doc_id, new_version)
        self.save()

        return new_version_num, False  # is_new=False (it's an update, not new)

    def get_superseding_warning(self, doc_id: str) -> Optional[str]:
        """
        Get a human-readable warning message for superseded documents.

        Args:
            doc_id: Document ID

        Returns:
            Warning message or None if not superseded
        """
        if not self.registry.is_superseded(doc_id):
            return None

        latest = self.registry.get_latest(doc_id)
        if latest and latest.superseded_by:
            return (
                f"⚠️  Dokumen ini sudah tidak berlaku dan digantikan oleh "
                f"{latest.superseded_by}"
            )

        return "⚠️  Dokumen ini sudah tidak berlaku"

    def get_version_info(self, doc_id: str) -> dict:
        """
        Get full version information for a document.

        Returns:
            Dict with version history and status
        """
        all_versions = self.registry.get_all_versions(doc_id)

        if not all_versions:
            return {"exists": False}

        return {
            "exists": True,
            "total_versions": len(all_versions),
            "current_version": all_versions[-1].version,
            "is_superseded": self.registry.is_superseded(doc_id),
            "superseded_by": all_versions[-1].superseded_by,
            "versions": [v.to_dict() for v in all_versions],
        }

    def get_active_documents(self) -> set[str]:
        """Get set of all active document IDs."""
        active = set()

        for doc_id, versions in self.registry.versions.items():
            if versions and versions[-1].status == "active":
                active.add(doc_id)

        return active

    def get_stats(self) -> dict:
        """Get version manager statistics."""
        total_docs = len(self.registry.versions)
        superseded = sum(
            1 for versions in self.registry.versions.values()
            if versions and versions[-1].status == "superseded"
        )

        return {
            "total_documents": total_docs,
            "active_documents": total_docs - superseded,
            "superseded_documents": superseded,
            "registry_path": str(self.registry_path),
        }


# ------------------------------------------------------------------------------
# Search Result Enricher
# ------------------------------------------------------------------------------

def enrich_search_result(result: dict) -> dict:
    """
    Add superseding warning and version info to a search result.

    Args:
        result: Search result dict (must include metadata with doc_id)

    Returns:
        Enriched result dict with warning fields
    """
    doc_id = result.get("metadata", {}).get("doc_id", "")

    if not doc_id:
        return result

    version_manager = VersionManager()
    warning = version_manager.get_superseding_warning(doc_id)

    if warning:
        result["superseded_warning"] = warning
        result["is_superseded"] = True
    else:
        result["superseded_warning"] = None
        result["is_superseded"] = False

    return result


def enrich_search_results(results: list[dict]) -> list[dict]:
    """Enrich multiple search results."""
    return [enrich_search_result(r) for r in results]


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Document Version Manager")
    parser.add_argument("--action", choices=["stats", "history", "check"],
                        default="stats", help="Action to perform")
    parser.add_argument("--doc-id", help="Document ID for history/check")

    args = parser.parse_args()

    vm = VersionManager()

    if args.action == "stats":
        stats = vm.get_stats()
        print("\n[STAT] Version Manager Statistics")
        print("=" * 50)
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.action == "history":
        if not args.doc_id:
            print("[ERR] --doc-id required for history action")
            exit(1)

        info = vm.get_version_info(args.doc_id)
        print(f"\n[HISTORY] {args.doc_id}")
        print("=" * 50)
        for key, value in info.items():
            if key != "versions":
                print(f"  {key}: {value}")

        if info.get("versions"):
            print("\n  Version history:")
            for v in info["versions"]:
                print(f"    v{v['version']} | {v['status']} | {v['processed_at']}")
                if v.get("superseded_by"):
                    print(f"      Superseded by: {v['superseded_by']}")

    elif args.action == "check":
        if not args.doc_id:
            print("[ERR] --doc-id required for check action")
            exit(1)

        is_sup = vm.registry.is_superseded(args.doc_id)
        warning = vm.get_superseding_warning(args.doc_id)
        print(f"\n[CHECK] {args.doc_id}")
        print(f"  Is superseded: {is_sup}")
        print(f"  Warning: {warning or 'None'}")
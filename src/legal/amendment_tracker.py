"""
Amendment Tracker for IndoGovRAG
Tracks regulatory amendments and changes across versions.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_HISTORY_FILE = str(
    Path(__file__).resolve().parents[1] / ".." / "data" / "amendment_history.json"
)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AmendmentRecord:
    """Single amendment entry within a document's history."""

    amendment: str  # e.g. "PP 7/2020"
    date: str  # ISO date string YYYY-MM-DD
    changes: str | None = None
    perubahan_ke: int | None = None  # ordinal: 1=Pertama, 2=Kedua, etc.
    related_topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AmendmentHistory:
    """Full amendment history for a single regulatory document."""

    original_date: str | None = None
    amendments: list[dict[str, Any]] = field(default_factory=list)
    status: str = "Original"  # Original | Amended | Superseded
    superseded_by: str | None = None
    title: str | None = None
    issuing_body: str | None = None
    topics: list[str] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Core Tracker Class
# ---------------------------------------------------------------------------


class AmendmentTracker:
    """
    Tracks amendments to Indonesian government regulations.

    Stores data in a JSON file and provides methods to query amendment
    history, check amendment status, and find related regulations.
    """

    _instance: AmendmentTracker | None = None

    def __init__(self, history_file: str | None = None) -> None:
        self.history_file = history_file or DEFAULT_HISTORY_FILE
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load history from JSON file, creating it if it doesn't exist."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        else:
            self._ensure_dir()
            self._data = {}
            self._save()

    def _save(self) -> None:
        """Persist current state to JSON file."""
        self._ensure_dir()
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _ensure_dir(self) -> None:
        """Create parent directory of history file if needed."""
        Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(doc_id: str) -> str:
        """Canonical key for a document ID (case-insensitive)."""
        return doc_id.strip()

    @staticmethod
    def _detect_perubahan_ke(text: str) -> int | None:
        """
        Detect 'Perubahan ke-' ordinal from amendment document title.

        Returns:
            1  for "Perubahan Pertama"
            2  for "Perubahan Kedua"
            3  for "Perubahan Ketiga"
            4  for "Perubahan Keempat"
            etc.
            None if no ordinal is detected.
        """
        ordinal_map = {
            "pertama": 1,
            "kedua": 2,
            "ketiga": 3,
            "keempat": 4,
            "kelima": 5,
            "keenam": 6,
            "ketujuh": 7,
            "kedelapan": 8,
            "kesembilan": 9,
            "kesepuluh": 10,
        }
        text_lower = text.lower()
        for word, num in ordinal_map.items():
            if word in text_lower:
                return num
        # Regex fallback: "Perubahan ke-<digit>"
        m = re.search(r"perubahan\s+ke\s*[-]?\s*(\d+)", text_lower)
        if m:
            return int(m.group(1))
        return None

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def track_amendment(
        self,
        doc_id: str,
        amendment_data: dict[str, Any] | None = None,
        *,
        original_date: str | None = None,
        title: str | None = None,
        issuing_body: str | None = None,
        topics: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Register or update a regulatory document and its amendment history.

        Args:
            doc_id:          Canonical document ID, e.g. "PP 24/2018"
            amendment_data:  Dict with keys: {amendment, date, changes,
                             related_topics}. Used to record a single
                             amendment event on top of an existing doc.
            original_date:   ISO date string for the original regulation.
            title:           Full title of the regulation.
            issuing_body:    Issuing authority (e.g. "PRESIDEN").
            topics:          List of topic tags for search.
            notes:           Free-text notes.

        Returns:
            The full history entry for `doc_id` after the update.
        """
        key = self._normalise(doc_id)

        if key not in self._data:
            self._data[key] = AmendmentHistory().to_dict()

        entry = self._data[key]

        # Apply metadata on first registration
        if entry.get("original_date") is None and original_date:
            entry["original_date"] = original_date
        if entry.get("title") is None and title:
            entry["title"] = title
        if entry.get("issuing_body") is None and issuing_body:
            entry["issuing_body"] = issuing_body
        if entry.get("topics") is None and topics:
            entry["topics"] = topics
        if entry.get("notes") is None and notes:
            entry["notes"] = notes

        # Record amendment event
        if amendment_data:
            amend_id = amendment_data.get("amendment", "")
            amend_date = amendment_data.get("date", "")
            amend_changes = amendment_data.get("changes")
            amend_topics = amendment_data.get("related_topics", [])

            # Auto-detect ordinal from title if not provided
            perubahan_ke = amendment_data.get("perubahan_ke")
            if perubahan_ke is None and amend_id:
                perubahan_ke = self._detect_perubahan_ke(amend_id)

            record: dict[str, Any] = {
                "amendment": amend_id,
                "date": amend_date,
                "changes": amend_changes,
                "perubahan_ke": perubahan_ke,
                "related_topics": amend_topics,
            }
            entry["amendments"].append(record)
            entry["status"] = "Amended"

        self._save()
        return entry

    def get_amendment_history(self, doc_id: str) -> dict[str, Any] | None:
        """
        Return the full amendment history for `doc_id`.

        Returns None if the document has never been registered.
        """
        return self._data.get(self._normalise(doc_id))

    def check_if_amended(self, doc_id: str) -> bool:
        """Return True if `doc_id` has any recorded amendments."""
        entry = self._data.get(self._normalise(doc_id))
        return entry is not None and len(entry.get("amendments", [])) > 0

    def get_latest_version(self, doc_id: str) -> dict[str, Any] | None:
        """
        Return the most recent amendment record for `doc_id`.

        Returns the original document metadata if no amendments exist.
        Returns None if `doc_id` is completely unknown.
        """
        entry = self._data.get(self._normalise(doc_id))
        if entry is None:
            return None
        amendments = entry.get("amendments", [])
        if amendments:
            return amendments[-1]
        return {
            "amendment": doc_id,
            "date": entry.get("original_date", ""),
            "changes": None,
            "perubahan_ke": None,
            "related_topics": entry.get("topics", []),
        }

    def find_related_amendments(
        self, search_term: str, *, doc_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Find all amendment records matching `search_term`.

        Search covers:
          - document IDs
          - amendment IDs
          - change descriptions
          - topic tags
          - regulation titles

        Args:
            search_term: Text to search for (case-insensitive).
            doc_id:       Optional — restrict results to a specific document.

        Returns:
            List of matching amendment record dicts, each enriched with
            the parent ``doc_id`` key.
        """
        term = search_term.lower()
        results: list[dict[str, Any]] = []

        scope = {self._normalise(doc_id): self._data[self._normalise(doc_id)]} \
            if doc_id else self._data

        for parent_id, entry in scope.items():
            for record in entry.get("amendments", []):
                if any(
                    term in str(v).lower()
                    for v in [
                        record.get("amendment", ""),
                        record.get("changes", ""),
                        record.get("related_topics", []),
                        entry.get("title", ""),
                    ]
                ):
                    enriched = dict(record)
                    enriched["doc_id"] = parent_id
                    enriched["doc_title"] = entry.get("title")
                    results.append(enriched)

        return results

    def get_frequently_updated(
        self, *, min_amendments: int = 2
    ) -> list[dict[str, Any]]:
        """
        Return documents that have been amended at least `min_amendments` times.

        Useful for alerting users about regulations that change often.
        """
        return [
            {
                "doc_id": doc_id,
                "title": entry.get("title"),
                "amendment_count": len(entry.get("amendments", [])),
                "latest_amendment": entry["amendments"][-1]
                if entry.get("amendments")
                else None,
            }
            for doc_id, entry in self._data.items()
            if len(entry.get("amendments", [])) >= min_amendments
        ]

    def mark_superseded(self, doc_id: str, superseded_by: str) -> None:
        """Mark a regulation as superseded by another regulation."""
        key = self._normalise(doc_id)
        if key in self._data:
            self._data[key]["status"] = "Superseded"
            self._data[key]["superseded_by"] = superseded_by
            self._save()

    def list_all(self) -> list[str]:
        """Return all registered document IDs."""
        return list(self._data.keys())


# ---------------------------------------------------------------------------
# Module-level convenience functions (singleton tracker)
# ---------------------------------------------------------------------------

_tracker: AmendmentTracker | None = None


def get_tracker(history_file: str | None = None) -> AmendmentTracker:
    """Return the shared AmendmentTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = AmendmentTracker(history_file)
    return _tracker


def track_amendment(doc_id: str, amendment_data: dict[str, Any]) -> dict[str, Any]:
    """Convenience wrapper around ``AmendmentTracker.track_amendment``."""
    return get_tracker().track_amendment(doc_id, amendment_data)


def get_amendment_history(doc_id: str) -> dict[str, Any] | None:
    """Convenience wrapper around ``AmendmentTracker.get_amendment_history``."""
    return get_tracker().get_amendment_history(doc_id)


def check_if_amended(doc_id: str) -> bool:
    """Convenience wrapper around ``AmendmentTracker.check_if_amended``."""
    return get_tracker().check_if_amended(doc_id)


def get_latest_version(doc_id: str) -> dict[str, Any] | None:
    """Convenience wrapper around ``AmendmentTracker.get_latest_version``."""
    return get_tracker().get_latest_version(doc_id)


def find_related_amendments(search_term: str) -> list[dict[str, Any]]:
    """Convenience wrapper around ``AmendmentTracker.find_related_amendments``."""
    return get_tracker().find_related_amendments(search_term)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_amendment_report(doc_id: str) -> str:
    """
    Produce a human-readable amendment report for `doc_id`.

    Example output matches the spec::

        REGULASI: PP 24/2018 tentang OSS
        STATUS: Diubah oleh PP 7/2020 dan PP 21/2022

        HISTORY:
        1. PP 24/2018 (Original) - 13 Juni 2018
        2. PP 7/2020 (Perubahan Pertama) - 13 Juli 2020
           └── Perubahan: Penyederhanaan perizinan mikro & kecil
        3. PP 21/2022 (Perubahan Kedua) - 30 Juni 2022
           └── Perubahan: Integrasi dengan sistem NIB

        CURRENT VERSION: PP 21/2022 (Latest)
    """
    tracker = get_tracker()
    entry = tracker.get_amendment_history(doc_id)

    if entry is None:
        return f"Dokumen '{doc_id}' tidak ditemukan dalam tracker."

    amendments = entry.get("amendments", [])
    title = entry.get("title", "")
    status = entry.get("status", "Original")
    original_date = entry.get("original_date", "")

    # Build header
    header_id = doc_id
    if title:
        header_id += f" tentang {title}"
    lines = [f"REGULASI: {header_id}"]

    # Status line
    if amendments:
        amend_names = [a["amendment"] for a in amendments]
        status_str = " dan ".join(amend_names)
        lines.append(f"STATUS: Diubah oleh {status_str}")
    else:
        lines.append("STATUS: Original (belum diubah)")

    lines.append("")
    lines.append("HISTORY:")

    # Original
    orig_label = f"{doc_id} (Original)"
    if original_date:
        lines.append(f"1. {orig_label} - {original_date}")
    else:
        lines.append(f"1. {orig_label}")

    # Amendments
    for i, amend in enumerate(amendments, start=2):
        amend_id = amend.get("amendment", "")
        amend_date = amend.get("date", "")
        perubahan_ke = amend.get("perubahan_ke")
        changes = amend.get("changes")

        if perubahan_ke:
            ordinal_label = _ordinal_label(perubahan_ke)
            label = f"{amend_id} (Perubahan {ordinal_label})"
        else:
            label = amend_id

        if amend_date:
            lines.append(f"{i}. {label} - {amend_date}")
        else:
            lines.append(f"{i}. {label}")

        if changes:
            lines.append(f"   └── Perubahan: {changes}")

    # Current version
    lines.append("")
    if amendments:
        latest = amendments[-1]["amendment"]
        lines.append(f"CURRENT VERSION: {latest} (Latest)")
    else:
        lines.append(f"CURRENT VERSION: {doc_id} (Original)")

    return "\n".join(lines)


def _ordinal_label(n: int) -> str:
    """Return the Indonesian ordinal word for 1-10."""
    labels = {
        1: "Pertama",
        2: "Kedua",
        3: "Ketiga",
        4: "Keempat",
        5: "Kelima",
        6: "Keenam",
        7: "Ketujuh",
        8: "Kedelapan",
        9: "Kesembilan",
        10: "Kesepuluh",
    }
    return labels.get(n, f"Ke-{n}")


# ---------------------------------------------------------------------------
# Demo / Test
# ---------------------------------------------------------------------------

def demo() -> None:
    """Demonstrate the AmendmentTracker with sample data."""
    print("=" * 60)
    print("AMENDMENT TRACKER — Demo")
    print("=" * 60)

    tracker = get_tracker()

    # --- Register PP 24/2018 original ---
    tracker.track_amendment(
        "PP 24/2018",
        original_date="2018-06-13",
        title="OSS",
        issuing_body="PRESIDEN",
        topics=["oss", "perizinan", "oss"],
    )

    # --- Amendments to PP 24/2018 ---
    tracker.track_amendment(
        "PP 24/2018",
        amendment_data={
            "amendment": "PP 7/2020",
            "date": "2020-07-13",
            "changes": "Simplified perizinan for mikro",
            "related_topics": ["oss", "mikro"],
        },
    )

    tracker.track_amendment(
        "PP 24/2018",
        amendment_data={
            "amendment": "PP 21/2022",
            "date": "2022-06-30",
            "changes": "Integrasi dengan sistem NIB",
            "related_topics": ["nib", "oss"],
        },
    )

    # --- Register UU 11/2020 ---
    tracker.track_amendment(
        "UU 11/2020",
        original_date="2020-05-21",
        title="Cipta Kerja",
        issuing_body="PRESIDEN",
        topics=["ketenagakerjaan", "usaha"],
    )

    tracker.track_amendment(
        "UU 11/2020",
        amendment_data={
            "amendment": "UU 6/2023",
            "date": "2023-03-31",
            "changes": "Penjelasan Omnibus Law dan corrected clauses",
            "related_topics": ["omnibus", "cipta-kerja"],
        },
    )

    # --- Register frequently amended regulation ---
    tracker.track_amendment(
        "PP 5/2021",
        original_date="2021-02-02",
        title="OSS Implementing",
        issuing_body="PRESIDEN",
        topics=["oss"],
    )
    for i, year in enumerate([2022, 2023, 2024], start=1):
        tracker.track_amendment(
            "PP 5/2021",
            amendment_data={
                "amendment": f"PP {i + 50}/{year}",
                "date": f"{year}-0{i+1}-15",
                "changes": f"Amendment #{i} for PP 5/2021",
                "related_topics": ["oss"],
            },
        )

    # --- Print reports ---
    print(format_amendment_report("PP 24/2018"))
    print()
    print(format_amendment_report("UU 11/2020"))
    print()

    # --- Frequently updated ---
    print("=" * 60)
    print("FREQUENTLY UPDATED REGULATIONS (>= 2 amendments)")
    print("=" * 60)
    for item in tracker.get_frequently_updated(min_amendments=2):
        print(
            f"  * {item['doc_id']} — {item['amendment_count']} amendments  "
            f"(latest: {item['latest_amendment']['amendment']})"
        )
    print()

    # --- Search ---
    print("=" * 60)
    print("SEARCH: 'oss'")
    print("=" * 60)
    for r in tracker.find_related_amendments("oss"):
        print(f"  [{r['doc_id']}] {r['amendment']} — {r.get('changes')}")
    print()

    # --- check_if_amended ---
    print("check_if_amended('PP 24/2018'):", check_if_amended("PP 24/2018"))
    print("check_if_amended('UU 11/2020'):", check_if_amended("UU 11/2020"))
    print("check_if_amended('UNKNOWN'):", check_if_amended("UNKNOWN"))
    print()

    # --- get_latest_version ---
    print("get_latest_version('PP 24/2018'):", get_latest_version("PP 24/2018"))
    print()
    print("History file:", tracker.history_file)


if __name__ == "__main__":
    demo()

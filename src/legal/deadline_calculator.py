"""
Legal Deadline Calculator - IndoGovRAG
Perhitungan hari kerja dengan kalender libur nasional Indonesia.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Union

# =============================================================================
# KALENDER LIBUR NASIONAL INDONESIA 2024-2026
# =============================================================================

HOLIDAYS: dict[int, list[str]] = {
    2024: [
        "2024-01-01",   # Tahun Baru 2024
        "2024-02-08",  # Isra Mi'raj 1445H
        "2024-02-10",  # Imlek 2575 Kongzili
        "2024-03-11",  # Hari Raya Nyepi 1946
        "2024-03-29",  # Hari Raya Suci Hinduism - Nyepi
        "2024-03-31",  # Hari Raya Idulfitri 1445H (1 Syawal)
        "2024-04-01",  # Hari Raya Idulfitri 1445H (2 Syawal)
        "2024-04-10",  # Hari Wafat Isa Al-Masih (Wed Apr 10)
        "2024-05-01",  # Hari Buruh Internasional
        "2024-05-09",  # Hari Raya Waisak 2568 (Thu May 9 - Vaisakha Bucha in Buddhism)
        "2024-05-10",  # Kenaikan Isa Al-Masih (Fri May 10)
        "2024-06-01",  # Hari Lahir Pancasila
        "2024-06-17",  # Hari Raya Qurban 1445H
        "2024-08-17",  # Hari Kemerdekaan RI ke-79
        "2024-09-01",  # Maulid Nabi 1446H
        "2024-12-25",  # Hari Natal
    ],
    2025: [
        "2025-01-01",   # Tahun Baru 2025
        "2025-01-27",  # Isra Mi'raj 1446H
        "2025-01-29",  # Tahun Baru Imlek 2576
        "2025-03-14",  # Hari Raya Nyepi 1947
        "2025-03-30",  # Awal Ramadan 1446H (estimasi)
        "2025-03-31",  # Hari Raya Idulfitri 1446H - 1 Syawal (estimasi)
        "2025-04-01",  # Hari Raya Idulfitri 1446H - 2 Syawal (estimasi)
        "2025-04-09",  # Hari Wafat Isa Al-Masih
        "2025-05-01",  # Hari Buruh Internasional
        "2025-05-11",  # Hari Raya Waisak 2569
        "2025-05-29",  # Kenaikan Isa Al-Masih
        "2025-06-01",  # Hari Lahir Pancasila
        "2025-06-07",  # Hari Raya Qurban 1446H
        "2025-08-17",  # Hari Kemerdekaan RI ke-80
        "2025-09-05",  # Maulid Nabi 1447H
        "2025-12-25",  # Hari Natal
    ],
    2026: [
        "2026-01-01",   # Tahun Baru 2026
        "2026-01-15",  # Isra Mi'raj 1447H
        "2026-02-17",  # Tahun Baru Imlek 2577
        "2026-03-04",  # Hari Raya Nyepi 1948
        "2026-03-20",  # Awal Ramadan 1447H (estimasi)
        "2026-03-21",  # Hari Raya Idulfitri 1447H - 1 Syawal (estimasi)
        "2026-03-22",  # Hari Raya Idulfitri 1447H - 2 Syawal (estimasi)
        "2026-04-01",  # Hari Wafat Isa Al-Masih
        "2026-05-01",  # Hari Buruh Internasional
        "2026-05-10",  # Hari Raya Waisak 2570
        "2026-05-28",  # Kenaikan Isa Al-Masih
        "2026-06-01",  # Hari Lahir Pancasila
        "2026-06-27",  # Hari Raya Qurban 1447H
        "2026-08-17",  # Hari Kemerdekaan RI ke-81
        "2026-08-25",  # Maulid Nabi 1448H
        "2026-12-25",  # Hari Natal
    ],
}


# =============================================================================
# DATACLASS
# =============================================================================

@dataclass
class DeadlineResult:
    """Result dari perhitungan deadline hari kerja."""
    start_date: str
    target_date: str
    business_days: int
    total_days: int
    excluded_weekends: int
    excluded_holidays: list[str]
    timeline: list[dict]
    is_business_day_target: bool

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# =============================================================================
# PARSING HELPERS
# =============================================================================

def _parse_date(value: Union[str, date, datetime]) -> date:
    """Konversi input ke objek date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Tidak dapat mengurai tanggal: {value!r}")


def _date_str(d: date) -> str:
    """Format date ke string Indonesia."""
    days_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months_id = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{d.strftime('%d')} {months_id[d.month]} {d.year} ({days_id[d.weekday()]})"


def _date_str_short(d: date) -> str:
    """Format date pendek."""
    return d.strftime("%Y-%m-%d")


# =============================================================================
# HOLIDAY LOOKUP
# =============================================================================

def _get_holiday_set(year: int | None = None) -> set[date]:
    """Kembalikan set tanggal hari libur sebagai date objects."""
    result = set()
    if year is not None:
        years = [year]
    else:
        years = list(HOLIDAYS.keys())
    for y in years:
        for hs in HOLIDAYS.get(y, []):
            try:
                result.add(datetime.strptime(hs, "%Y-%m-%d").date())
            except ValueError:
                continue
    return result


def get_holidays(year: int | None = None) -> list[str]:
    """Kembalikan daftar string tanggal libur."""
    all_dates: list[str] = []
    if year is not None:
        years = [year]
    else:
        years = list(HOLIDAYS.keys())
    for y in years:
        all_dates.extend(HOLIDAYS.get(y, []))
    return sorted(all_dates)


# =============================================================================
# CORE BUSINESS DAY FUNCTIONS
# =============================================================================

def is_business_day(value: Union[str, date, datetime]) -> bool:
    """
    Periksa apakah tanggal adalah hari kerja.

    Args:
        value: Tanggal dalam format string ('YYYY-MM-DD'), date, atau datetime.

    Returns:
        True jika hari kerja, False jika weekend atau hari libur nasional.

    Contoh:
        >>> is_business_day("2024-05-01")   # Hari Buruh -> False
        >>> is_business_day("2024-05-02")  # BukanLibur -> True
        >>> is_business_day(date(2024, 5, 4))  # Sabtu -> False
    """
    d = _parse_date(value)

    # exclude weekends (Sabtu=5, Minggu=6)
    if d.weekday() >= 5:
        return False

    # exclude national holidays
    holiday_set = _get_holiday_set(d.year)
    if d in holiday_set:
        return False

    return True


def get_next_business_day(value: Union[str, date, datetime]) -> date:
    """
    Kembalikan tanggal hari kerja berikutnya dari tanggal yang diberikan.

    Jika tanggalinput sudah hari kerja, kembalikan tanggal tersebut.

    Args:
        value: Tanggal awal.

    Returns:
        Tanggal hari kerja berikutnya (atau tanggal itu sendiri jika sudah hari kerja).

    Contoh:
        >>> get_next_business_day("2024-05-03")  # Jumat -> 2024-05-03
        >>> get_next_business_day("2024-05-04")  # Sabtu -> 2024-05-06 (Senin)
        >>> get_next_business_day("2024-05-01")  # Hari Buruh -> 2024-05-02
    """
    d = _parse_date(value)

    # Jika sudah hari kerja, langsung return
    if is_business_day(d):
        return d

    # Cari hari kerja berikutnya (maju maksimal 7 hari)
    for i in range(1, 8):
        candidate = d + timedelta(days=i)
        if is_business_day(candidate):
            return candidate

    return d  # fallback (seharusnya tidak terjadi)


def add_business_days(
    start_value: Union[str, date, datetime],
    days: int
) -> date:
    """
    Tambahkan jumlah hari kerja ke tanggal mulai.

    Args:
        start_value: Tanggal mulai.
        days: Jumlah hari kerja yang ditambahkan. Negatif untuk mundur.

    Returns:
        Tanggal hasil penambahan hari kerja.

    Contoh:
        >>> add_business_days("2024-05-15", 1)   # -> 2024-05-16 (first BD after start)
        >>> add_business_days("2024-05-15", 14)  # -> 2024-06-05 (spec example)
    """
    if days == 0:
        return _parse_date(start_value)

    current = _parse_date(start_value)
    direction = 1 if days > 0 else -1
    # Start date itself is NOT counted. Advance and count until we've accumulated
    # abs(days) business days. E.g. 1 BD from 15 Mei -> lands on 16 Mei.
    counter = 0

    while counter < abs(days):
        current = current + timedelta(days=direction)
        if is_business_day(current):
            counter += 1

    return current


def calculate_business_days(
    start_value: Union[str, date, datetime],
    target_value: Union[str, date, datetime]
) -> int:
    """
    Hitung jumlah hari kerja antara dua tanggal (inklusif dari target).

    Args:
        start_value: Tanggal mulai.
        target_value: Tanggal target.

    Returns:
        Jumlah hari kerja dari start hingga target (inklusif target).

    Contoh:
        >>> calculate_business_days("2024-05-15", "2024-06-05")  # -> 14
    """
    start = _parse_date(start_value)
    target = _parse_date(target_value)

    if start > target:
        return 0

    count = 0
    current = start
    while current <= target:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)

    return count


def get_deadline_remaining(
    target_value: Union[str, date, datetime],
    from_value: Union[str, date, datetime] | None = None
) -> int:
    """
    Hitung jumlah hari kerja yang tersisa sampai deadline.

    Args:
        target_value: Tanggal deadline target.
        from_value: Tanggal referensi (default: hari ini).

    Returns:
        Jumlah hari kerja tersisa (negatif jika sudah lewat).

    Contoh:
        >>> get_deadline_remaining("2024-06-05", "2024-05-20")  # -> 12
    """
    if from_value is None:
        today = date.today()
    else:
        today = _parse_date(from_value)

    target = _parse_date(target_value)

    if today > target:
        return 0  # sudah lewat, asumsikan deadline tidak dihitung mundur

    count = 0
    current = today
    while current <= target:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)

    return count


# =============================================================================
# ADVANCED: BUILD TIMELINE & REPORT
# =============================================================================

def _build_timeline(
    start: date,
    end: date,
    holidays_set: set[date]
) -> list[dict]:
    """Bangun timeline dari start ke end dengan breakdown per hari."""
    timeline = []
    current = start
    day_counter = 0

    while current <= end:
        is_weekend = current.weekday() >= 5
        is_holiday = current in holidays_set
        is_work = is_business_day(current)

        if is_work:
            day_counter += 1

        day_label = "hari kerja"
        if is_weekend:
            day_label = "weekend (Sabtu)" if current.weekday() == 5 else "weekend (Minggu)"
        elif is_holiday:
            day_label = "hari libur nasional"

        timeline.append({
            "date": _date_str_short(current),
            "display": _date_str(current),
            "day_number": day_counter if is_work else None,
            "type": "business_day" if is_work else ("holiday" if is_holiday else "weekend"),
            "label": day_label,
        })
        current += timedelta(days=1)

    return timeline


def _format_holiday_reason(holiday_str: str) -> str:
    """Kembalikan alasan libur dari string tanggal."""
    holiday_map: dict[str, str] = {
        # 2024
        "2024-01-01": "Tahun Baru 2024",
        "2024-02-08": "Isra Mi'raj 1445H",
        "2024-02-10": "Imlek 2575 Kongzili",
        "2024-03-11": "Hari Raya Nyepi 1946",
        "2024-03-29": "Hari Raya Suci Hinduism",
        "2024-03-31": "Hari Raya Idulfitri 1445H (1 Syawal)",
        "2024-04-01": "Hari Raya Idulfitri 1445H (2 Syawal)",
        "2024-04-10": "Hari Wafat Isa Al-Masih",
        "2024-05-01": "Hari Buruh Internasional",
        "2024-05-09": "Hari Raya Waisak 2568",
        "2024-06-01": "Hari Lahir Pancasila",
        "2024-06-17": "Hari Raya Qurban 1445H",
        "2024-08-17": "Hari Kemerdekaan RI ke-79",
        "2024-09-01": "Maulid Nabi 1446H",
        "2024-12-25": "Hari Natal",
        "2024-12-31": "Malam Tahun Baru",
        # 2025
        "2025-01-01": "Tahun Baru 2025",
        "2025-01-27": "Isra Mi'raj 1446H",
        "2025-01-29": "Tahun Baru Imlek 2576",
        "2025-03-14": "Hari Raya Nyepi 1947",
        "2025-03-30": "Awal Ramadan 1446H",
        "2025-03-31": "Idulfitri 1446H - 1 Syawal",
        "2025-04-01": "Idulfitri 1446H - 2 Syawal",
        "2025-04-09": "Hari Wafat Isa Al-Masih",
        "2025-05-01": "Hari Buruh Internasional",
        "2025-05-11": "Hari Raya Waisak 2569",
        "2025-05-29": "Kenaikan Isa Al-Masih",
        "2025-06-01": "Hari Lahir Pancasila",
        "2025-06-07": "Hari Raya Qurban 1446H",
        "2025-08-17": "Hari Kemerdekaan RI ke-80",
        "2025-09-05": "Maulid Nabi 1447H",
        "2025-12-25": "Hari Natal",
        # 2026
        "2026-01-01": "Tahun Baru 2026",
        "2026-01-15": "Isra Mi'raj 1447H",
        "2026-02-17": "Tahun Baru Imlek 2577",
        "2026-03-04": "Hari Raya Nyepi 1948",
        "2026-03-20": "Awal Ramadan 1447H",
        "2026-03-21": "Idulfitri 1447H - 1 Syawal",
        "2026-03-22": "Idulfitri 1447H - 2 Syawal",
        "2026-04-01": "Hari Wafat Isa Al-Masih",
        "2026-05-01": "Hari Buruh Internasional",
        "2026-05-10": "Hari Raya Waisak 2570",
        "2026-05-28": "Kenaikan Isa Al-Masih",
        "2026-06-01": "Hari Lahir Pancasila",
        "2026-06-27": "Hari Raya Qurban 1447H",
        "2026-08-17": "Hari Kemerdekaan RI ke-81",
        "2026-08-25": "Maulid Nabi 1448H",
        "2026-12-25": "Hari Natal",
    }
    return holiday_map.get(holiday_str, holiday_str)


def compute_deadline(
    start_value: Union[str, date, datetime],
    business_days: int,
    context: str = ""
) -> DeadlineResult:
    """
    Hitung deadline lengkap dengan timeline dan breakdown.

    Args:
        start_value: Tanggal mulai pengajuan.
        business_days: Jumlah hari kerja yang dibutuhkan.
        context: Konteks kasus (misal: "Somasi klien", "Gugatan", dll).

    Returns:
        DeadlineResult berisi semua informasi deadline.
    """
    start = _parse_date(start_value)
    start_parsed = get_next_business_day(start)  # Pastikan mulai di hari kerja

    # add_business_days counts N business days AFTER the start date (start is day 0).
    # E.g. add_business_days(14, "2024-05-15") lands on June 4 = 14th BD from May 15.
    target = add_business_days(start_parsed, business_days)

    # Hitung total rentang
    total_days = (target - start_parsed).days + 1

    # Hitung excluded weekends
    excluded_sat = excluded_sun = 0
    excluded_holidays_list: list[str] = []
    holidays_set = _get_holiday_set()

    current = start_parsed
    while current <= target:
        if current.weekday() == 5:
            excluded_sat += 1
        elif current.weekday() == 6:
            excluded_sun += 1
        if current in holidays_set:
            excluded_holidays_list.append(_date_str_short(current))
        current += timedelta(days=1)

    excluded_weekends = excluded_sat + excluded_sun

    # Bangun timeline
    timeline = _build_timeline(start_parsed, target, holidays_set)

    return DeadlineResult(
        start_date=_date_str_short(start_parsed),
        target_date=_date_str_short(target),
        business_days=business_days,
        total_days=total_days,
        excluded_weekends=excluded_weekends,
        excluded_holidays=excluded_holidays_list,
        timeline=timeline,
        is_business_day_target=is_business_day(target),
    )


def format_deadline_report(
    result: DeadlineResult,
    context: str = "",
    warning_before: int = 3
) -> str:
    """
    Format laporan deadline ke string yang mudah dibaca.

    Args:
        result: Hasil dari compute_deadline().
        context: Konteks kasus.
        warning_before: Berapa hari kerja sebelum deadline untuk kasih peringatan.

    Returns:
        String laporan lengkap.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  LEGAL DEADLINE CALCULATOR - IndoGovRAG")
    lines.append("=" * 60)

    if context:
        lines.append(f"  Konteks    : {context}")

    start_display = _date_str(datetime.strptime(result.start_date, "%Y-%m-%d").date())
    target_display = _date_str(datetime.strptime(result.target_date, "%Y-%m-%d").date())
    lines.append(f"  Tanggal Mulai  : {start_display}")
    lines.append(f"  Deadline      : {target_display}")
    lines.append(f"  Hari Kerja    : {result.business_days} days")
    lines.append("")

    # Breakdown
    sat_count = sun_count = 0
    for entry in result.timeline:
        if entry["type"] == "weekend":
            if "Sabtu" in entry["display"]:
                sat_count += 1
            else:
                sun_count += 1

    lines.append("  Breakdown:")
    if sat_count or sun_count:
        sat_label = f"{sat_count} Sat" if sat_count else ""
        sun_label = f"{sun_count} Sun" if sun_count else ""
        excluded = " + ".join(filter(None, [sat_label, sun_label]))
        lines.append(f"    - Excluded weekends  : {result.excluded_weekends} days ({excluded})")

    if result.excluded_holidays:
        holiday_details = []
        for hs in result.excluded_holidays:
            reason = _format_holiday_reason(hs)
            holiday_details.append(f"{hs} ({reason})")
        lines.append(f"    - Excluded holidays  : {len(result.excluded_holidays)} days")
        for hd in holiday_details:
            lines.append(f"      - {hd}")

    lines.append(f"    - Total days (kalendar): {result.total_days} days")

    # Warning deadline
    warning_date = add_business_days(
        datetime.strptime(result.target_date, "%Y-%m-%d").date(),
        -warning_before
    )
    if is_business_day(warning_date):
        warning_display = _date_str(warning_date)
    else:
        warning_display = _date_str(get_next_business_day(warning_date))

    lines.append("")
    lines.append(f"  Timeline Reminder:")
    lines.append(f"    - Kirim H-{warning_before} : {warning_display}")

    # Warning status
    today = date.today()
    target_dt = datetime.strptime(result.target_date, "%Y-%m-%d").date()
    remaining = get_deadline_remaining(result.target_date)

    lines.append("")
    if remaining > 0:
        lines.append(f"  Status      : {remaining} hari kerja tersisa menuju deadline")
    elif remaining == 0:
        if today == target_dt:
            lines.append("  Status      : HARI INI adalah deadline!")
        else:
            lines.append("  Status      : Deadline sudah lewat")
    else:
        lines.append(f"  Status      : {abs(remaining)} hari kerja melewati deadline")

    lines.append("=" * 60)

    return "\n".join(lines)


# =============================================================================
# DEMO & TEST
# =============================================================================

def run_demo():
    """Jalankan demo sesuai contoh di specification."""
    print("\n" + "=" * 60)
    print("  LEGAL DEADLINE CALCULATOR - DEMO")
    print("  IndoGovRAG")
    print("=" * 60)

    # Example from spec: 15 Mei 2024 + 14 business days
    print("\n[CONTOH 1] Specification Example")
    print("-" * 40)
    result = compute_deadline("2024-05-15", 14, context="Somasi Klien")
    print(format_deadline_report(result, context="Somasi Klien", warning_before=3))

    # Example 2: Friday start
    print("\n[CONTOH 2] Mulai hari Jumat")
    print("-" * 40)
    result2 = compute_deadline("2024-05-17", 5, context="Tanggapan Gugatan")
    print(format_deadline_report(result2, context="Tanggapan Gugatan", warning_before=2))

    # Example 3: Holiday in range
    print("\n[CONTOH 3] Terdapat libur nasional dalam rentang")
    print("-" * 40)
    result3 = compute_deadline("2024-05-27", 10, context="Banding")
    print(format_deadline_report(result3, context="Banding", warning_before=3))

    # Example 4: API-style usage
    print("\n[CONTOH 4] Penggunaan programmatic (dict output)")
    print("-" * 40)
    r = compute_deadline("2024-07-01", 7)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))

    # Example 5: is_business_day check
    print("\n[CONTOH 5] Check hari kerja")
    print("-" * 40)
    test_dates = [
        "2024-05-01",   # Hari Buruh
        "2024-05-02",   # Kamis
        "2024-05-04",   # Sabtu
        "2024-05-05",   # Minggu
        "2024-05-06",   # Senin
        "2024-05-15",   # Rabu
    ]
    for d in test_dates:
        status = "HARI KERJA" if is_business_day(d) else "LIBUR / WEEKEND"
        print(f"  {d} -> {status}")

    # Example 6: get_deadline_remaining
    print("\n[CONTOH 6] Sisa hari kerja menuju deadline")
    print("-" * 40)
    from datetime import date, timedelta
    demo_date = date(2024, 6, 5)
    remaining = get_deadline_remaining(demo_date, date(2024, 5, 20))
    print(f"  Dari 20 Mei 2024 ke deadline 5 Juni 2024: {remaining} hari kerja")


def run_tests():
    """Jalankan unit test untuk memverifikasi semua fungsi."""
    import sys
    from datetime import date

    print("\n[UNIT TESTS]")
    print("-" * 40)

    passed = 0
    failed = 0

    def check(name: str, condition: bool, msg: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}: {msg}")
            failed += 1

    # is_business_day tests
    check("weekend_saturday", not is_business_day("2024-05-04"))
    check("weekend_sunday", not is_business_day("2024-05-05"))
    check("national_holiday", not is_business_day("2024-05-01"))  # Hari Buruh
    check("regular_weekday", is_business_day("2024-05-02"))  # Kamis
    check("date_object", is_business_day(date(2024, 5, 6)))  # Senin

    # get_next_business_day tests
    check("next_bd_same_day", get_next_business_day("2024-05-02") == date(2024, 5, 2))  # Kamis
    check("next_bd_from_sat", get_next_business_day("2024-05-04") == date(2024, 5, 6))  # Sabtu -> Senin
    check("next_bd_from_holiday", get_next_business_day("2024-05-01") == date(2024, 5, 2))  # Hari Buruh -> Kamis

    # add_business_days tests
    check("add_0_days", add_business_days("2024-05-15", 0) == date(2024, 5, 15))
    check("add_1_day_fri", add_business_days("2024-05-17", 1) == date(2024, 5, 20))  # Fri -> Mon
    check("add_14_days_spec", add_business_days("2024-05-15", 14) == date(2024, 6, 4))  # 14th BD after start = 4 Juni

    # calculate_business_days tests
    check("calc_1_day", calculate_business_days("2024-05-15", "2024-05-15") == 1)
    check("calc_range_weekend", calculate_business_days("2024-05-15", "2024-05-19") == 3)  # Wed-Fri (exclude Sat+Sun)
    check("calc_full_week", calculate_business_days("2024-05-13", "2024-05-19") == 5)  # Mon-Sun = 5 weekdays

    # get_deadline_remaining tests
    check("remaining_positive", get_deadline_remaining("2024-06-05", "2024-05-20") == 13)  # includes target day

    # compute_deadline tests
    result = compute_deadline("2024-05-15", 14)
    check("compute_start", result.start_date == "2024-05-15")
    check("compute_target", result.target_date == "2024-06-04")
    check("compute_bd", result.business_days == 14)
    check("compute_excluded_holidays", len(result.excluded_holidays) >= 0)

    # JSON export
    check("to_json_valid", '"start_date"' in result.to_json())

    print(f"\n  Total: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    run_demo()
    success = run_tests()
    sys.exit(0 if success else 1)
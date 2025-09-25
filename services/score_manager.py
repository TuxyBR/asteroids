import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORES_FILE = DATA_DIR / "scores.json"
MAX_RECORDS = 100


@dataclass
class ScoreEntry:
  name: str
  score: int
  timestamp: str


def _ensure_data_dir() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_scores() -> List[ScoreEntry]:
  if not SCORES_FILE.exists():
    return []

  try:
    with SCORES_FILE.open("r", encoding="utf-8") as file:
      data = json.load(file)
  except (OSError, json.JSONDecodeError):
    return []

  records: List[ScoreEntry] = []
  for item in data:
    if not isinstance(item, dict) or "score" not in item:
      continue
    try:
      value = int(item["score"])
    except (TypeError, ValueError):
      continue

    timestamp = item.get("timestamp", "")
    name = item.get("name") or item.get("nome") or "???"
    records.append(ScoreEntry(name=name, score=value, timestamp=timestamp))

  records.sort(key=lambda entry: entry.score, reverse=True)
  return records


def _write_scores(records: List[ScoreEntry]) -> None:
  _ensure_data_dir()
  with SCORES_FILE.open("w", encoding="utf-8") as file:
    json.dump([asdict(entry) for entry in records], file, ensure_ascii=False, indent=2)


def record_score(score: int, name: str) -> None:
  try:
    value = int(score)
  except (TypeError, ValueError):
    return

  records = load_scores()
  records.append(
    ScoreEntry(
      name=(name or "???").strip() or "???",
      score=value,
      timestamp=datetime.now().isoformat(timespec="seconds"),
    )
  )

  records.sort(key=lambda entry: entry.score, reverse=True)
  _write_scores(records[:MAX_RECORDS])


def should_record(score: int) -> bool:
  try:
    value = int(score)
  except (TypeError, ValueError):
    return False

  records = load_scores()
  if len(records) < MAX_RECORDS:
    return True

  worst_score = records[-1].score if records else 0
  return value > worst_score

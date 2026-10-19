from logging import raiseExceptions
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Brak SUPABASE_URL i/lub SUPABASE_KEY w pliku .env")

supabase = create_client(url, key)


def save_article(article: dict) -> None:
    """Zapisuje nowy artykuł, nie nadpisując istniejącego."""
    supabase.table("articles").upsert(
        article,
        on_conflict="hash_id",
        ignore_duplicates=True,
    ).execute()


def get_pending_analysis(limit: int = 20) -> list[dict]:
    """Pobiera artykuły, które nie mają jeszcze analizy AI."""
    response = (
        supabase.table("articles")
        .select("*")
        .is_("analyzed_at", "null")
        .limit(limit)
        .execute()
    )
    return response.data


def save_analysis(hash_id: str, analysis: dict) -> None:
    """Zapisuje wynik analizy Nemotrona."""
    fields = {
        "summary": analysis["summary"],
        "topic": analysis["topic"],
        "sentiment": analysis["sentiment"],
        "clickbait_score": analysis["clickbait_score"],
        "sensationalism_score": analysis["sensationalism_score"],
        "confidence": analysis["confidence"],
        "reasoning": analysis["reasoning"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("articles").update(fields).eq("hash_id", hash_id).execute()


def get_pending_publication(limit: int = 20) -> list[dict]:
    """Pobiera przeanalizowane artykuły, których nie opublikowano."""
    response = (
        supabase.table("articles")
        .select("*")
        .not_.is_("analyzed_at", "null")
        .is_("discord_posted_at", "null")
        .limit(limit)
        .execute()
    )
    return response.data


def mark_discord_posted(hash_id: str) -> None:
    """Oznacza artykuł jako opublikowany na Discordzie."""
    supabase.table("articles").update(
        {"discord_posted_at": datetime.now(timezone.utc).isoformat()}
    ).eq("hash_id", hash_id).execute()


if __name__ == "__main__":
    print("Artykuły do analizy:", get_pending_analysis())
    print("Artykuły do publikacji:", get_pending_publication())

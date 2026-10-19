import discord
import asyncio
import os
from dotenv import load_dotenv
from rss import rss_sniff
from database import (
    get_pending_analysis,
    save_analysis,
    get_pending_publication,
    mark_discord_posted,
)
from analyzer import analyze_article


CHANNEL_ID = 1561431282955854035

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def run_once():
    print("Sprawdzam RSS...")

    try:
        await asyncio.to_thread(rss_sniff)
    except Exception as error:
        print(f"Błąd pobierania lub zapisu RSS: {error}")

    try:
        pending = await asyncio.to_thread(get_pending_analysis)
    except Exception as error:
        print(f"Błąd pobierania artykułów do analizy: {error}")
        return

    for article in pending:
        hash_id = article["hash_id"]

        try:
            analysis = await asyncio.to_thread(
                analyze_article,
                article["title"],
                article["description"],
            )

            await asyncio.to_thread(save_analysis, hash_id, analysis)
            print(f"Przeanalizowano: {article['title']}")

        except Exception as error:
            print(f"Błąd analizy artykułu {hash_id}: {error}")
            continue

    try:
        pending = await asyncio.to_thread(get_pending_publication)
    except Exception as error:
        print(f"Błąd pobierania artykułów do publikacji: {error}")
        return

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        channel = await client.fetch_channel(CHANNEL_ID)
    for article in pending:
        try:
            embed = discord.Embed(
                title=article["title"][:256],
                url=article["link"] or None,
                description=(article["description"] or "")[:4096],
                color=discord.Color.from_rgb(35, 45, 65),
            )

            embed.add_field(
                name="Podsumowanie AI",
                value=(article["summary"] or "Brak podsumowania")[:1024],
                inline=False,
            )

            embed.add_field(
                name="Kategoria",
                value=article["topic"] or "Nieznana",
                inline=True,
            )

            embed.add_field(
                name="Sentyment",
                value=article["sentiment"] or "Nieznany",
                inline=True,
            )

            embed.add_field(
                name="Clickbait",
                value=f"{article['clickbait_score']}/100",
                inline=True,
            )

            embed.add_field(
                name="Sensacyjność",
                value=f"{article['sensationalism_score']}/100",
                inline=True,
            )

            embed.add_field(
                name="Pewność analizy",
                value=f"{article['confidence']:.0%}",
                inline=True,
            )

            embed.add_field(
                name="Data publikacji",
                value=article["pub_date"] or "Nieznana",
                inline=True,
            )

            embed.set_footer(text="RSS Sniffer • Analiza AI")

            await channel.send(embed=embed)

            await asyncio.to_thread(mark_discord_posted, article["hash_id"])

            print(f"Opublikowano: {article['title']}")

        except Exception as error:
            print(f"Błąd publikacji artykułu {article['hash_id']}: {error}")
            continue


@client.event
async def on_ready():
    print(f"Bot zalogowany jako: {client.user}")
    try:
        await run_once()
    finally:
        await client.close()


client.run(token)

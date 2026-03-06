import sys
import asyncio

def configure_event_loop():
    """Настраивает цикл событий для Windows, чтобы psycopg работал корректно."""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("✅ Цикл событий настроен на WindowsSelectorEventLoopPolicy")
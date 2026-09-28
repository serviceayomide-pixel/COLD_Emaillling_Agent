import asyncio
from app.worker import run_pipeline

async def main():
    await run_pipeline()

asyncio.run(main())

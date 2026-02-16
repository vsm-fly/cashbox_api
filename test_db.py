import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        "postgresql://cashbox:cashbox@localhost:55432/cashbox"
    )
    value = await conn.fetchval("select 1")
    print("DB OK:", value)
    await conn.close()

asyncio.run(main())

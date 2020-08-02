import asyncio
import json

from database.database import Database
from kantek.utils.config import Config


async def main():
    a_config = Config()
    arango = Database()
    await arango.connect(a_config)
    pg_config = Config()
    pg_config.db_type = 'postgres'
    pg_config.db_username = pg_config.pg_db_username
    pg_config.db_name = pg_config.pg_db_name
    pg_config.db_host = pg_config.pg_db_host
    pg_config.db_port = pg_config.pg_db_port
    pg = Database()
    await pg.connect(pg_config)
    # print('Moving banlist')
    # all_bans = await arango.banlist.get_all()
    # all_bans = [{'id': b.id, 'reason': b.reason} for b in all_bans]
    # await pg.banlist.upsert_multiple(all_bans)

    print('Moving chats')
    all_chats = arango.db.chats.fetchAll()
    all_chats = [(c['id'], json.dumps(c['named_tags'].getStore())) for c in all_chats]
    async with pg.db.chats.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('CREATE TEMPORARY TABLE _data(id BIGINT, tags JSONB ) ON COMMIT DROP;')
            await conn.copy_records_to_table('_data', records=all_chats)
            await conn.execute('''
                    INSERT INTO chats
                    SELECT * FROM _data
                    ON CONFLICT (id)
                    DO UPDATE SET tags=excluded.tags
                ''')

    print('Moving blacklists')
    blacklists = ['bio', 'channel', 'domain', 'file', 'mhash', 'string']
    for b in blacklists:
        print(f'    Moving {b} blacklist')
        blacklisted_items = await getattr(arango.blacklists, b).get_all()
        if blacklisted_items:
            max_index = blacklisted_items[-1].index
            for i in range(1, int(max_index)):
                item = await getattr(arango.blacklists, b).get_indices([i])
                if not item:
                    await getattr(pg.blacklists, b).add('<retired item from legacy database>')
                else:
                    item = item[0]
                    await getattr(pg.blacklists, b).add(item.value)
            await getattr(pg.blacklists, b).retire('<retired item from legacy database>')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

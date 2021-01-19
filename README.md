<p align="center">
  <img src="https://i.sitischu.com/kantek_main_smol_256.png">
</p>

# Kantek
Kantek is a userbot written in Python using Telethon.

## A word of warning!
Kantek is mostly built to help with the Administration of chats and is the main source for [SpamWat.ch](https://spamwat.ch). 
Because of that it checks every message your account receives for blacklisted items, this includes strings, domains, top level domains, files, images and telegram entities. This means that for every message your account receives Kantek might make multiple http requests and resolve multiple telegram entities. The latter might lead to **large (6+ hours) Floodwaits from Telegram.**

If you want to use Kantek without the administration part, simply remove the `plugins/autobahn` folder to disable these features. 

## Requirements
Python 3.8+ is required to run the bot.
ArangoDB 3.5+ or Postgres is used to store data.

## Setup
- Copy the example config file to `config.json`
Read either the ArangoDB section or the PostgreSQL section depending on what you prefer
ArangoDB might be deprecated in the future so using postgres is suggested.

### PostgreSQL
- Set `db_type` to `postgres` in the config
- Create a database and a user in postgres
- kantek uses [migrant](https://github.com/jaemk/migrant) for migrations. Follow  the installation instructions [here](https://github.com/jaemk/migrant#installation).
- Copy the `example.Migrant.toml` to `Migrant.toml` and fill out the details.
- Run `migrant setup`
- Run `migrant apply --all` 

### ArangoDB
- Set `db_type` to `arango` in the config
- Install the driver with `pip install pyArango~=1.3.4`
- Create a user and a Database in ArangoDB. Give the user full permissions to the Database. The config defaults to the user and database name to `kantek` can be changed with [db_username](#db_username) and [db_name](#db_name) respectively.

After setting up the database:

- Put the Authentication data into the config file.
- Run bot.py

## Migrating from ArangoDB to Postgres
If you postgres runs on nonstandard values set `pg_db_username`, `pg_db_name`, `pg_db_host`, `pg_db_port`, `pg_db_password`
Stop your bot and run `migrate_to_postgres.py`. This will move everything over. If you have removed blacklist items with the old database you now might see `<retired item from legacy database>` as items when querying for some indices. This is done to keep the new indices the same. These items are disabled and users won't be banned for it. 
Once the migration is done. Change your `db_*` to the new settings and restart the bot.

## Config
### api_id
Get it from http://my.telegram.org/

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | int  | `-`       |

### api_hash
Get it from http://my.telegram.org/

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | str  | `-`       |

### db_type
The database to use. Choices from `arango` or `postgres`

| Required | Type | Default |
| -------- | ---- | ------- |
| No       | str  | arango  |

### db_username

| Required | Type | Default |
| -------- | ---- | ------- |
| No       | str  | kantek  |  

### db_name

| Required | Type | Default |
| -------- | ---- | ------- |
| No       | str  | kantek  |

### db_password

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | str  | `-`       |

### db_host
The IP the Database runs on. For ArangoDB the http is automatically added

| Required | Type | Default    |
| -------- | ---- | ---------- |
| No       | str  | 127.0.0.1  |

### db_port

Default depends on the DB type. 

ArangoDB: 8529
Postgres: 5432

| Required | Type | Default          |
| -------- | ---- | ---------------- |
| No       | int  | See description  |

### db_cluster_mode
Set this if you use your Database in a cluster

If using ArangoDB this will mean you blacklist indices will be very large

| Required | Type | Default                |
| -------- | ---- | ---------------------- |
| No       | bool | false  |


### log_bot_token

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | str  | `-`       |

### log_channel_id

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | int  | `-`       |

### gban_group

| Required | Type | Default   |
| -------- | ---- | --------- |
| No       | int  | `-`       |

### cmd_prefix
 Provide single prefix or a list of prefixes
 These will be escaped automatically

| Required | Type     | Default |
| -------- | -------- | ------- |
| No       | str|list | `.`     |

### session_name

| Required | Type | Default            |
| -------- | ---- | ------------------ |
| No       | str  | kantek-session     |

### spamwatch_host

| Required | Type | Default                  |
| -------- | ---- | ------------------------ |
| No       | str  | `https://api.spamwat.ch` |

### spamwatch_token

| Required | Type | Default   |
| -------- | ---- | --------- |
| No       | str  | `-`       |

### debug_mode
Useful for local development. Disabled actually banning a user in groups and reporting messages when using gban.

| Required | Type  | Default |
| -------- | ----- | ------- |
| No       | bool  | `False` |

### source_url
Used in .kantek and .update

| Required | Type | Default       |
| -------- | ---- | ------------- |
| No       | str  | `src.kv2.dev` |

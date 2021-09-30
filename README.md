<p align="center">
  <img src="https://i.sitischu.com/kantek_main_smol_256.png">
</p>

# Kantek
Kantek is a userbot written in Python using Telethon.

## A word of warning
Kantek is mostly built to help with the Administration of chats and is the main source for [SpamWat.ch](https://spamwat.ch). 
Because of that it checks every message your account receives for blacklisted items, this includes strings, domains, top level domains, files, images and telegram entities. This means that for every message your account receives Kantek might make multiple http requests an resolve multiple telegram entities. The latter might lead to large (6+ hours) Floodwaits from Telegram.

If you want to use Kantek without the administration part, simply remove the `plugins/autobahn` folder to disable these features. 

## Requirements
Python 3.8+ is required to run the bot.
ArangoDB 3.5+ or Postgres is used to store data.

## Setup
- Copy the example config file to `config.json`

### PostgreSQL
- Create a database and a user in postgres
- kantek uses [migrant](https://github.com/jaemk/migrant) for migrations. Follow the installation instructions [here](https://github.com/jaemk/migrant#installation) or run `cargo install migrant --features postgres`.
- Copy the `example.Migrant.toml` to `Migrant.toml` and fill out the details.
- Run `migrant setup`
- Run `migrant apply --all` 

After setting up the database:

- Put the Authentication data into the config file.
- Run bot.py

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
The database to use. Only `postgres` is supported currently.

| Required | Type | Default   |
| -------- | ---- | --------- |
| No       | str  | postgres  |

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

Postgres: 5432

| Required | Type | Default          |
| -------- | ---- | ---------------- |
| No       | int  | See description  |

### log_bot_token
The bot token for the bot that logs into the log channel

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | str  | `-`       |

### log_channel_id
The channel id for the log bot

| Required | Type | Default   |
| -------- | ---- | --------- |
| Yes      | int  | `-`       |

### gban_group
The group where gban and fban commands are sent to

| Required | Type | Default   |
| -------- | ---- | --------- |
| No       | int  | `-`       |

### prefix
The prefix you want to use

| Required | Type     | Default |
| -------- | -------- | ------- |
| No       | str      | `.`     |

### prefixes
A list of prefixes you want to use

| Required | Type      | Default |
| -------- | --------- | ------- |
| No       | List[str] | `["."]` |

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

### kill_command
Command to be run when executing `.kill`. For example `systemctl stop kantek` or `pm2 stop kantek`

| Required | Type  | Default |
| -------- | ----- | ------- |
| No       | str   | `-`     |

### source_url
Used in .kantek and .update

| Required | Type | Default       |
| -------- | ---- | ------------- |
| No       | str  | `src.kv2.dev` |

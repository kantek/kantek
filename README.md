<p align="center">
  <img src="https://i.sitischu.com/kantek_main_smol_256.png">
</p>

# Kantek
Kantek is a userbot written in Python using Telethon.

## A word of warning
Kantek is mostly built to help with the Administration of chats and is the main source for [SpamWat.ch](https://spamwat.ch). 
Because of that it checks every message your account receives for blacklisted items, this includes strings, domains, top level domains, files, images and telegram entities. This means that for every message your account receiver kantek might make multiple http requests an resolve multiple telegram entities. The latter might lead to large (6+ hours) Floodwaits from Telegram.

If you want to use kantek without the administration part, simply remove the `plugins/autobahn` folder to disable these features. 

## Requirements
Python 3.6+ is required to run the bot.
ArangoDB 3.5+ is used to store bot data.

## Setup
- Copy the example config file to `config.json`
- Create a user and a Database in ArangoDB. Give the user full permissions to the Database. The config defaults to the user and database name to `kantek` can be changed with [db_username](#db_username) and [db_name](#db_name) respectively. 
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

| Required | Type | Default                |
| -------- | ---- | ---------------------- |
| No       | str  | http://127.0.0.1:8529  |

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
If a valid regex character is used it has to be escaped. 
For example to use `\` as prefix you would have to put `\\\\` into the config.  

| Required | Type | Default |
| -------- | ---- | ------- |
| No       | str  | `.`     |

### help_prefix
The prefix that is used in the help commands examples. This does not need to be regex escaped.

| Required | Type | Default |
| -------- | ---- | ------- |
| No       | str  | `.`     |

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

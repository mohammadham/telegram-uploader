# Telegram Uploader Python Library API

This document describes the Python API for the `telegram-uploader` library. You can use all Telegram upload/download features directly in your Python code.

---

## Installation

```bash
pip install telegram-uploader
```

---

## Quick Start Example

```python
from telegram_uploader import create_client, upload_files

client = create_client(config_file='~/.config/telegram-upload.json')
result = upload_files(client, files='myfile.mp4', to='me')
print(result)
```

---

## API Reference

### 1. create_client

**Description:**
Create and return a TelegramManagerClient instance for all operations.

**Signature:**
```python
def create_client(config_file: str = None, proxy: str = None, **kwargs) -> TelegramManagerClient:
```
- `config_file`: Path to config file (default: `~/.config/telegram-upload.json`)
- `proxy`: Optional proxy string (e.g. socks5://user:pass@host:port)

**Example:**
```python
client = create_client(config_file='~/.config/telegram-upload.json')
```

---

### 2. upload_files

**Description:**
Upload one or more files to Telegram.

**Signature:**
```python
def upload_files(client, files, to=None, caption=None, thumbnail=None, force_file=False, recursive=False, delete_on_success=False, as_album=False, sort=False):
```
- `client`: TelegramManagerClient instance
- `files`: str or list of file paths
- `to`: Destination chat/channel/group (default: saved messages)
- `caption`: Caption for the file(s)
- `thumbnail`: Path to thumbnail image
- `force_file`: Force send as file (not media)
- `recursive`: Recursively upload files in directories
- `delete_on_success`: Delete local file after upload
- `as_album`: Send as album (for media)
- `sort`: Sort files by name before upload

**Example:**
```python
upload_files(client, files=['a.mp4', 'b.jpg'], to='@mychannel', caption='My files', as_album=True)
```

---

### 3. download_files

**Description:**
Download files from Telegram.

**Signature:**
```python
def download_files(client, entity, output_dir='.', split_mode='keep', delete_on_success=False, overwrite=False):
```
- `client`: TelegramManagerClient instance
- `entity`: Source chat/channel/group
- `output_dir`: Directory to save files
- `split_mode`: 'keep' or 'join' for split files
- `delete_on_success`: Delete Telegram message after download
- `overwrite`: Overwrite files if they exist

**Example:**
```python
download_files(client, entity='me', output_dir='./downloads', overwrite=True)
```

---

### 4. delete_messages

**Description:**
Delete one or more messages by message ID.

**Signature:**
```python
def delete_messages(client, entity, message_ids):
```
- `entity`: Chat/channel/group
- `message_ids`: int or list of ints

**Example:**
```python
delete_messages(client, entity='@mygroup', message_ids=[123, 124])
```

---

### 5. forward_messages

**Description:**
Forward messages to another chat/channel/group.

**Signature:**
```python
def forward_messages(client, from_chat, message_ids, to_chat):
```
- `from_chat`: Source chat
- `message_ids`: int or list of ints
- `to_chat`: Destination chat

**Example:**
```python
forward_messages(client, from_chat='me', message_ids=123, to_chat='@target')
```

---

### 6. forward_and_download

**Description:**
Forward messages and download them.

**Signature:**
```python
def forward_and_download(client, from_chat, message_ids, to_chat, output_dir='.', max_parallel=2):
```
- `from_chat`: Source chat
- `message_ids`: int or list of ints
- `to_chat`: Destination chat
- `output_dir`: Directory to save files
- `max_parallel`: Maximum parallel downloads

**Example:**
```python
forward_and_download(client, from_chat='me', message_ids=[123,124], to_chat='@target', output_dir='./dl')
```

---

### 7. upload_folder

**Description:**
Upload all files in a folder.

**Signature:**
```python
def upload_folder(client, folder, to=None, caption=None, thumbnail=None):
```
- `folder`: Path to folder
- `to`: Destination chat
- `caption`: Caption for all files
- `thumbnail`: Thumbnail for all files

**Example:**
```python
upload_folder(client, folder='./myfolder', to='me')
```

---

### 8. get_message_info

**Description:**
Get full info of a message by message ID and chat.

**Signature:**
```python
def get_message_info(client, chat, message_id):
```
- `chat`: Chat/channel/group
- `message_id`: Message ID

**Example:**
```python
info = get_message_info(client, chat='@mygroup', message_id=123)
print(info)
```

---

### 9. edit_message

**Description:**
Edit the text of a message by message ID.

**Signature:**
```python
def edit_message(client, chat, message_id, text):
```
- `chat`: Chat/channel/group
- `message_id`: Message ID
- `text`: New text

**Example:**
```python
edit_message(client, chat='@mygroup', message_id=123, text='New text!')
```

---

### 10. list_dialogs

**Description:**
List all dialogs (chats/channels/groups).

**Signature:**
```python
def list_dialogs(client):
```

**Example:**
```python
for dialog in list_dialogs(client):
    print(dialog.name, dialog.id)
```

---

### 11. list_files

**Description:**
List all files in a chat/channel/group.

**Signature:**
```python
def list_files(client, entity):
```
- `entity`: Chat/channel/group

**Example:**
```python
for file in list_files(client, entity='me'):
    print(file.file_name)
```

---

### 12. validate_file

**Description:**
Check if a file is valid for upload.

**Signature:**
```python
def validate_file(file_path):
```
- `file_path`: Path to file

**Example:**
```python
if validate_file('myfile.mp4'):
    print('File is valid!')
```

---

## Notes
- All methods require a valid `TelegramManagerClient` (use `create_client`).
- For advanced usage, see the Telethon documentation.
- For CLI usage, see [COMMANDS.md](./docs/COMMANDS.md).

---

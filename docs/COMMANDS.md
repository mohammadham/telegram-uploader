# Telegram Upload - Command Reference

This document describes all available commands and options for the telegram-upload package.

## Installation

You can install the package via pip:

```bash
pip3 install telegram-upload
```
Or use it as a Python module:
```bash
python -m telegram_upload.management <command> [options]
```

## Commands

### upload
Upload one or more files to Telegram.

**Usage:**
```bash
telegram-upload file1.mp4 file2.mkv [options]
```
**Options:**
- `--to <entity>`: Destination chat/channel/group (default: saved messages)
- `--caption <text>`: Set caption for the file
- `--thumbnail-file <path>`: Set thumbnail for the file
- `--json-output`: Show full JSON output of uploaded file info
- `--json-minimal`: Show only file_id and message_id as JSON
- `--delete-on-success`: Delete local file after successful upload
- `--force-file`: Force send as file
- `--sort`: Sort files by name before upload
- `--interactive`: Use interactive mode

### download
Download files from Telegram.

**Usage:**
```bash
telegram-download [options]
```
**Options:**
- `--from <entity>`: Source chat/channel/group (default: saved messages)
- `--output-dir <path>`: Directory to save downloaded files
- `--overwrite`: Overwrite files if they exist
- `--delete-on-success`: Delete telegram message after successful download
- `--split-files <mode>`: How to handle split files (keep/join)
- `--interactive`: Use interactive mode

### delete
Delete one or more messages from a chat/channel/group by message ID.

**Usage:**
```bash
telegram-delete --from <entity> --message-ids <id1> --message-ids <id2>
```
**Options:**
- `--from <entity>`: Source chat/channel/group
- `--message-ids <id>`: Message ID(s) to delete (can be repeated)

### forward-messages
Forward one or more messages to another chat/channel/group.

**Usage:**
```bash
telegram-upload forward-messages --from-chat <entity> --message-ids <id1> --message-ids <id2> --to-chat <entity>
```
**Options:**
- `--from-chat <entity>`: Source chat/channel/group
- `--message-ids <id>`: Message ID(s) to forward (can be repeated)
- `--to-chat <entity>`: Destination chat/channel/group

### forward-and-download
Forward one or more messages to another chat/channel/group and download them.

**Usage:**
```bash
telegram-upload forward-and-download --from-chat <entity> --message-ids <id1> --message-ids <id2> --to-chat <entity> [--max-parallel <n>]
```
**Options:**
- `--from-chat <entity>`: Source chat/channel/group
- `--message-ids <id>`: Message ID(s) to forward and download (can be repeated)
- `--to-chat <entity>`: Destination chat/channel/group
- `--max-parallel <n>`: Maximum parallel downloads (default: 2)

### upload-folder
Upload all files in a folder to Telegram.

**Usage:**
```bash
telegram-upload upload-folder --folder <path> [--to <entity>] [--caption <text>] [--thumbnail <path>]
```
**Options:**
- `--folder <path>`: Path to folder
- `--to <entity>`: Destination chat/channel/group (default: saved messages)
- `--caption <text>`: Set caption for all files
- `--thumbnail <path>`: Set thumbnail for all files

### get-message-info
Get full info of a message by message ID and chat.

**Usage:**
```bash
telegram-upload get-message-info --chat <entity> --message-id <id>
```
**Options:**
- `--chat <entity>`: Chat/channel/group
- `--message-id <id>`: Message ID

### edit-message
Edit the text of a message by message ID (if allowed by Telegram).

**Usage:**
```bash
telegram-upload edit-message --chat <entity> --message-id <id> --text "new text"
```
**Options:**
- `--chat <entity>`: Chat/channel/group
- `--message-id <id>`: Message ID
- `--text <text>`: New text for the message

## General Notes
- All commands support `--config` for specifying a custom config file.
- You can use `--proxy` to set a proxy for all commands.
- All outputs are in JSON format for easy integration.
- For more details, see the [main README](../README.rst).

## Examples
See the README for more usage examples and tips.

---
For more help, see the documentation or run any command with `--help`.

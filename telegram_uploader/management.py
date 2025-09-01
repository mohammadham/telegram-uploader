# -*- coding: utf-8 -*-

"""Console script for telegram-uploader."""
import os

import click
from telethon.tl.types import User

from telegram_uploader.cli import show_checkboxlist, show_radiolist
from telegram_uploader.client import TelegramManagerClient, get_message_file_attribute
from telegram_uploader.config import default_config, CONFIG_FILE
from telegram_uploader.download_files import KeepDownloadSplitFiles, JoinDownloadSplitFiles
from telegram_uploader.exceptions import catch
from telegram_uploader.upload_files import NoDirectoriesFiles, RecursiveFiles, NoLargeFiles, SplitFiles, is_valid_file
from telegram_uploader.utils import async_to_sync, amap, sync_to_async_iterator


try:
    from natsort import natsorted
except ImportError:
    natsorted = None


DIRECTORY_MODES = {
    'fail': NoDirectoriesFiles,
    'recursive': RecursiveFiles,
}
LARGE_FILE_MODES = {
    'fail': NoLargeFiles,
    'split': SplitFiles,
}
DOWNLOAD_SPLIT_FILE_MODES = {
    'keep': KeepDownloadSplitFiles,
    'join': JoinDownloadSplitFiles,
}


def get_file_display_name(message):
    display_name_parts = []
    is_document = message.document
    if is_document and message.document.mime_type:
        display_name_parts.append(message.document.mime_type.split('/')[0])
    if is_document and get_message_file_attribute(message):
        display_name_parts.append(get_message_file_attribute(message).file_name)
    if message.text:
        display_name_parts.append(f'[{message.text}]' if display_name_parts else message.text)
    from_user = message.sender and isinstance(message.sender, User)
    if from_user:
        display_name_parts.append('by')
    if from_user and message.sender.first_name:
        display_name_parts.append(message.sender.first_name)
    if from_user and message.sender.last_name:
        display_name_parts.append(message.sender.last_name)
    if from_user and message.sender.username:
        display_name_parts.append(f'@{message.sender.username}')
    display_name_parts.append(f'{message.date}')
    return ' '.join(display_name_parts)


async def interactive_select_files(client, entity: str):
    iterator = client.iter_files(entity)
    iterator = amap(lambda x: (x, get_file_display_name(x)), iterator,)
    return await show_checkboxlist(iterator)


async def interactive_select_local_files():
    iterator = filter(lambda x: os.path.isfile(x) and os.path.lexists(x), os.listdir('.'))
    iterator = sync_to_async_iterator(map(lambda x: (x, x), iterator))
    return await show_checkboxlist(iterator, 'Not files were found in the current directory '
                                             '(subdirectories are not supported). Exiting...')


async def interactive_select_dialog(client):
    iterator = client.iter_dialogs()
    iterator = amap(lambda x: (x, x.name), iterator,)
    value = await show_radiolist(iterator, 'Not dialogs were found in your Telegram session. '
                                           'Have you started any conversations?')
    return value.id if value else None


class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with'
                ' arguments: [{}].'.format(self.mutually_exclusive_text)
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    self.mutually_exclusive_text
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )

    @property
    def mutually_exclusive_text(self):
        return ', '.join([x.replace('_', '-') for x in self.mutually_exclusive])

@click.command()
@click.option('--from', '-f', 'from_', required=True, help='Chat/channel/group ID, username, or invite link.')
@click.option('--message-ids', required=True, multiple=True, type=int, help='Message ID(s) to delete. You can specify multiple.')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
def delete(from_, message_ids, config, proxy):
    """Delete one or more messages from a chat/channel/group by message ID."""
    import json
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    if  not from_:
        from_ = 'me'
    try:
        entity = client.get_input_entity(from_)
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to resolve entity: {e}"}, ensure_ascii=False))
        return
    try:
        result = async_to_sync(client.delete_messages(entity, message_ids))
        # Telethon returns True for deleted, False for not deleted (for each message)
        response = []
        for mid, status in zip(message_ids, result if isinstance(result, list) else [result]):
            response.append({"message_id": mid, "deleted": bool(status)})
        click.echo(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": f"Delete failed: {e}"}, ensure_ascii=False))
@click.command()
@click.argument('files', nargs=-1)
@click.option('--to', default=None, help='Phone number, username, invite link or "me" (saved messages). By default "me".')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-d', '--delete-on-success', is_flag=True, help='Delete local file after successful upload.')
@click.option('--print-file-id', is_flag=True, help='Print the id of the uploaded file after the upload.')
@click.option('--force-file', is_flag=True, help='Force send as a file. The filename will be preserved but the preview will not be available.')
@click.option('-f', '--forward', multiple=True, help='Forward the file to a chat (alias or id) or user (username, mobile or id). This option can be used multiple times.')
@click.option('--directories', default='fail', type=click.Choice(list(DIRECTORY_MODES.keys())), help='Defines how to process directories. By default directories are not accepted and will raise an error.')
@click.option('--large-files', default='fail', type=click.Choice(list(LARGE_FILE_MODES.keys())), help='Defines how to process large files unsupported for Telegram. By default large files are not accepted and will raise an error.')
@click.option('--caption', type=str, help='Change file description. By default the file name.')
@click.option('--no-thumbnail', is_flag=True, cls=MutuallyExclusiveOption, mutually_exclusive=["thumbnail_file"], help='Disable thumbnail generation. For some known file formats, Telegram may still generate a thumbnail or show a preview.')
@click.option('--thumbnail-file', default=None, cls=MutuallyExclusiveOption, mutually_exclusive=["no_thumbnail"], help='Path to the preview file to use for the uploaded file.')
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-a', '--album', is_flag=True, help='Send video or photos as an album.')
@click.option('-i', '--interactive', is_flag=True, help='Use interactive mode.')
@click.option('--sort', is_flag=True, help='Sort files by name before upload it. Install the natsort Python package for natural sorting.')
@click.option('--json-output', is_flag=True, help='Show full JSON output of uploaded file info.')
@click.option('--json-minimal', is_flag=True, help='Show only file_id and message_id as JSON.')
def upload(files, to, config, delete_on_success, print_file_id, force_file, forward, directories, large_files, caption,
           no_thumbnail, thumbnail_file, proxy, album, interactive, sort, json_output, json_minimal):
    """Upload one or more files to Telegram using your personal account.
    The maximum file size is 2 GiB for free users and 4 GiB for premium accounts.
    By default, they will be saved in your saved messages.
    """
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    if interactive and not files:
        click.echo('Select the local files to upload:')
        click.echo('[SPACE] Select file [ENTER] Next step')
        files = async_to_sync(interactive_select_local_files())
    if interactive and not files:
        # No files selected. Exiting.
        return
    if interactive and to is None:
        click.echo('Select the recipient dialog of the files:')
        click.echo('[SPACE] Select dialog [ENTER] Next step')
        to = async_to_sync(interactive_select_dialog(client))
    elif to is None:
        to = 'me'
    files = filter(lambda file: is_valid_file(file, lambda message: click.echo(message, err=True)), files)
    files = DIRECTORY_MODES[directories](client, files)
    if directories == 'fail':
        # Validate now
        files = list(files)
    if no_thumbnail:
        thumbnail = False
    elif thumbnail_file:
        thumbnail = thumbnail_file
    else:
        thumbnail = None
    files_cls = LARGE_FILE_MODES[large_files]
    files = files_cls(client, files, caption=caption, thumbnail=thumbnail, force_file=force_file)
    if large_files == 'fail':
        # Validate now
        files = list(files)
    if isinstance(to, str) and to.lstrip("-+").isdigit():
        to = int(to)
    if sort and natsorted:
        files = natsorted(files, key=lambda x: x.name)
    elif sort:
        files = sorted(files, key=lambda x: x.name)
    # اگر خروجی json فعال باشد، print_file_id را غیرفعال کن تا فقط خروجی json نمایش داده شود
    pfid = print_file_id
    if json_output or json_minimal:
        pfid = False
    if album:
        messages = client.send_files_as_album(to, files, delete_on_success, pfid, forward)
        if json_output or json_minimal:
            for msg in messages:
                if json_minimal:
                    click.echo(client.get_message_minimal_json(msg))
                else:
                    click.echo(client.get_message_json(msg))
    else:
        messages = client.send_files(to, files, delete_on_success, pfid, forward)
        if json_output or json_minimal:
            for msg in messages:
                if json_minimal:
                    click.echo(client.get_message_minimal_json(msg))
                else:
                    click.echo(client.get_message_json(msg))


@click.command()
@click.option('--from', '-f', 'from_', default='', help='Phone number, username, chat id or "me" (saved messages). By default "me".')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-d', '--delete-on-success', is_flag=True, help='Delete telegram message after successful download. Useful for creating a download queue.')
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-m', '--split-files', default='keep', type=click.Choice(list(DOWNLOAD_SPLIT_FILE_MODES.keys())), help='Defines how to download large files split in Telegram. By default the files are not merged.')
@click.option('-i', '--interactive', is_flag=True, help='Use interactive mode.')
@click.option('--output-dir', default=None, help='Directory to save downloaded files.')
@click.option('--overwrite', is_flag=True, help='Overwrite files if they exist.')
def download(from_, config, delete_on_success, proxy, split_files, interactive, output_dir, overwrite):
    """Download all the latest messages that are files in a chat, by default download
    from "saved messages". It is recommended to forward the files to download to
    "saved messages" and use parameter ``--delete-on-success``. Forwarded messages will
    be removed from the chat after downloading, such as a download queue.
    """
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    if not interactive and not from_:
        from_ = 'me'
    elif isinstance(from_, str)  and from_.lstrip("-+").isdigit():
        from_ = int(from_)
    elif interactive and not from_:
        click.echo('Select the dialog of the files to download:')
        click.echo('[SPACE] Select dialog [ENTER] Next step')
        from_ = async_to_sync(interactive_select_dialog(client))
    if interactive:
        click.echo('Select all files to download:')
        click.echo('[SPACE] Select files [ENTER] Download selected files')
        messages = async_to_sync(interactive_select_files(client, from_))
    else:
        messages = client.find_files(from_)
    messages_cls = DOWNLOAD_SPLIT_FILE_MODES[split_files]
    download_files = messages_cls(reversed(list(messages)))
    # مدیریت مسیر ذخیره و overwrite
    import os
    for download_file in download_files:
        save_path = download_file.file_name
        if output_dir:
            save_path = os.path.join(output_dir, os.path.basename(download_file.file_name))
        if os.path.exists(save_path) and not overwrite:
            click.echo(f"File exists and overwrite is disabled: {save_path}", err=True)
            continue
        download_file.set_download_file_name(save_path)
        client.download_files(from_, [download_file], delete_on_success)
@click.command()
@click.option('--from-chat', required=True, help='Source chat/channel/group ID, username, or invite link.')
@click.option('--message-ids', required=True, multiple=True, type=int, help='Message ID(s) to forward and download. You can specify multiple.')
@click.option('--to-chat', default='me', help='Destination chat/channel/group ID, username, or "me" (saved messages).')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
@click.option('--max-parallel', default=2, type=int, help='Maximum parallel downloads (queue size). Default: 2')
def forward_and_download(from_chat, message_ids, to_chat, config, proxy, max_parallel):
    """Forward one or more file messages by message_id from source chat to destination, then download them from destination as a queue."""
    import json
    import concurrent.futures
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    try:
        src_entity = client.get_input_entity(from_chat)
        dst_entity = client.get_input_entity(to_chat)
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to resolve entity: {e}"}, ensure_ascii=False))
        return
    try:
        # فوروارد پیام‌ها
        fwd_msgs = async_to_sync(client.forward_messages(dst_entity, message_ids, src_entity))
        if not isinstance(fwd_msgs, list):
            fwd_msgs = [fwd_msgs]
        # دانلود صفی با تعداد همزمان مشخص
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_msg = {
                executor.submit(async_to_sync, client.download_media, msg): msg
                for msg in fwd_msgs if hasattr(msg, 'document') and msg.document
            }
            for future in concurrent.futures.as_completed(future_to_msg):
                msg = future_to_msg[future]
                try:
                    file_name = future.result()
                    results.append({
                        "message_id": msg.id,
                        "file_name": file_name,
                        "status": "downloaded"
                    })
                except Exception as e:
                    results.append({
                        "message_id": msg.id,
                        "status": f"download_failed: {e}"
                    })
        # پیام‌هایی که فایل نداشتند
        for msg in fwd_msgs:
            if not (hasattr(msg, 'document') and msg.document):
                results.append({
                    "message_id": msg.id,
                    "status": "no_document_found"
                })
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": f"Forward or download failed: {e}"}, ensure_ascii=False))

@click.command()
@click.option('--from-chat', required=True, help='Source chat/channel/group ID, username, or invite link.')
@click.option('--message-ids', required=True, multiple=True, type=int, help='Message ID(s) to forward. You can specify multiple.')
@click.option('--to-chat', required=True, help='Destination chat/channel/group ID, username, or invite link.')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
def forward_messages_cmd(from_chat, message_ids, to_chat, config, proxy):
    """Forward one or more messages by message_id from source chat to destination."""
    import json
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    try:
        src_entity = client.get_input_entity(from_chat)
        dst_entity = client.get_input_entity(to_chat)
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to resolve entity: {e}"}, ensure_ascii=False))
        return
    try:
        fwd_msgs = async_to_sync(client.forward_messages(dst_entity, message_ids, src_entity))
        response = []
        if not isinstance(fwd_msgs, list):
            fwd_msgs = [fwd_msgs]
        for msg in fwd_msgs:
            response.append({
                "message_id": getattr(msg, 'id', None),
                "status": "forwarded" if hasattr(msg, 'id') else "failed"
            })
        click.echo(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": f"Forward failed: {e}"}, ensure_ascii=False))
@click.command()
@click.option('--chat', required=True, help='Chat/channel/group ID, username, or invite link.')
@click.option('--message-id', required=True, type=int, help='Message ID to edit.')
@click.option('--text', required=True, help='New text for the message.')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
def edit_message(chat, message_id, text, config, proxy):
    """Edit the text of a message by message_id (if allowed by Telegram)."""
    import json
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    try:
        entity = client.get_input_entity(chat)
        msg = async_to_sync(client.edit_message(entity, message_id, text))
        click.echo(json.dumps({
            "message_id": getattr(msg, 'id', None),
            "status": "edited",
            "new_text": getattr(msg, 'text', None)
        }, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": f"Edit message failed: {e}"}, ensure_ascii=False))
@click.command()
@click.option('--folder', required=True, help='Path to folder to upload all files.')
@click.option('--to', default='me', help='Destination chat/channel/group ID, username, or "me" (saved messages).')
@click.option('--caption', type=str, help='Set caption for all files.')
@click.option('--thumbnail', default=None, help='Set thumbnail for all files.')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
def upload_folder(folder, to, caption, thumbnail, config, proxy):
    """Upload all files in a folder to destination chat with optional caption/thumbnail."""
    import os
    import json
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    if not os.path.isdir(folder):
        click.echo(json.dumps({"error": f"Folder not found: {folder}"}, ensure_ascii=False))
        return
    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not files:
        click.echo(json.dumps({"error": "No files found in folder."}, ensure_ascii=False))
        return
    results = []
    for file_path in files:
        try:
            msg = client.send_files(to, [file_path], delete_on_success=False, print_file_id=False, forward=(), send_as_media=False)
            if isinstance(msg, list):
                msg = msg[0]
            results.append({
                "file": file_path,
                "message_id": getattr(msg, 'id', None),
                "status": "uploaded"
            })
        except Exception as e:
            results.append({
                "file": file_path,
                "status": f"upload_failed: {e}"})
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))
@click.command()
@click.option('--chat', required=True, help='Chat/channel/group ID, username, or invite link.')
@click.option('--message-id', required=True, type=int, help='Message ID to get info.')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-p', '--proxy', default=None, help='Use an http proxy, socks4, socks5 or mtproxy.')
def get_message_info(chat, message_id, config, proxy):
    """Get full info of a message by message_id and chat."""
    import json
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    try:
        entity = client.get_input_entity(chat)
        msg = async_to_sync(client.get_messages(entity, ids=message_id))
        # نمایش اطلاعات کامل پیام
        info = {
            "message_id": getattr(msg, 'id', None),
            "chat_id": getattr(getattr(msg, 'chat', None), 'id', None),
            "date": str(getattr(msg, 'date', None)),
            "sender_id": getattr(getattr(msg, 'sender', None), 'id', None),
            "text": getattr(msg, 'text', None),
            "file_name": getattr(get_message_file_attribute(msg), 'file_name', None) if msg.document else None,
            "media": str(getattr(msg, 'media', None)),
            "document": bool(getattr(msg, 'document', None)),
        }
        click.echo(json.dumps(info, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": f"Get message info failed: {e}"}, ensure_ascii=False))
upload_cli = catch(upload)
download_cli = catch(download)
delete_cli = catch(delete)
forward_cli = catch(forward_messages_cmd)
dforward_cli = catch(forward_and_download)
info_cli = catch(get_message_info)
edit_cli = catch(edit_message)
folder_cli = catch(upload_folder)


if __name__ == '__main__':
    import sys
    import re
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    commands = {'upload': upload_cli, 'download': download_cli, 'delete': delete_cli, 'forward-and-download': dforward_cli, 'forward-messages': forward_cli, 'get-message-info': info_cli, 'upload-folder': folder_cli, 'edit-message': edit_cli}
    if len(sys.argv) < 2:
        sys.stderr.write('A command is required. Available commands: {}\n'.format(
            ', '.join(commands)
        ))
        sys.exit(1)
    if sys.argv[1] not in commands:
        sys.stderr.write('{} is an invalid command. Valid commands: {}\n'.format(
            sys.argv[1], ', '.join(commands)
        ))
        sys.exit(1)
    fn = commands[sys.argv[1]]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    sys.exit(fn())

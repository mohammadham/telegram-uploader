"""
High-level Python API for telegram-uploader library.
"""
from typing import List, Optional, Union
from .client.telegram_manager_client import TelegramManagerClient
from .upload_files import (
    is_valid_file,
    NoDirectoriesFiles,
    RecursiveFiles,
    NoLargeFiles,
    SplitFiles,
)
from .download_files import DownloadFile, KeepDownloadSplitFiles, JoinDownloadSplitFiles
from .exceptions import TelegramUploadError
from typing import Callable
try:
    from natsort import natsorted
except ImportError:
    natsorted = None
def create_client(config_file: Optional[str] = None, proxy: Optional[str] = None, **kwargs) -> TelegramManagerClient:
    """
    Create and return a TelegramManagerClient instance.
    """
    return TelegramManagerClient(config_file=config_file, proxy=proxy, **kwargs)

WarnFunc = Callable[[str], None]

# 1-to-1 mapping kept in cli
DIRECTORY_MODES = {
    "ignore": lambda client, files, **kw: NoDirectoriesFiles(client, files, **kw),
    "recursive": lambda client, files, **kw: RecursiveFiles(client, files, **kw),
    "fail": lambda client, files, **kw: NoDirectoriesFiles(client, files, **kw),
}

LARGE_FILE_MODES = {
    'fail': NoLargeFiles,
    'split': SplitFiles,
}


def upload_files(
    client: TelegramManagerClient,
    files: Union[str, List[str]],
    to: Optional[str] = None,
    caption: Optional[str] = None,
    thumbnail: Optional[str] = None,
    force_file: bool = False,
    delete_on_success: bool = False,
    as_album: bool = False,
    sort: bool = False,
    *,
    directories: str = "ignore",          # ignore | recursive | fail
    large_files: str = "fail",          #   split | fail
    no_thumbnail: bool = False,           # mimic CLI flag
    warn: Optional[WarnFunc] = None,
    **_,
) -> List:
    """
    Upload file(s) to Telegram – *same behaviour as CLI upload command*.
    All optional flags mirror the CLI names.  No click dependency.
    """
    if warn is None:
        warn = lambda msg: print(msg, file=sys.stderr)

    # ---------- normalise ----------
    if isinstance(files, str):
        files = [files]
    if to is None:
        to = "me"
    if isinstance(to, str) and to.lstrip("-+").isdigit():
        to = int(to)

    # ---------- validate files ----------
    files = filter(lambda f: is_valid_file(f, lambda m: warn(m)), files)

    # ---------- directory mode ----------
    files_iter_cls = DIRECTORY_MODES[directories]
    files = files_iter_cls(
        client, files, thumbnail=thumbnail, force_file=force_file, caption=caption
    )
    if directories == "fail":           # force early validation
        files = list(files)

    # ---------- large-file mode ----------
    if no_thumbnail:                    # CLI semantic
        thumbnail = False
    files_cls = LARGE_FILE_MODES[large_files]
    files = files_cls(
        client, files, caption=caption, thumbnail=thumbnail, force_file=force_file
    )
    if large_files == "fail":
        files = list(files)

    # ---------- sort ----------
    if sort and natsorted:
        files = natsorted(files, key=lambda x: x.name)
    elif sort:
        files = sorted(files, key=lambda x: x.name)

    # ---------- send ----------
    if as_album:
        return client.send_files_as_album(to, files, delete_on_success, print_file_id=False)
    else:
        return client.send_files(to, files, delete_on_success, print_file_id=False)
def download_files(
    client: TelegramManagerClient,
    entity: str,
    output_dir: str = '.',
    split_mode: str = 'keep',
    delete_on_success: bool = False,
    overwrite: bool = False,
    **kwargs
):
    """
    Download files from Telegram.
    """
    import os
    if split_mode == 'join':
        split_handler = JoinDownloadSplitFiles
    else:
        split_handler = KeepDownloadSplitFiles
    messages = client.find_files(entity)
    download_files_iter = split_handler(messages)
    results = []
    for download_file in download_files_iter:
        save_path = download_file.file_name
        if output_dir:
            save_path = os.path.join(output_dir, os.path.basename(download_file.file_name))
        if os.path.exists(save_path) and not overwrite:
            continue
        download_file.set_download_file_name(save_path)
        results.append(client.download_files(entity, [download_file], delete_on_success=delete_on_success))
    return results
def delete_messages(client: TelegramManagerClient, entity: str, message_ids: Union[int, List[int]]):
    """
    Delete one or more messages from a chat/channel/group by message ID.
    """
    if isinstance(message_ids, int):
        message_ids = [message_ids]
    entity = client.get_input_entity(entity)
    return client.delete_messages(entity, message_ids)

def forward_messages(client: TelegramManagerClient, from_chat: str, message_ids: Union[int, List[int]], to_chat: str):
    """
    Forward one or more messages to another chat/channel/group.
    """
    if isinstance(message_ids, int):
        message_ids = [message_ids]
    src_entity = client.get_input_entity(from_chat)
    dst_entity = client.get_input_entity(to_chat)
    return client.forward_messages(dst_entity, message_ids, src_entity)

def forward_and_download(client: TelegramManagerClient, from_chat: str, message_ids: Union[int, List[int]], to_chat: str, output_dir: str = '.', max_parallel: int = 2):
    """
    Forward messages and download them to output_dir.
    """
    import concurrent.futures
    if isinstance(message_ids, int):
        message_ids = [message_ids]
    src_entity = client.get_input_entity(from_chat)
    dst_entity = client.get_input_entity(to_chat)
    fwd_msgs = client.forward_messages(dst_entity, message_ids, src_entity)
    if not isinstance(fwd_msgs, list):
        fwd_msgs = [fwd_msgs]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        future_to_msg = {
            executor.submit(client.download_media, msg): msg
            for msg in fwd_msgs if hasattr(msg, 'document') and msg.document
        }
        for future in concurrent.futures.as_completed(future_to_msg):
            results.append(future.result())
    return results

def upload_folder(client: TelegramManagerClient, folder: str, to: Optional[str] = None, caption: Optional[str] = None, thumbnail: Optional[str] = None):
    """
    Upload all files in a folder to Telegram.
    """
    import os
    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    return upload_files(client, files, to=to, caption=caption, thumbnail=thumbnail)

def get_message_info(client: TelegramManagerClient, chat: str, message_id: int):
    """
    Get full info of a message by message ID and chat.
    """
    entity = client.get_input_entity(chat)
    return client.get_messages(entity, ids=message_id)

def edit_message(client: TelegramManagerClient, chat: str, message_id: int, text: str):
    """
    Edit the text of a message by message ID.
    """
    entity = client.get_input_entity(chat)
    return client.edit_message(entity, message_id, text)

# Utility: list dialogs (chats)
def list_dialogs(client: TelegramManagerClient):
    """
    List all dialogs (chats/channels/groups).
    """
    return list(client.iter_dialogs())

# Utility: list files in a chat
def list_files(client: TelegramManagerClient, entity: str):
    """
    List all files in a chat/channel/group.
    """
    return list(client.find_files(entity))


def validate_file(file_path: str) -> bool:
    """
    Check if a file is valid for upload.
    """
    return is_valid_file(file_path)

# -*- coding: utf-8 -*-

"""Top-level package for telegram-uploader."""

__author__ = """mohammadham"""
__email__ = 'contacto@mohammadham.ir'
__version__ = '0.9.3'

# Library API
from .api import (
	create_client, upload_files, download_files, validate_file,
	delete_messages, forward_messages, forward_and_download, upload_folder,
	get_message_info, edit_message, list_dialogs, list_files
)

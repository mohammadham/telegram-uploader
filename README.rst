
.. image:: https://raw.githubusercontent.com/mohammadham/telegram-uploader/master/logo.png
    :width: 100%

|

#################
telegram-uploader
#################

Telegram-uploader can be used both as a **command-line tool** and as a **Python library** in your own code.

**Python Library Usage:**

See `Docs <docs/library_api.md>`_ for full API reference and code examples for all features.

Telegram-uploader uses your **personal Telegram account** to **upload** / **download**  files up to **4 GiB** (2 GiB for
free users) and ext actions. Turn Telegram into your personal ☁ cloud!

To **install 🔧 telegram-uploader**, run this command in your terminal:

.. code-block:: console

    $ sudo pip3 install -U telegram-uploader

This is the preferred method to install telegram-upload, as it will always install the most recent stable release.
🐍 **Python 3.7-3.11** are tested and supported. There are other installation ways available like `Docker <#-docker>`_.
New options
-----------

JSON output options
-------------------
You can get the upload result as JSON for integration with other tools:

.. code-block:: console

  $ telegram-upload file.jpg --json-output

This will print all available info about the uploaded file/message as JSON.

If you only need file_id and message_id:

.. code-block:: console

  $ telegram-upload file.jpg --json-minimal

No other text will be printed when these options are used, so you can safely parse the output.


Full command reference and options are available in the documentation:

`See COMMANDS.md for all commands and options <docs/COMMANDS.md>`_


.. image:: https://raw.githubusercontent.com/mohammadham/telegram-uploader/master/telegram-upload-demo.gif
  :target: https://asciinema.org/a/592098
  :width: 100%

❓ Usage
========
To use this program you need an Telegram account and your **App api_id & api_hash** (get it in
`my.telegram.org <https://my.telegram.org/>`_). The first time you use telegram-upload it requests your
📱 **telephone**, **api_id** and **api_hash**. Bot tokens can not be used with this program (bot uploads are limited to
50MB).

To **send ⬆️ files** (by default it is uploaded to saved messages):

.. code-block:: console

    $ telegram-upload file1.mp4 file2.mkv

You can **download ⤵️ the files** again from your saved messages (by default) or from a channel. All files will be
downloaded until the last text message.

.. code-block:: console

    $ telegram-download

`Read the documentation <https://docs.nekmo.org/telegram-upload/usage.html#telegram-download>`_ for more info about the
options availables.

Interactive mode
----------------
The **interactive option** (``--interactive``) allows you to choose the dialog and the files to download or upload with
a **terminal 🪄 wizard**. It even **supports mouse**!

.. code-block:: console

    $ telegram-upload --interactive    # Interactive upload
    $ telegram-download --interactive  # Interactive download

`More info in the documentation <https://docs.nekmo.org/telegram-upload/usage.html#interactive-mode>`_

Set group or chat
-----------------
By default when using telegram-upload without specifying the recipient or sender, telegram-upload will use your personal
chat. However you can define the 👨 destination. For file upload the argument is ``--to <entity>``. For example:

.. code-block::

    $ telegram-upload --to telegram.me/joinchat/AAAAAEkk2WdoDrB4-Q8-gg video.mkv

You can download files from a specific chat using the --from <entity> parameter. For example:

.. code-block::

    $ telegram-download --from username

You can see all `the possible values for the entity in the documentation <https://docs.nekmo.org/telegram-upload/usage.html#set-recipient-or-sender>`_.

Split & join files
------------------
If you try to upload a file that **exceeds the maximum supported** by Telegram by default, an error will occur. But you
can enable ✂ **split mode** to upload multiple files:

.. code-block:: console

    $ telegram-upload --large-files split large-video.mkv

Files split using split can be rejoined on download using:

.. code-block:: console

    $ telegram-download --split-files join

Find more help in `the telegram-upload documentation <https://docs.nekmo.org/telegram-upload/usage.html#split-files>`_.

Delete on success
-----------------
The ``--delete-on-success`` option allows you to ❌ **delete the Telegram message** after downloading the file. This is
useful to send files to download to your saved messages and avoid downloading them again. You can use this option to
download files on your computer away from home.

Configuration
-------------
Credentials are saved in ``~/.config/telegram-upload.json`` and ``~/.config/telegram-upload.session``. You must make
sure that these files are secured. You can copy these 📁 files to authenticate ``telegram-uploader`` on more machines, but
it is advisable to create a session file for each machine or in config file set session method with session file address.

More options
------------

Telegram-upload has more options available, like customizing the files thumbnail, set a caption message (including
variables) or configuring a proxy.
`Read the documentation <https://docs.nekmo.org/telegram-upload/usage.html#telegram-download>`_ for more info.

💡 Features
===========

* **Upload** and **download** multiples files  (up to 4 GiB per file for premium users).
* **Interactive** mode.
* Add video **thumbs**.
* **Split** and **join** large files.
* **Delete** local or remote file on success.
* Use **variables** in the **caption** message.
* ... And **more**.

🐋 Docker
=========
Run telegram-upload without installing it on your system using Docker. Instead of ``telegram-upload``
and ``telegram-download`` you should use ``upload`` and ``download``. Usage::


    $ docker run -v <files_dir>:/files/
                 -v <config_dir>:/config
                 -it mohammadham/telegram-uploader:master
                 <command> <args>

* ``<files_dir>``: upload or download directory.
* ``<config_dir>``: Directory that will be created to store the telegram-upload configuration.
  It is created automatically.
* ``<command>``: ``upload`` and ``download``.
* ``<args>``: ``telegram-upload`` and ``telegram-download`` arguments.

For example::

    $ docker run -v /media/data/:/files/
                 -v $PWD/config:/config
                 -it mohammadham/telegram-uploader:master
                 upload file_to_upload.txt

❤️ Thanks
=========
This project developed by `MohammadHam <https://github.com/mohammadham>`_  and base project developed by`Nekmo <https://github.com/Nekmo>`_ & `collaborators <https://github.com/Nekmo/telegram-upload/graphs/contributors>`_ would not be possible without
`Telethon <https://github.com/LonamiWebs/Telethon>`_, the library used as a Telegram client.

Telegram-upload is licensed under the `MIT license <https://github.com/mohammadham/telegram-uploader/blob/master/LICENSE>`_.

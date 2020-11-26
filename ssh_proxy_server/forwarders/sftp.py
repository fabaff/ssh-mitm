import uuid
import os
import logging
import paramiko
from enhancements.modules import Module
from paramiko import SFTPFile


class SFTPHandlerBasePlugin(Module):

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def close(self):
        pass

    def handle_data(self, data):
        return data


class SFTPHandlerPlugin(SFTPHandlerBasePlugin):
    pass


class SFTPHandlerStoragePlugin(SFTPHandlerPlugin):
    @classmethod
    def parser_arguments(cls):
        cls.PARSER.add_argument(
            '--sftp-storage',
            dest='sftp_storage_dir',
            required=True,
            help='directory to store files from scp'
        )

    def __init__(self, filename):
        super().__init__(filename)
        self.file_id = str(uuid.uuid4())
        logging.info("sftp file transfer: %s -> %s", filename, self.file_id)
        self.output_path = os.path.join(self.args.sftp_storage_dir, self.file_id)
        self.out_file = open(self.output_path, 'wb')

    def close(self):
        self.out_file.close()

    def handle_data(self, data):
        self.out_file.write(data)
        return data


class SFTPBaseHandle(paramiko.SFTPHandle):

    def __init__(self, plugin, filename, flags=0):
        super().__init__(flags)
        self.plugin = plugin(filename)
        self.writefile = None
        self.readfile = None

    def close(self):
        super().close()
        self.plugin.close()

    def read(self, offset, length):
        data = self.readfile.read(length)
        return self.plugin.handle_data(data)

    def write(self, offset, data):
        data = self.plugin.handle_data(data)
        self.writefile.write(data)
        return paramiko.SFTP_OK


class SFTPHandlerReplacePlugin(SFTPHandlerPlugin):
    """
    Replaces a SFTP transmitted File during transit
    """
    @classmethod
    def parser_arguments(cls):
        cls.PARSER.add_argument(
            '--sftp-replace',
            dest='sftp_replacement_file',
            required=True,
            help='file that is used for replacement'
        )

    def __init__(self, filename):
        super().__init__(filename)
        # self.file_id = filename # str(uuid.uuid4())
        logging.info("sftp file transfer detected: %s", filename)
        logging.info("intercepting sftp file, replacement: %s", self.args.sftp_replacement_file)
        self.replacement = open(self.args.sftp_replacement_file, "rb")
        self.out_file = open("test/copy.txt", "w+")

    def close(self):
        self.replacement.close()
        self.out_file.close()

    def handle_data(self, data):
        buf = self.replacement.read(32768)
        self.out_file.write(str(len(data)) + "\n")
        return buf


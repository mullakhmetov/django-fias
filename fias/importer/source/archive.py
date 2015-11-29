#coding: utf-8
from __future__ import unicode_literals, absolute_import

import rarfile
import tempfile
from progress.bar import Bar

try:
    from urllib.request import urlretrieve
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlretrieve
    HTTPError = IOError

from fias.importer.table import table_dbf_re, table_dbt_re

from .tablelist import TableList, TableListLoadingError
from .directory import DirectoryTableList
from .wrapper import RarArchiveWrapper

# Задаем UNRAR_TOOL глобально
rarfile.UNRAR_TOOL = 'unrar'


class BadArchiveError(TableListLoadingError):
    pass


class RetrieveError(TableListLoadingError):
    pass


class LocalArchiveTableList(TableList):
    wrapper_class = RarArchiveWrapper

    @staticmethod
    def unpack(archive):
        path = tempfile.mkdtemp()
        archive.extractall(path)
        return path

    def load_data(self, source):
        try:
            archive = rarfile.RarFile(source)
        except (rarfile.NotRarFile, rarfile.BadRarFile) as e:
            raise BadArchiveError('Archive: `{0}`, ver: `{1}` corrupted'
                                  ' or is not rar-archive'.format(self._src))

        if not archive.namelist():
            raise BadArchiveError('Archive: `{0}`, ver: `{1}` is empty'
                                  ''.format(source))

        first_name = archive.namelist()[0]
        if table_dbf_re.match(first_name) or table_dbt_re.match(first_name):
            path = LocalArchiveTableList.unpack(archive=archive)
            return DirectoryTableList.wrapper_class(source=path, is_temporary=True)

        return self.wrapper_class(source=archive)


class DlProgressBar(Bar):
    message = 'Downloading: '
    suffix = '%(index)d/%(max)d'
    hide_cursor = False


class RemoteArchiveTableList(LocalArchiveTableList):
    download_progress_class = DlProgressBar

    def load_data(self, source):
        progress = self.download_progress_class()

        def update_progress(count, block_size, total_size):
            progress.goto(int(count * block_size * 100 / total_size))

        try:
            src = urlretrieve(source, reporthook=update_progress)[0]
        except HTTPError as e:
            raise RetrieveError('Can not download data archive at url `{0}`. Error occured: "{1}"'.format(
                source, str(e)
            ))
        progress.finish()

        return super(RemoteArchiveTableList, self).load_data(source=src)
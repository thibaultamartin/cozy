from gi.repository import Gio

import cozy.ext.inject as inject
from peewee import SqliteDatabase

from cozy.control.offline_cache import OfflineCache
from cozy.media.files import Files
from cozy.media.player import Player
from cozy.report import reporter
from cozy.application_settings import ApplicationSettings
from cozy.architecture.singleton import Singleton
from cozy.control.db import get_db
from cozy.control.filesystem_monitor import FilesystemMonitor
from cozy.model.book import Book
from cozy.model.library import Library
from cozy.model.settings import Settings
from cozy.model.storage_block_list import StorageBlockList
from cozy.open_view import OpenView
from cozy.ui.book_detail_view import BookDetailView
from cozy.ui.library_view import LibraryView
from cozy.ui.main_view import CozyUI
from cozy.ui.search_view import SearchView
from cozy.ui.widgets.whats_new_window import WhatsNewWindow
from cozy.view_model.book_detail_view_model import BookDetailViewModel
from cozy.view_model.library_view_model import LibraryViewModel, LibraryViewMode
from cozy.view_model.search_view_model import SearchViewModel
from cozy.ui.settings import Settings as UISettings


class AppController(metaclass=Singleton):
    def __init__(self, main_window_builder, main_window):
        self.main_window: CozyUI = main_window
        self.main_window_builder = main_window_builder

        inject.configure_once(self.configure_inject)

        reporter.info("main", "startup")

        self.whats_new_window: WhatsNewWindow = WhatsNewWindow()

        self.library_view: LibraryView = LibraryView(main_window_builder)
        self.search_view: SearchView = SearchView(main_window_builder)
        self.book_detail_view: BookDetailView = BookDetailView(main_window_builder)

        self.library_view_model = inject.instance(LibraryViewModel)
        self.search_view_model = inject.instance(SearchViewModel)
        self.book_detail_view_model = inject.instance(BookDetailViewModel)

        self.search_view_model.add_listener(self._on_open_view)
        self.book_detail_view_model.add_listener(self._on_open_view)
        self.library_view_model.add_listener(self._on_open_view)
        self.library_view_model.add_listener(self._on_library_view_event)

        self.main_window.add_listener(self._on_main_window_event)

    def configure_inject(self, binder):
        binder.bind_to_provider(SqliteDatabase, get_db)
        binder.bind("MainWindow", self.main_window)
        binder.bind_to_constructor(Gio.Settings, lambda: Gio.Settings("com.github.geigi.cozy"))
        binder.bind_to_constructor(ApplicationSettings, lambda: ApplicationSettings())
        binder.bind_to_constructor(Settings, lambda: Settings())
        binder.bind_to_constructor("FilesystemMonitor", lambda: FilesystemMonitor())
        binder.bind_to_constructor(OfflineCache, lambda: OfflineCache())
        binder.bind_to_constructor(Player, lambda: Player())
        binder.bind_to_constructor(Library, lambda: Library())
        binder.bind_to_constructor(LibraryViewModel, lambda: LibraryViewModel())
        binder.bind_to_constructor(SearchViewModel, lambda: SearchViewModel())
        binder.bind_to_constructor(UISettings, lambda: UISettings())
        binder.bind_to_constructor(StorageBlockList, lambda: StorageBlockList())
        binder.bind_to_constructor(Files, lambda: Files())
        binder.bind_to_constructor(BookDetailViewModel, lambda: BookDetailViewModel())

    def open_author(self, author: str):
        self.library_view_model.library_view_mode = LibraryViewMode.AUTHOR
        self.library_view_model.selected_filter = author

    def open_reader(self, reader: str):
        self.library_view_model.library_view_mode = LibraryViewMode.READER
        self.library_view_model.selected_filter = reader

    def open_book(self, book: Book):
        self.book_detail_view_model.book = book

    def open_library(self):
        self.library_view_model.open_library()

    def _on_open_view(self, event, data):
        if event == OpenView.AUTHOR:
            self.open_author(data)
        elif event == OpenView.READER:
            self.open_reader(data)
        elif event == OpenView.BOOK:
            self.open_book(data)
        elif event == OpenView.LIBRARY:
            self.open_library()

    def _on_library_view_event(self, event: str, data):
        if event == "work-done":
            self.main_window.switch_to_playing()

    def _on_main_window_event(self, event: str, data):
        if event == "working":
            self.book_detail_view_model.lock_ui = data
        if event == "open_view":
            self._on_open_view(data, None)

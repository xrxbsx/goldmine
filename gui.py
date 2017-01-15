#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dragon5232's cool text editor."""
import sys
import asyncio
import os
import inspect
import re
import io
import random
from datetime import datetime
import signal
import traceback
import shutil
import logging
import discord
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import multiprocessing as mp
import __main__
__main__.core_file = __file__
import util.token as token

logging.basicConfig(level=logging.INFO)
about = """<h2>About Discordian</h2>
<h3>Version 0.0.1</h3>
This is Dragon5232's Discord client, Discordian.
It was designed to be fast and compact from the ground up.
<br><br>

<b>Todo</b>:
<ul>
 <li>Everything that Discord has</li>
</ul>

See Dragon5232's blog at <a href='https://blog.khronodragon.com/'>blog.khronodragon.com</a>
for more info.
<br><br>

This program is open-source, licensed under the MIT license.
You can find the code on <a href='https://github.com/Armored-Dragon/goldmine'>GitHub</a>.
Anyone is welcome to contribute to the project.<br><br>

Copyright \u00a92017 Dragon5232. Redistribution is allowed."""
path = os.path.abspath(sys.argv[0])
dir_path = os.path.dirname(path)
try:
    import qdarkstyle
    qdark_style = qdarkstyle.load_stylesheet_pyqt5()
    del qdarkstyle
except ImportError:
    qdark_style = ''
stylesheets = ['', qdark_style]

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    qApp.quit()

def error_handler(ex_type, ex, tb_obj):
    """Global exception handler.
    ex_type: type(exception)
    ex: exception
    tb_obj: exception.__traceback__"""
    print('Error:')
    tb = '\n'.join(traceback.format_tb(tb_obj))
    text = 'Traceback (most recent call last):\n' + tb + '\n' + ex_type.__name__ + ': ' + str(ex)
    print(text)
    QMessageBox.critical(QWidget(), 'Discordian: Error!', text)

class FatalError(QWidget):
    """Fatal error dialog."""
    def __init__(self, exp, parent=None):
        """Initialize Discordian."""
        super().__init__(parent)
        self.err = exp
        self.init_ui()

    def init_ui(self):
        """Initialize the window."""
        # x, y, width, height
        self.setGeometry(600, 600, 1024, 768)
        self.setWindowTitle('Discordian: Error')
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.process)
        self.main_wrap = QVBoxLayout()
        self.main_wrap.addWidget(QLabel(type(e).__name__ + ': ' + str(e)))
        self.main_wrap.addWidget(self.ok_btn)
        self.main_grid = QGridLayout()
        self.main_grid.addLayout(self.main_wrap, 0, 1)
        self.setLayout(self.main_grid)

class DiscordWindow(QMainWindow):
    """Main window wrapper for Discordian."""
    def __init__(self):
        super().__init__()
        self.css_index = 0
        self.setMinimumSize(260, 210)
        self.setGeometry(200, 200, 1024, 768)
        self.setWindowTitle('Discordian')
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        self.editor = DiscordMain(parent=self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.editor)
        self.widget.setLayout(self.layout)
        self.actions = []
        self.createActions()
        self.createMenus()
        self.statusBar().showMessage('Welcome to Discordian.')
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.discord = None

    def createActions(self):
        file_tb = self.addToolBar('File')
        self.actions.append([])
        l_act = QAction('&Start', self)
        l_act.setShortcuts([QKeySequence.New, QKeySequence.AddTab])
        l_act.setToolTip('Start')
        l_act.setStatusTip('Start the bot and login to Discord')
        l_act.triggered.connect(self.login)
        self.actions[0].append(l_act)

        o_action = QAction('&Open...', self)
        o_action.setShortcuts(QKeySequence.Open)
        o_action.setToolTip('Open')
        o_action.setStatusTip('Open a file or folder')
        o_action.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(o_action)

        s_action = QAction('&Save', self)
        s_action.setShortcuts(QKeySequence.Save)
        s_action.setToolTip('Save file')
        s_action.setStatusTip('Save the current file')
        s_action.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(s_action)

        sa_action = QAction('Save &As...', self)
        sa_action.setShortcuts(QKeySequence.SaveAs)
        sa_action.setToolTip('Save file as')
        sa_action.setStatusTip('Save the current file under a new name')
        sa_action.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(sa_action)

        sal_action = QAction('Save A&ll...', self)
        sal_action.setToolTip('Save all files')
        sal_action.setStatusTip('Save all opened files to disk')
        sal_action.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(sal_action)

        rs_act = QAction('&Restart', self)
        rs_act.setShortcuts(QKeySequence.Refresh)
        rs_act.setStatusTip('Restart Discordian')
        rs_act.setToolTip('Restart Discordian')
        rs_act.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(rs_act)

        x_act = QAction('E&xit', self)
        x_act.setShortcuts(QKeySequence.Quit)
        x_act.setStatusTip('Exit Discordian')
        x_act.setToolTip('Exit Discordian')
        x_act.triggered.connect(lambda: QMessageBox.information(self, 'Discordian: Info', 'Not implemented yet!'))
        self.actions[0].append(x_act)
        for i in range(2):
            file_tb.addAction(self.actions[0][i])
        file_tb.addAction(self.actions[0][2])

        edit_tb = self.addToolBar('Edit')
        self.actions.append([])
        cut_act = QAction('Cu&t', self)
        cut_act.setShortcuts(QKeySequence.Cut)
        cut_act.setToolTip('Cut')
        cut_act.setStatusTip('Cut the current selection\'s contents to the clipboard')
        cut_act.triggered.connect(lambda: self.editor.tabs.currentWidget().cut())
        self.actions[1].append(cut_act)

        cp_act = QAction('&Copy', self)
        cp_act.setShortcuts(QKeySequence.Copy)
        cp_act.setToolTip('Copy')
        cp_act.setStatusTip('Copy the current selection\'s contents to the clipboard')
        cp_act.triggered.connect(lambda: self.editor.tabs.currentWidget().copy())
        self.actions[1].append(cp_act)

        p_act = QAction('&Paste', self)
        p_act.setShortcuts(QKeySequence.Paste)
        p_act.setToolTip('Paste')
        p_act.setStatusTip('Paste the clipboard\'s contents into the current editor')
        p_act.triggered.connect(lambda: self.editor.tabs.currentWidget().paste())
        self.actions[1].append(p_act)

        u_act = QAction('&Undo', self)
        u_act.setShortcuts(QKeySequence.Undo)
        u_act.setToolTip('Undo')
        u_act.setStatusTip('Undo the previous action in the current editor')
        u_act.triggered.connect(lambda: self.editor.tabs.currentWidget().undo())
        self.actions[1].append(u_act)

        r_act = QAction('&Redo', self)
        r_act.setShortcuts(QKeySequence.Redo)
        r_act.setToolTip('Redo')
        r_act.setStatusTip('Redo the previous undoed action in the current editor')
        r_act.triggered.connect(lambda: self.editor.tabs.currentWidget().redo())
        self.actions[1].append(r_act)
        for a in self.actions[1]:
            edit_tb.addAction(a)
        edit_tb.addSeparator()
        s_act = QAction('Select &All', self)
        s_act.setShortcuts(QKeySequence.SelectAll)
        s_act.setToolTip('Select All')
        s_act.setStatusTip('Select all the text in the current editor')
        s_act.triggered.connect(lambda: self.editor.tabs.currentWidget().selectAll())
        self.actions[1].append(s_act)
        edit_tb.addAction(s_act)

        view_tb = self.addToolBar('View')
        self.actions.append([])
        f_act = QAction('Toggle Full&screen', self)
        f_act.setShortcuts(QKeySequence.FullScreen)
        f_act.setToolTip('Toggle Fullscreen')
        f_act.setStatusTip('Toggle fullscreen view of the window')
        f_act.triggered.connect(self.toggle_fullscreen)
        self.actions[2].append(f_act)

        d_act = QAction('&Cycle Themes', self)
        d_act.setShortcuts(QKeySequence.Underline)
        d_act.setToolTip('Cycle Themes')
        d_act.setStatusTip('Cycle between the editor\'s several built-in themes')
        d_act.triggered.connect(self.cycle_css)
        self.actions[2].append(d_act)
        for a in self.actions[2]:
            view_tb.addAction(a)

        w_act = QAction('&What\'s This', self)
        w_act.setShortcuts(QKeySequence.WhatsThis)
        w_act.setToolTip('Enter What\'s This')
        w_act.setStatusTip('Enter the interactive Qt What\'s This inspector.')
        w_act.triggered.connect(QWhatsThis.enterWhatsThisMode)
        self.whats_this_act = w_act

        self.actions.append([])
        a_act = QAction('&About Discordian', self)
        a_act.setToolTip('About Discordian')
        a_act.setStatusTip('Show some information about Discordian')
        a_act.triggered.connect(self.about)
        self.actions[3].append(a_act)

        aq_act = QAction('About &Qt', self)
        aq_act.setToolTip('About Qt')
        aq_act.setStatusTip('About the Qt library used by Discordian')
        aq_act.triggered.connect(QApplication.aboutQt)
        self.actions[3].append(aq_act)

    def createMenus(self):
        self.file_menu = self.menuBar().addMenu('&File')
        for i in range(5):
            self.file_menu.addAction(self.actions[0][i])
        self.file_menu.addSeparator()
        for i in range(5, len(self.actions[0])):
            self.file_menu.addAction(self.actions[0][i])

        self.edit_menu = self.menuBar().addMenu('&Edit')
        for i in range(5):
            self.edit_menu.addAction(self.actions[1][i])
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.actions[1][5])

        self.view_menu = self.menuBar().addMenu('&View')
        for a in self.actions[2]:
            self.view_menu.addAction(a)

        self.help_menu = self.menuBar().addMenu('&Help')
        self.help_menu.addAction(self.whats_this_act)
        self.help_menu.addSeparator()
        for a in self.actions[3]:
            self.help_menu.addAction(a)

    def about(self):
        QMessageBox.about(self, 'About Discordian', about)

    def cycle_css(self):
        """Cycle between the different CSS sheets."""
        self.css_index += 1
        try:
            qApp.setStyleSheet(stylesheets[self.css_index])
        except IndexError:
            self.css_index = 0
            qApp.setStyleSheet(stylesheets[0])

    def toggle_fullscreen(self):
        if self.windowState() & Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

    def login(self):
        self.discord = DiscordInterface()

class DiscordMain(QWidget):
    """The core of Discordian."""
    def __init__(self, parent=None):
        """Initialize Discordian."""
        super().__init__(parent)
        self.parent = parent
        self.untitled_index = 1
        self.init_ui()

    def init_ui(self):
        """Initialize the window."""
        # x, y, width, height
        self.setGeometry(200, 200, 1024, 768)
        self.setWindowTitle('Discordian')
        self.main_wrap = QHBoxLayout()
        self.server_list = QListView()
        self.server_model = QStringListModel()
        self.server_list.setModel(self.server_model)
        self.channel_list = QListView()
        self.channel_model = QStringListModel()
        self.channel_list.setModel(self.channel_model)
        self.msg_view = QTextEdit()
        self.font = QFont('Fira Code')
        self.font.setPointSize(12)
        self.font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        self.font.setStyleHint(QFont.Monospace)
        self.font.setFixedPitch(True)
        self.msg_view.setFont(self.font)
        self.main_wrap.addWidget(self.server_list)
        self.main_wrap.addWidget(self.channel_list)
        self.main_wrap.addWidget(self.msg_view)
        btn = QPushButton('test msg')
        btn.clicked.connect(lambda: self.parent.discord.send_message(self.parent.discord.gen_chan, 'test message'))
        self.main_wrap.addWidget(btn)
        self.main_grid = QGridLayout()
        self.main_grid.addLayout(self.main_wrap, 0, 1)
        self.setLayout(self.main_grid)

class FakeDiscordCallable:
    def __init__(self, name, interface, attr):
        self.name = name
        self.iface = interface
        self.attr = attr
    def __call__(self, *args, **kwargs):
        print('called fake')
        res = self.attr(*args, **kwargs)
        print('calling regular' + str(args))
        print(self.attr)
        if inspect.isawaitable(res):
            self.iface.loop.create_task(res)
class DiscordCall:
    def __init__(self, func, *args, **kwargs):
        self.coro = kwargs.get('call_is_coro', True)
        self.call = func
        self.args = args
        self.kwargs = kwargs

class DiscordInterface:
    """The interface to discord.py."""
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.bot = discord.Client()
        self.bot_task = None
        self.discord = None
        self.queue = None
        self.event = None
        self.gen_chan = {}
        self.thread = mp.Process(target=self.thread_start)
        self.thread.start()

    def thread_start(self):
        self.thread_init()
        self.thread_loop()

    def thread_init(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def thread_loop(self):
        self.loop.run_until_complete(self.async_loop())
        self.loop.close()

    def finish(self):
        self.loop.call_soon(self.bot.logout)

    async def async_loop(self):
        self.queue = asyncio.Queue()
        self.event = asyncio.Event()
        self.bot = discord.Client()
        @self.bot.event
        async def on_ready():
            print('Discord component ready!')
            self.gen_chan = {c.name: c for c in {s.name: s for s in self.bot.servers}['Codes \'n Skillz Hideout'].channels}['bot-testing']
            await self.bot.send_message(self.gen_chan, '**Discordian** GUI started.')
        await self.bot.start(*token.bot_token)
        self.loop.stop()

    def __getattr__(self, name):
        if name in dir(self):
            return getattr(self, name)
        else:
            if hasattr(self.bot, name):
                bot_attr = getattr(self.bot, name)
                if hasattr(bot_attr, '__call__'):
                    return FakeDiscordCallable(name, self, bot_attr)
                else:
                    return bot_attr

def quit_cleanup(window):
    if window.discord:
        window.discord.finish()

def main():
    """Main function."""
    sys.excepthook = error_handler
    try:
        signal.signal(signal.SIGINT, sigint_handler)
    except ValueError:
        print('Warning: couldn\'t start SIGINT (ctrl-c) handler.')
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheets[0])
    window = DiscordWindow()
    timer = QTimer()
    timer.start(60) # let interpreter run every 550ms
    timer.timeout.connect(lambda: None)
    window.show()
    window.raise_()
    window.setWindowState(window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    window.activateWindow() # mac...
    app.aboutToQuit.connect(lambda: quit_cleanup(window))
    exc = app.exec_()
    return exc

if __name__ == "__main__":
    sys.exit(main())

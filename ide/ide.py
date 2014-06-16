#!/usr/bin/env python3
#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#Depends on python3-gi, gir1.2-gtksource-3.0, and gir1.2-webkit-3.0

from gi.repository import Gtk, GtkSource, WebKit
from os import path

projectDir = path.expanduser("~/Projects")

class IDE(Gtk.Window):
    currFile = None
    def __init__(self):
        Gtk.Window.__init__(self, title="Raspberry IDEa")
        self.set_size_request(400, 400)
        self.connect("delete-event", Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.toolbar = Gtk.Toolbar();
        self.grid.attach(self.toolbar, 0, 0, 3, 1)

        self.rbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_PLAY) #Run
        self.rbutton.connect("clicked", self.run)
        self.toolbar.insert(self.rbutton, 0)

        self.sbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_STOP) #Stop
        self.sbutton.connect("clicked", self.stop)
        self.toolbar.insert(self.sbutton, 1)

        self.nbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_EDIT) #New
        self.nbutton.connect("clicked", self.newFile)
        self.toolbar.insert(self.nbutton, 2)

        self.obutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_DIRECTORY) #Open
        self.obutton.connect("clicked", self.openFile)
        self.toolbar.insert(self.obutton, 3)

        self.mainholder = Gtk.Paned()
        self.grid.attach(self.mainholder, 0, 1, 1, 1)
        self.codesplit = Gtk.Paned.new(Gtk.Orientation.VERTICAL)
        self.mainholder.pack1(self.codesplit, True, True)

        self.codebuffer = GtkSource.Buffer()
        self.code = GtkSource.View.new_with_buffer(self.codebuffer)
        self.code.set_auto_indent(True)
        self.code.set_show_line_numbers(True)
        self.code.set_tab_width(4)
        self.codebuffer.set_highlight_syntax(True)
        lm = GtkSource.LanguageManager()
        self.codebuffer.set_language(lm.get_language("python"))

        self.codescroller = Gtk.ScrolledWindow()
        self.codescroller.set_vexpand(True)
        self.codescroller.set_hexpand(True)
        self.codescroller.add_with_viewport(self.code)      
        self.codescroller.show_all()
        self.codesplit.pack1(self.codescroller, True, True)

        self.outputbuffer = GtkSource.Buffer()
        self.output = GtkSource.View.new_with_buffer(self.outputbuffer)
        self.outputscroller = Gtk.ScrolledWindow()
        self.outputscroller.set_vexpand(True)
        self.outputscroller.set_hexpand(True)
        self.outputscroller.add_with_viewport(self.output)
        self.outputscroller.show_all()
        self.codesplit.pack2(self.outputscroller, True, True)
        self.codesplit.set_position(300)

        self.webscroller = Gtk.ScrolledWindow()
        self.webscroller.set_vexpand(True)
        self.webscroller.set_hexpand(True)
        self.mainholder.pack2(self.webscroller, True, True)
        self.mainholder.set_position(200)

        self.browser = WebKit.WebView()
        self.webscroller.add_with_viewport(self.browser)
        self.browser.load_uri("http://google.com")

    def run(self, widget):
        print("Run")

    def stop(self, widget):
        print("Stop")

    def newFile(self, widget):
        print("New")

    def openFile(self, widget):
        dialog = Gtk.FileChooserDialog("Select Project", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_py = Gtk.FileFilter()
        filter_py.set_name("Python files")
        filter_py.add_mime_type("text/x-python")
        dialog.add_filter(filter_py)
        dialog.set_current_folder_uri("file://"+projectDir)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Open clicked")
            print("File selected: " + dialog.get_filename())
        dialog.destroy()

win = IDE()
win.show_all()
Gtk.main()

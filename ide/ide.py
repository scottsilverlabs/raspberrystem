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
#Depends on python3-gi, gir1.2-gtksource-3.0, gir1.2-webkit-3.0, and python3-pexpect

from gi.repository import Gtk, GtkSource, WebKit
from os import path, mkdir, chmod
from pexpect import spawn
import threading
import json

projectDir = path.expanduser("~/raspberryidea/")
settings = {"Theme ID" : "cobalt", "Browser Homepage" : "http://google.com", "Tab Width" : 4}

class NewFileDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Save File", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(150, 100)
        self.entry = Gtk.Entry()
        box = self.get_content_area()
        box.add(self.entry)
        self.show_all()

    def text(self):
        return self.entry.get_text()

class IDE(Gtk.Window):

    currFile = None
    currProc = None

    def __init__(self):
        Gtk.Window.__init__(self, title="Raspberry IDEa")
        self.set_size_request(400, 400)
        self.connect("delete-event", self.exit)

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
        self.codebuffer.set_highlight_syntax(True)
        self.codebuffer.set_text("#!/usr/bin/env python3\n")
        theme = GtkSource.StyleSchemeManager.new().get_scheme(settings["Theme ID"])
        self.codebuffer.set_style_scheme(theme)
        self.code = GtkSource.View.new_with_buffer(self.codebuffer)
        self.code.set_auto_indent(True)
        self.code.set_show_line_numbers(True)
        self.code.set_tab_width(settings["Tab Width"])
        self.code.set_indent_width(-1) #Sets it to tab width
        lm = GtkSource.LanguageManager()
        self.codebuffer.set_language(lm.get_language("python3"))

        self.codescroller = Gtk.ScrolledWindow()
        self.codescroller.set_vexpand(True)
        self.codescroller.set_hexpand(True)
        self.codescroller.add_with_viewport(self.code)      
        self.codescroller.show_all()
        self.codesplit.pack1(self.codescroller, True, True)

        self.outputbuffer = GtkSource.Buffer()
        self.outputbuffer.set_style_scheme(self.codebuffer.get_style_scheme())
        self.output = GtkSource.View.new_with_buffer(self.outputbuffer)
        self.output.set_editable(False)
        self.outputscroller = Gtk.ScrolledWindow()
        self.outputscroller.set_vexpand(True)
        self.outputscroller.set_hexpand(True)
        self.outputscroller.add_with_viewport(self.output)
        self.outputscroller.show_all()
        self.codesplit.pack2(self.outputscroller, True, True)
        self.codesplit.set_position(306)

        self.webscroller = Gtk.ScrolledWindow()
        self.webscroller.set_vexpand(True)
        self.webscroller.set_hexpand(True)
        self.mainholder.pack2(self.webscroller, True, True)
        self.mainholder.set_position(200)

        self.browser = WebKit.WebView()
        self.webscroller.add_with_viewport(self.browser)
        self.browser.load_uri(settings["Browser Homepage"])

    def exit(self, widget, event):
        self.save()
        Gtk.main_quit()

    def log(self, message):
        self.outputbuffer.insert(self.outputbuffer.get_end_iter(), message)
        curr = self.outputscroller.get_vadjustment()
        adj = Gtk.Adjustment.new(curr.get_upper(), curr.get_lower(), 
            curr.get_upper(), curr.get_step_increment(), 
            curr.get_page_increment(), curr.get_page_size()
        )
        self.outputscroller.set_vadjustment(adj)

    def printLoop(self):
        self.currProc = spawn(self.currFile)
        try:
            while self.currProc is not None and self.currProc.isalive():
                    output = self.currProc.read_nonblocking(2048).decode("utf-8")
                    if output != "^C":
                        self.log(output)
        except: pass
        self.currProc = None

    def run(self, widget):
        if self.currProc is None:
            self.code.set_editable(False)
            self.save()
            while self.currFile is None:
                self.save()
            t = threading.Thread(target=self.printLoop)
            t.start()
            self.code.set_editable(True)

    def stop(self, widget):
        if self.currProc is not None:
            print("Proc is none")
            self.code.set_editable(True)
            self.currProc.sendcontrol('c');

    def save(self):
        if self.currFile is None:
            dialog = NewFileDialog(self)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.currFile = projectDir+dialog.text().replace(' ','_')+".py"
            else:
                return
            dialog.destroy()
        f = open(self.currFile, "w")
        chmod(self.currFile, 555)
        f.write(self.codebuffer.get_text(self.codebuffer.get_start_iter(), self.codebuffer.get_end_iter(), True))
        f.close()

    def newFile(self, widget):
        dialog = NewFileDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if self.currFile is not None:
                self.save()
                self.currFile = projectDir+dialog.text().replace(' ','_')+".py"
                self.codebuffer.set_text("#!/usr/bin/env python3\n")                
        dialog.destroy()

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
            if self.currFile is not None:
                self.save()
            self.currFile = dialog.get_filename()
            f = open(self.currFile, "r")
            text = f.read()
            f.close()
            self.codebuffer.set_text(text)
        dialog.destroy()

if not path.isdir(projectDir):
    mkdir(projectDir)
if not path.exists(projectDir+"settings.conf"):
    f = open(projectDir+"settings.conf", "w")
    f.write(json.dumps(settings, sort_keys=True, indent=4))
    f.close()
f = open(projectDir+"settings.conf", "r")
settings = json.loads(f.read())
f.close()
win = IDE()
win.show_all()
Gtk.main()
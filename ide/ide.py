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
#Depends on python3-gi, gir1.2-gtksource-3.0, gir1.2-webkit-3.0, libkeybinder, and pexpect from pip-3
#TODO add icons in left gutter to indicate errors

from gi.repository import Gtk, GtkSource, Keybinder, WebKit, GLib, Gio, GObject
from os import path, mkdir, chmod
from pexpect import spawn
from time import time
import json, re

projectDir = path.expanduser("~/raspberryidea/")
settings = {"Theme ID" : "cobalt",
    "Browser Homepage" : "http://google.com",
    "Tab Width" : 4,
    "Undo Key" : "<Control>z",
    "Redo Key" : "<Control>y"
}

#File name chooser popup
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

    #Create the main GUI
    def __init__(self):
        self.currFile = None
        self.currProc = None
        self.loss = 0
        self.errorTags = []

        Gtk.Window.__init__(self, title="Raspberry IDEa")
        self.connect("notify::is-active", self.focuschange)
        self.set_size_request(400, 400)
        self.connect("delete-event", self.exit)

        grid = Gtk.Grid()
        self.add(grid)

        toolbar = Gtk.Toolbar();
        grid.attach(toolbar, 0, 0, 3, 1)

        self.rbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_PLAY) #Run
        self.rbutton.connect("clicked", self.run)
        toolbar.insert(self.rbutton, 0)

        nbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_EDIT) #New
        nbutton.connect("clicked", self.newFile)
        toolbar.insert(nbutton, 1)

        obutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_DIRECTORY) #Open
        obutton.connect("clicked", self.openFile)
        toolbar.insert(obutton, 2)

        mainholder = Gtk.Paned()
        grid.attach(mainholder, 0, 1, 1, 1)
        codesplit = Gtk.Paned.new(Gtk.Orientation.VERTICAL)
        mainholder.pack1(codesplit, True, True)

        self.codebuffer = GtkSource.Buffer()
        self.codebuffer.set_highlight_syntax(True)
        self.codebuffer.set_text("#!/usr/bin/env python3\n")
        theme = GtkSource.StyleSchemeManager.new().get_scheme(settings["Theme ID"])
        self.codebuffer.set_style_scheme(theme)
        lm = GtkSource.LanguageManager()
        self.codebuffer.set_language(lm.get_language("python3"))
        self.tagtable = self.codebuffer.get_tag_table()
        self.code = GtkSource.View.new_with_buffer(self.codebuffer)
        self.code.set_auto_indent(True)
        self.code.set_show_line_numbers(True)
        self.code.set_tab_width(settings["Tab Width"])
        self.code.set_indent_width(-1) #Sets it to tab width

        codescroller = Gtk.ScrolledWindow()
        codescroller.set_vexpand(True)
        codescroller.set_hexpand(True)
        codescroller.add_with_viewport(self.code)      
        codescroller.show_all()
        codesplit.pack1(codescroller, True, True)

        self.outputbuffer = GtkSource.Buffer()
        self.outputbuffer.set_style_scheme(self.codebuffer.get_style_scheme())
        self.output = GtkSource.View.new_with_buffer(self.outputbuffer)
        self.output.set_editable(False)
        self.outputscroller = Gtk.ScrolledWindow()
        self.outputscroller.set_vexpand(True)
        self.outputscroller.set_hexpand(True)
        self.outputscroller.add_with_viewport(self.output)
        self.outputscroller.show_all()
        self.outputscroller.connect("size-allocate", self.outputScroll)
        codesplit.pack2(self.outputscroller, True, True)
        codesplit.set_position(260)

        webscroller = Gtk.ScrolledWindow()
        webscroller.set_vexpand(True)
        webscroller.set_hexpand(True)
        mainholder.pack2(webscroller, True, True)
        mainholder.set_position(200)

        self.browser = WebKit.WebView()
        webscroller.add_with_viewport(self.browser)
        self.browser.load_uri(settings["Browser Homepage"])

        #Hotkeys
        Keybinder.init()
        self.hotkey(settings["Undo Key"], self.codebuffer.undo)
        self.hotkey(settings["Redo Key"], self.codebuffer.redo)

    def focused(self):
        print(self.props.is_active)
        print(int(time()) - self.loss)
        return self.props.is_active or int(time()) - self.loss < 2

    def focuschange(self, widget, event):
        if not self.props.is_active:
            self.loss = int(time())

    def runHotkey(self, key, method):
        #print(method)
        #print(self.focused)
        if self.focused():
            print("Performing method")
            method()

    def hotkey(self, keystring, method):
        print(keystring)
        print(method)
        Keybinder.bind(keystring, self.runHotkey, method)

    def hotkeyTest(self, hotkey):
        print(self.props.is_active)

    def exit(self, widget, event):
        self.save()
        Gtk.main_quit()

    #Called when self.outputscroller changes in size
    def outputScroll(self, widget, edata):
        adj = self.outputscroller.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    #Prints to the output window
    def log(self, message):
        self.outputbuffer.insert(self.outputbuffer.get_end_iter(), message)

    #Parses output sent by the print loop and highlights errors
    def errorEval(self, errString):
        errRegex = re.compile("\s+File \""+self.currFile+"\", line \d+.+Error:.+\r", flags=re.M|re.S)
        res = re.findall(errRegex, errString)
        for i in res:
            broken = i[:-1].split("\r\n")
            line = int(broken[0].split(", ")[1].split(" ")[1])
            #err = broken[3].split(": ")[1].capitalize()
            start = self.codebuffer.get_iter_at_line(line-1)
            end = self.codebuffer.get_iter_at_line(line-1)
            end.forward_line()
            text = start.get_text(end)
            start.forward_chars(len(text)-len(text.strip())-1)
            tag = self.codebuffer.create_tag(None, background="Red")
            self.errorTags.append(tag)
            self.codebuffer.apply_tag(tag, start, end)

    def printLoop(self, a, b, c): #To be honest, no idea what a, b, and c are supposed to be
        self.currProc = spawn(self.currFile)
        self.outputbuffer.set_text("")
        for tag in self.errorTags:
            self.tagtable.remove(tag)
        out = ""
        try:
            while self.currProc is not None and self.currProc.isalive():
                output = self.currProc.read_nonblocking(512).decode("utf-8")
                if output != "^C":
                    self.log(output)
                    out += output
        except Exception: 
            pass
        self.errorEval(out)
        self.currProc = None
        self.code.set_editable(True)
        self.rbutton.set_stock_id(Gtk.STOCK_MEDIA_PLAY)

    #Called when the run button is pressed
    def run(self, widget):
        if self.currProc is None:
            self.code.set_editable(False)
            self.save()
            self.rbutton.set_stock_id(Gtk.STOCK_MEDIA_STOP)
            while self.currFile is None:
                self.save()
            Gio.io_scheduler_push_job(self.printLoop, None, GLib.PRIORITY_DEFAULT, None)
        else:
            self.code.set_editable(True)
            self.currProc.sendcontrol('c');
            self.rbutton.set_stock_id(Gtk.STOCK_MEDIA_PLAY)

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
GObject.threads_init()
win = IDE()
win.show_all()
Gtk.main()

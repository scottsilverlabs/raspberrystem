#!/usr/bin/env python3
#TODO Copyright/License
#TODO Buttons

from gi.repository import Gtk, GtkSource
class IDE(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Raspberry IDEa")
        self.set_size_request(400, 400)
        self.connect("delete-event", Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.toolbar = Gtk.Toolbar();
        self.grid.attach(self.toolbar, 0, 0, 3, 1)

        self.rbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_PLAY)
        self.rbutton.connect("clicked", self.run)
        self.toolbar.insert(self.rbutton, 0)

        self.sbutton = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_STOP)
        self.sbutton.connect("clicked", self.stop)
        self.toolbar.insert(self.sbutton, 1)

        self.code = GtkSource.View()
        self.codebuffer = self.code.get_buffer()
        self.codebuffer.set_highlight_syntax(True)
        lm = GtkSource.LanguageManager()
        self.codebuffer.set_language(lm.get_language("python"))

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_vexpand(True)
        self.scrolledwindow.set_hexpand(True)
        self.grid.attach(self.scrolledwindow, 0, 1, 3, 1)
        self.scrolledwindow.add_with_viewport(self.code)      
        self.scrolledwindow.show_all()

    def run(self, widget):
        print("Run")

    def stop(self, widget):
        print("Stop")

win = IDE()
win.show_all()
Gtk.main()

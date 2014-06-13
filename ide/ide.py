#!/usr/bin/env python3
import wx

class ComputerologyIde(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(350, 250))

        toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        toolbar.SetToolBitmapSize((64, 64))
        img = wx.Image('icons/stop.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        stop_button = toolbar.AddSimpleTool(wx.ID_ANY, img, 'foo', '')
        toolbar.AddSeparator()
        img = wx.Image('icons/play.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        play_button = toolbar.AddSimpleTool(wx.ID_ANY, img, 'Exit', '')
        toolbar.Realize()

        self.splitter = wx.SplitterWindow(self, -1)
        panel1 = wx.Panel(self.splitter, -1)
        txt = wx.TextCtrl(panel1, style=wx.TE_MULTILINE)
        bsizer = wx.BoxSizer()
        bsizer.Add(txt, 1, wx.EXPAND)
        panel1.SetSizer(bsizer)
        panel1.SetBackgroundColour(wx.LIGHT_GREY)
        panel2 = wx.Panel(self.splitter, -1)
        wx.StaticText(panel2, -1,
                    "Whether you think that you can, or that you can't, you are usually right."
                    "\n\n Henry Ford",
            (100,100), style=wx.ALIGN_CENTRE)
        panel2.SetBackgroundColour(wx.WHITE)
        self.splitter.SplitVertically(panel1, panel2)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(toolbar, 0, wx.EXPAND, border=5)
        vbox.Add(self.splitter, 1, wx.EXPAND)

        self.splitter.SetSashGravity(0.5)
        self.SetAutoLayout(True)
        self.SetSizer(vbox)
        self.statusbar = self.CreateStatusBar()
        self.Layout()

        self.Bind(wx.EVT_TOOL, self.OnStop, id=stop_button.GetId())
        self.Bind(wx.EVT_TOOL, self.OnPlay, id=play_button.GetId())

    def OnStop(self, event):
        self.statusbar.SetStatusText('New Command')

    def OnPlay(self, event):
        self.Close()

class MyApp(wx.App):
    def OnInit(self):
        frame = ComputerologyIde(None, -1, 'toolbar.py')
        frame.Show(True)
        return True

if __name__ == "__main__":
    MyApp().MainLoop()


"""
Littera note-taking app

Author: programmingdesigner
Website: github.com/programmingdesigner/littera
Last modified: august 2022
"""

# 导入所需的模块
import os
import itertools
import webbrowser

# 导入wxPython和其他第三方库
import wx
import wx.richtext as rt
import wx.html as html
import wx.adv
import markdown
from xhtml2pdf import pisa

# 文件选择对话框的通配符
wildcard = "Markdown (*.md)|*.md|" \
           "Text (*.txt)|*.txt|"   \
           "All (*.*)|*.*"         \

# 定义查找对话框类
class findDlg(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Find", size=(300, 140))

        self.parent = parent  # 记录父窗口的引用

        panel = wx.Panel(self)  # 创建面板

        # 创建垂直和水平布局管理器
        vBox = wx.BoxSizer(wx.VERTICAL)
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        btnBox = wx.BoxSizer(wx.HORIZONTAL)

        # 创建并添加标签和文本输入框到水平布局中
        label = wx.StaticText(panel, label="Search for")
        self.textEntry = wx.TextCtrl(panel)
        hBox.Add(label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        hBox.Add(self.textEntry, proportion=1)

        # 将水平布局添加到垂直布局中
        vBox.Add(hBox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=16)
        vBox.Add((-1, 10))  # 添加空白空间

        # 创建查找按钮和查找下一个按钮
        findBtn = wx.Button(panel, wx.ID_OK, label="Find", size=(75, 25))
        findNextBtn = wx.Button(panel, label="Find Next", size=(75, 25))
        findBtn.SetDefault()  # 设置默认按钮

        # 将按钮添加到按钮布局中
        btnBox.Add(findBtn)
        btnBox.Add(findNextBtn, flag=wx.LEFT | wx.BOTTOM)

        # 将按钮布局添加到垂直布局中
        vBox.Add(btnBox, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=16)

        # 设置面板的布局管理器
        panel.SetSizer(vBox)

        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self.onClose)
        findBtn.Bind(wx.EVT_BUTTON, self.parent.onFind)
        findNextBtn.Bind(wx.EVT_BUTTON, self.onFindNext)

        self.Centre()  # 窗口居中

    def onClose(self, e):
        self.Destroy()  # 销毁对话框
        self.parent.findDlg = None  # 清空父窗口中的对话框引用
        self.parent.statusbar.SetStatusText("")  # 清空状态栏文本
        print("findDlg destroyed")  # 打印销毁消息

    def onFindNext(self, e):
        self.parent.textCtrl.SetInsertionPoint(next(self.parent.iterators))  # 设置插入点
        self.parent.textCtrl.ScrollIntoView(self.parent.textCtrl.GetInsertionPoint(), 13)  # 滚动到插入点
        self.parent.textCtrl.Update()  # 更新文本控制
        self.parent.textCtrl.Refresh()  # 刷新文本控制
        self.parent.textCtrl.SetFocus()  # 设置焦点


# 定义文本编辑器类
class textEditor(wx.Frame):
    def __init__(self, filename="untitled"):
        super(textEditor, self).__init__(None, size=(960, 540))

        # 属性
        self.dirname = "."  # 当前目录
        self.filename = filename  # 文件名
        self.modify = False  # 修改标志

        self.pos = 0  # 光标位置
        self.size = 0  # 文本大小

        self.appname = "Littera"  # 应用名
        self.appversion = "v1.0b"  # 应用版本

        icon = wx.Icon("favicon.ico", type=wx.BITMAP_TYPE_ICO)  # 设置应用图标

        self.findDlg = None  # 查找对话框引用

        # 字体
        wx.Font.AddPrivateFont("fonts/sans/NotoSans-Regular.ttf")
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                       underline=False, faceName="Noto Sans", encoding=wx.FONTENCODING_DEFAULT)
        labels = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                         underline=False, faceName="Noto Sans", encoding=wx.FONTENCODING_DEFAULT)

        # 用户界面
        self.splitter = wx.SplitterWindow(self, style=wx.SP_NO_XP_THEME)  # 创建分割窗口
        self.splitter.SetBackgroundColour("#F4F9F9")  # 设置背景颜色
        lPanel = wx.Panel(self.splitter)  # 左面板
        rPanel = wx.Panel(self.splitter)  # 右面板

        lPanel.SetBackgroundColour("#F4F9F9")  # 设置左面板背景颜色
        rPanel.SetBackgroundColour("#FFFFFF")  # 设置右面板背景颜色

        self.splitter.SplitVertically(lPanel, rPanel, -1)  # 垂直分割面板
        self.splitter.SetMinimumPaneSize(460)  # 设置最小面板大小

        lSizer = wx.BoxSizer(wx.VERTICAL)  # 左面板垂直布局
        rSizer = wx.BoxSizer(wx.VERTICAL)  # 右面板垂直布局

        # 用户界面 -- 左面板
        lLabel = wx.StaticText(lPanel, label="Text Editor")
        lLabel.SetFont(labels)  # 设置标签字体
        lLabel.SetForegroundColour("#9598A1")  # 设置标签前景色

        # 用户界面 -- 文本控制
        self.textCtrl = rt.RichTextCtrl(lPanel, -1, style=rt.RE_MULTILINE | wx.TE_RICH2 |
                                        wx.TE_NO_VSCROLL | wx.TE_WORDWRAP | wx.TE_AUTO_URL | wx.TE_PROCESS_TAB | wx.BORDER_NONE)
        self.textCtrl.SetEditable(True)  # 设置文本控制可编辑

        textAttr = rt.RichTextAttr()
        textAttr.SetFont(font)  # 设置文本字体
        textAttr.SetTextColour("#3C4245")  # 设置文本颜色
        textAttr.SetLineSpacing(12)  # 设置行间距
        textAttr.SetLeftIndent(60)  # 设置左缩进
        textAttr.SetRightIndent(80)  # 设置右缩进

        self.textCtrl.SetBasicStyle(textAttr)  # 设置文本基本样式
        self.textCtrl.SetBackgroundColour("#F4F9F9")  # 设置文本背景颜色

        self.mdExtensions = ['tables', 'sane_lists', 'fenced_code', 'smarty']  # Markdown扩展

        # 用户界面 -- 右面板
        rLabel = wx.StaticText(rPanel, label="HTML Preview")
        rLabel.SetFont(labels)  # 设置标签字体
        rLabel.SetForegroundColour("#9598A1")  # 设置标签前景色

        # 用户界面 -- HTML预览
        self.htmlPrev = html.HtmlWindow(rPanel)
        self.htmlPrev.SetStandardFonts(16, "Noto Sans")  # 设置预览字体

        # 用户界面 -- 配置布局
        lSizer.Add(lLabel, flag=wx.LEFT | wx.TOP, border=24)
        lSizer.Add((-1, 20))
        lSizer.Add(self.textCtrl, proportion=1, flag=wx.EXPAND)
        lPanel.SetSizer(lSizer)

        rSizer.Add(rLabel, flag=wx.LEFT | wx.TOP, border=24)
        rSizer.Add((-1, 20))
        rSizer.Add(self.htmlPrev, proportion=1, flag=wx.EXPAND)
        rPanel.SetSizer(rSizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)

        self.SetIcon(icon)  # 设置窗口图标
        self.Centre()  # 窗口居中

        # 功能
        self.setTitle()
        self.createMenu()
        self.setStatusBar()
        self.bindEvents()
        self.assignHotkeys()

    # 设置窗口标题
    def setTitle(self):
        super(textEditor, self).SetTitle(self.filename + " - " + self.appname)

    # 创建菜单
    def createMenu(self):
        menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        editMenu = wx.Menu()
        viewMenu = wx.Menu()
        helpMenu = wx.Menu()

        self.fileMenu_new = fileMenu.Append(wx.ID_NEW, "&New\tCtrl+N")
        self.fileMenu_open = fileMenu.Append(wx.ID_OPEN, "&Open\tCtrl+O")
        fileMenu.AppendSeparator()
        self.fileMenu_save = fileMenu.Append(wx.ID_SAVE, "&Save\tCtrl+S")
        self.fileMenu_saveas = fileMenu.Append(wx.ID_SAVEAS, "Save &As\tShift+Ctrl+S")
        fileMenu.AppendSeparator()
        self.fileMenu_print = fileMenu.Append(wx.ID_PRINT, "&Print\tCtrl+P")
        fileMenu.AppendSeparator()
        self.fileMenu_exit = fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt+F4")

        self.editMenu_undo = editMenu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z")
        self.editMenu_redo = editMenu.Append(wx.ID_REDO, "&Redo\tShift+Ctrl+Z")
        editMenu.AppendSeparator()
        self.editMenu_cut = editMenu.Append(wx.ID_CUT, "Cu&t\tCtrl+X")
        self.editMenu_copy = editMenu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        self.editMenu_paste = editMenu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        editMenu.AppendSeparator()
        self.editMenu_find = editMenu.Append(wx.ID_FIND, "&Find\tCtrl+F")
        self.editMenu_replace = editMenu.Append(wx.ID_REPLACE, "Rep&lace\tCtrl+H")

        self.viewMenu_markdown = viewMenu.AppendCheckItem(wx.ID_ANY, "Render &Markdown\tCtrl+M")
        self.viewMenu_pdf = viewMenu.Append(wx.ID_ANY, "Save as &PDF\tShift+Ctrl+P")

        self.helpMenu_about = helpMenu.Append(wx.ID_ABOUT, "&About")

        menuBar.Append(fileMenu, "&File")
        menuBar.Append(editMenu, "&Edit")
        menuBar.Append(viewMenu, "&View")
        menuBar.Append(helpMenu, "&Help")

        self.SetMenuBar(menuBar)

    # 设置状态栏
    def setStatusBar(self):
        self.statusbar = self.CreateStatusBar()

    # 绑定事件
    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onNew, self.fileMenu_new)
        self.Bind(wx.EVT_MENU, self.onOpen, self.fileMenu_open)
        self.Bind(wx.EVT_MENU, self.onSave, self.fileMenu_save)
        self.Bind(wx.EVT_MENU, self.onSaveAs, self.fileMenu_saveas)
        self.Bind(wx.EVT_MENU, self.onPrint, self.fileMenu_print)
        self.Bind(wx.EVT_MENU, self.onExit, self.fileMenu_exit)

        self.Bind(wx.EVT_MENU, self.onUndo, self.editMenu_undo)
        self.Bind(wx.EVT_MENU, self.onRedo, self.editMenu_redo)
        self.Bind(wx.EVT_MENU, self.onCut, self.editMenu_cut)
        self.Bind(wx.EVT_MENU, self.onCopy, self.editMenu_copy)
        self.Bind(wx.EVT_MENU, self.onPaste, self.editMenu_paste)
        self.Bind(wx.EVT_MENU, self.onFind, self.editMenu_find)
        self.Bind(wx.EVT_MENU, self.onReplace, self.editMenu_replace)

        self.Bind(wx.EVT_MENU, self.onToggleMarkdown, self.viewMenu_markdown)
        self.Bind(wx.EVT_MENU, self.onSaveAsPDF, self.viewMenu_pdf)

        self.Bind(wx.EVT_MENU, self.onAbout, self.helpMenu_about)

    # 分配快捷键
    def assignHotkeys(self):
        pass

    # 事件处理函数
    def onNew(self, e):
        self.textCtrl.Clear()
        self.filename = "untitled"
        self.setTitle()
        self.statusbar.SetStatusText("New file created")
        print("New file created")

    def onOpen(self, e):
        openFileDialog = wx.FileDialog(self, "Open", self.dirname, "", wildcard, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return

        self.dirname = openFileDialog.GetDirectory()
        self.filename = openFileDialog.GetFilename()
        filepath = os.path.join(self.dirname, self.filename)

        with open(filepath, "r") as file:
            self.textCtrl.SetValue(file.read())

        self.setTitle()
        self.statusbar.SetStatusText(f"Opened {self.filename}")
        print(f"Opened {self.filename}")

    def onSave(self, e):
        if self.filename == "untitled":
            self.onSaveAs(e)
        else:
            self.saveFile(self.filename)

    def onSaveAs(self, e):
        saveFileDialog = wx.FileDialog(self, "Save As", self.dirname, "", wildcard, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return

        self.dirname = saveFileDialog.GetDirectory()
        self.filename = saveFileDialog.GetFilename()
        self.saveFile(self.filename)

    def saveFile(self, filename):
        filepath = os.path.join(self.dirname, filename)
        with open(filepath, "w") as file:
            file.write(self.textCtrl.GetValue())

        self.setTitle()
        self.statusbar.SetStatusText(f"Saved {self.filename}")
        print(f"Saved {self.filename}")

    def onPrint(self, e):
        pass

    def onExit(self, e):
        self.Close(True)

    def onUndo(self, e):
        self.textCtrl.Undo()

    def onRedo(self, e):
        self.textCtrl.Redo()

    def onCut(self, e):
        self.textCtrl.Cut()

    def onCopy(self, e):
        self.textCtrl.Copy()

    def onPaste(self, e):
        self.textCtrl.Paste()

    def onFind(self, e):
        if not self.findDlg:
            self.findDlg = findDlg(self)
        self.findDlg.Show()
        self.statusbar.SetStatusText("Find dialog opened")
        print("Find dialog opened")

    def onReplace(self, e):
        pass

    def onToggleMarkdown(self, e):
        if self.viewMenu_markdown.IsChecked():
            self.renderMarkdown()
        else:
            self.htmlPrev.SetPage("")

    def onSaveAsPDF(self, e):
        html = self.htmlPrev.GetParser().GetSource()
        filename = wx.FileSelector("Save as PDF", wildcard="*.pdf", flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if filename:
            if not filename.endswith(".pdf"):
                filename += ".pdf"

            with open(filename, "wb") as file:
                pisa.CreatePDF(html, dest=file)

            self.statusbar.SetStatusText(f"Saved as {filename}")
            print(f"Saved as {filename}")

    def onAbout(self, e):
        wx.MessageBox(f"{self.appname} {self.appversion}\n\n"
                      "A minimalistic markdown text editor with HTML preview and PDF export.",
                      "About", wx.OK | wx.ICON_INFORMATION)

    def renderMarkdown(self):
        md = markdown.Markdown(extensions=self.mdExtensions)
        html = md.convert(self.textCtrl.GetValue())
        self.htmlPrev.SetPage(html)
        self.statusbar.SetStatusText("Markdown rendered")
        print("Markdown rendered")


if __name__ == "__main__":
    app = wx.App(False)
    frame = textEditor()
    frame.Show()
    app.MainLoop()

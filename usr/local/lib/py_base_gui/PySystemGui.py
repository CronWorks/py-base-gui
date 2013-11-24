from py_base.JobOutput import JobOutput
from py_base.PySystem import PySystem
from py_base.PySystemMock import PySystemMock

from os.path import dirname, isfile, realpath, sep
from re import search
from threading import Thread

import gobject
import pygtk
pygtk.require('2.0')
import gtk


class GuiWindow:
    PADDING_GENERAL = 10

    out = None
    rootWindow = None
    system = None

    # result codes:
    # None: process has not run, or is still running
    # False: failed command, or user cancelled
    # True: OK, or general success
    # String (including ''): User input for successful result where user was asked a question
    result = None

    windowImageMaxHeight = 200
    windowContentWidth = 400
    windowTextRequestHeight = 200

    # {'Event_String': eventHandlerFunction}
    keyPressDefaultActions = {}

    def __init__(self, windowTitle, out, system):
        self.out = out
        self.system = system
        self.rootWindow = gtk.Dialog(windowTitle)
        self.rootWindow.connect("delete_event", self.cancel)
        self.rootWindow.vbox.set_spacing(self.PADDING_GENERAL)

    def getScaledImage(self, imageFileName):
        pixbuf = gtk.gdk.pixbuf_new_from_file(imageFileName)
        pixbuf = self.scalePixbuf(pixbuf)
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)
        return image

    def getAnimation(self, imageFileName):
        pixbuf = gtk.gdk.PixbufAnimation(imageFileName)
        image = gtk.Image()
        image.set_from_animation(pixbuf)
        return image

    def scalePixbuf(self, pixbuf):
        originalHeight = pixbuf.get_height()
        originalWidth = pixbuf.get_width()
        scalingRatio = float(self.windowContentWidth) / originalWidth
        if float(self.windowImageMaxHeight) / originalHeight < scalingRatio:
            scalingRatio = float(self.windowImageMaxHeight) / originalHeight
        pixbuf = pixbuf.scale_simple(int(scalingRatio * originalWidth), int(scalingRatio * originalHeight), gtk.gdk.INTERP_BILINEAR)
        return pixbuf

    def addOkButton(self):
        ok = self.rootWindow.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        ok.connect("clicked", self.ok, None)
        ok.show()

    def ok(self, widget=None, data=None):
        self.out.put('OK: GTK window finishing with successful result', self.out.LOG_LEVEL_VERBOSE)
        self.result = True
        self.rootWindow.destroy()
        gtk.main_quit()

    def addCancelButton(self):
        cancel = self.rootWindow.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        cancel.connect("clicked", self.cancel, None)
        cancel.show()

    def cancel(self, widget=None, data=None):
        self.out.put('CANCEL: closing GTK window now', self.out.LOG_LEVEL_VERBOSE)
        self.result = False
        self.rootWindow.destroy()
        gtk.main_quit()

    def listenToDefaultActions(self, widget):
        widget.connect("key_press_event", self.keyPressDefaultAction)

    # process a keypress event based on the keyPressDefaultActions map
    def keyPressDefaultAction(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname in self.keyPressDefaultActions:
            action = self.keyPressDefaultActions[keyname]
            action(widget, event)

    def show(self):
        'returns boolean success value'
        self.rootWindow.show()
        gtk.main()
        return self.result


class InputDialog(GuiWindow):
    textInput = None
    getTextResult = None  # this will be set to the text-retrieval function when a text input widget is created

    def __init__(self, windowTitle, out, system, label='Input', defaultValue='', imageFileName='', freeText=''):
        GuiWindow.__init__(self, windowTitle, out, system)
        self.keyPressDefaultActions['KP_Enter'] = self.ok  # numpad
        self.keyPressDefaultActions['Return'] = self.ok  # keyboard

        if imageFileName:
            if isfile(imageFileName):
                image = self.getScaledImage(imageFileName)
                self.rootWindow.vbox.pack_start(image, False, False)
                image.show()
            elif self.out:
                self.out.put('Unable to find image file: ' + imageFileName)

        if freeText:
            freeTextScrolledWindow = gtk.ScrolledWindow()
            freeTextScrolledWindow.set_size_request(self.windowContentWidth, self.windowTextRequestHeight)

            freeTextBuffer = gtk.TextBuffer()
            freeTextBuffer.set_text(freeText)
            freeTextView = gtk.TextView(freeTextBuffer)

            freeTextScrolledWindow.add(freeTextView)

            freeTextVbox = gtk.VBox()
            freeTextVbox.set_border_width(10)
            freeTextVbox.pack_start(freeTextScrolledWindow)
            self.rootWindow.vbox.pack_start(freeTextVbox, True, True, 0)

            freeTextVbox.show()
            freeTextScrolledWindow.show()
            freeTextView.show()

        entryLabel = gtk.Label(label)
        self.rootWindow.vbox.pack_start(entryLabel)
        entryLabel.show()

        if type(defaultValue) == list:
            self.textInput = gtk.combo_box_entry_new_text()
            for item in defaultValue:
                self.textInput.append_text(item)
            self.textInput.set_active(0)

            # use gtk.ComboBoxText.get_active_text() to get the value from the text box
            self.getTextResult = self.textInput.get_active_text

        else:
            self.textInput = gtk.Entry()
            self.textInput.set_text(defaultValue)
            self.textInput.select_region(0, len(defaultValue))
            # use gtk.Entry.get_text() to get the value from the text box
            self.getTextResult = self.textInput.get_text

        self.rootWindow.vbox.pack_start(self.textInput)
        self.textInput.show()
        self.textInput.set_flags(gtk.CAN_FOCUS)
        self.rootWindow.set_focus(self.textInput)
        self.listenToDefaultActions(self.textInput)

        box = gtk.HBox(True, self.PADDING_GENERAL)
        box.show()

        self.rootWindow.vbox.add(box)
        self.addCancelButton()
        self.addOkButton()

    def ok(self, widget=None, data=None):
        self.result = self.getTextResult().strip()
        self.out.put('OK: finishing with successful result: %s' % self.result, self.out.LOG_LEVEL_VERBOSE)
        self.rootWindow.destroy()
        gtk.main_quit()


class PleaseWait(GuiWindow):
    CALLBACK_TIMEOUT_MS = 200
    DEFAULT_MESSAGE = 'Please Wait...'
    LOADER_ANIMATION_FILENAME = dirname(realpath(__file__)) + sep + 'loader.gif'

    childProcess = None
    outputFromChildProcess = ''
    timeoutId = None

    def __init__(self, windowTitle, out, system, childProcess, message=DEFAULT_MESSAGE):
        GuiWindow.__init__(self, windowTitle, out, system)
        self.out.put('PleaseWait started with child process %s' % childProcess, self.out.LOG_LEVEL_VERBOSE)
        self.childProcess = childProcess
        self.registerTimeout()

        # show the spinner
        image = self.getAnimation(self.LOADER_ANIMATION_FILENAME)
        self.rootWindow.vbox.pack_start(image, False, False)
        image.show()

        entryLabel = gtk.Label(message)
        self.rootWindow.vbox.pack_start(entryLabel)
        entryLabel.show()

        self.addCancelButton()

    def registerTimeout(self):
        # check the status of the callback thread every X milliseconds
        self.timeoutId = gobject.timeout_add(self.CALLBACK_TIMEOUT_MS, self.timeoutCallback)

    def timeoutCallback(self):
        # is the childProcess still running?
        self.result = self.childProcess.poll()

        if self.result == None:
            # The process is still running.
            # returning True will keep this timeoutCallback active.
            return True

        # the process has finished.
        self.outputThread.join()  # make sure we've collected all our nuts

        if self.result == 0:
            # child process has terminated successfully
            self.ok()  # sets success result
            return False  # kills the timeoutCallback

        # child process has terminated unsuccessfully
        self.cancel()  # sets failure result
        return False  # kills the timeoutCallback

    def cancel(self, widget=None, data=None):
        GuiWindow.cancel(self, widget, data)
        gobject.source_remove(self.timeoutId)  # prevent the timeout callback from firing again
        try:
            self.childProcess.terminate()
        except:
            # child process may have already terminated
            pass
        self.outputThread.join()  # make sure we've collected all our nuts

    def show(self, regex=None, logLevel=JobOutput.LOG_LEVEL_COMMON):
        'returns boolean success value'
        self.outputThread = Thread(target=self.readProcessOutput, args=(regex, logLevel))
        self.outputThread.start()
        GuiWindow.show(self)
        return self.result

    def readProcessOutput(self, regex, logLevel):
        # runs in a separate thread
        shouldContinue = True
        while shouldContinue:
            if self.result == None:
                # process is still running, so assume there will be more input
                shouldContinue = True
                line = self.childProcess.stdout.readline()
            else:
                # process has already stopped, so finish when the pipe is empty
                line = self.childProcess.stdout.readline()
                shouldContinue = line != ''
            if line != '':
                if regex == None or search(regex, line):
                    self.outputFromChildProcess += line
                    self.out.put(line.rstrip('\r\n'), logLevel)
                else:
                    # log all non-empty output, but if it didn't make the regex then log it at the lowest level.
                    self.out.put(line.rstrip('\r\n'), self.out.LOG_LEVEL_DEBUG)


class PySystemGui(PySystem):
    def getUserInput(self, question, defaultValue=''):
        if defaultValue != '':
            question = '%s [%s]' % (question, defaultValue)
        dialog = InputDialog(self.applicationName, self.out, self, label=question + ':', defaultValue=defaultValue)
        result = dialog.show()
        if result == '':
            result = defaultValue
        return result


    def runCommandWithPleaseWaitSpinner(self, command, workingDir=None, regex=None, err=None, logLevel=JobOutput.LOG_LEVEL_COMMON, message=PleaseWait.DEFAULT_MESSAGE):
        process = self.startCommandProcess(command, workingDir, err)
        pleaseWait = PleaseWait(self.applicationName, self.out, self, process, message)
        result = pleaseWait.show(regex, logLevel)
        if not result:
            # process error, or the user pressed cancel
            return False
        return pleaseWait.outputFromChildProcess

class PySystemMockGui(PySystemMock, PySystemGui):
    # adds the function runCommandWithPleaseWaitSpinner() to PySystemMock
    pass

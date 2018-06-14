import serial
import wx
import threading
import serial.tools.list_ports
import pynput
import re


EVT_PULLED_PLUG = wx.NewId()
EVT_THREAD_ABORTED = wx.NewId()


## Make 2 new events so the communication thread can signal the main GUI.
class PulledPlugEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_PULLED_PLUG)
        



class ThreadAbortedEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_THREAD_ABORTED)
        


## Class taken from https://wiki.wxpython.org/LongRunningTasks and modified.
# Thread class that executes processing
class CommunicationThread(threading.Thread):
    """Communication Thread Class."""
    def __init__(self, serial_connection):
        """Init Communication Thread Class."""
        threading.Thread.__init__(self)
        self.serial_connection = serial_connection
        self.selected_port = serial_connection.selected_port
        self.want_abort = False
        self.daemon = True
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start() 
    
    
    def run(self):
        """Run Communication Thread."""
        
        while not self.want_abort:
            try:
                data = self.serial_connection.ComPort.readline()
                
                
                if len(data) > 0:
                    data = str(data)
                    data = re.sub(r" ", "", data)
                    data = re.search(r"(-?\d*\.\d*)", data)
                    data = data.group()
        
                    self.serial_connection.keyboard.type(data)
                    self.serial_connection.keyboard.press(pynput.keyboard.Key.enter)
                    self.serial_connection.keyboard.release(pynput.keyboard.Key.enter)
            
            except serial.serialutil.SerialException:
                wx.PostEvent(self.serial_connection, PulledPlugEvent())
                return
                
        
        wx.PostEvent(self.serial_connection, ThreadAbortedEvent())
    
    
    def abort(self):
        """Abort Communication Thread."""
        # Method for use by main thread to signal an abort.
        self.want_abort = True 

        


class Wedge_GUI(wx.Frame):
    
    
    def __init__(self, parent, title, *args, **kwargs):
        
        super(Wedge_GUI, self).__init__(parent, title=title, size = (400, 275), *args, **kwargs) 
        
        ## Set up the event handlers for the communication thread.
        self.Connect(-1, -1, EVT_PULLED_PLUG, self.pulled_plug)
        self.Connect(-1, -1, EVT_THREAD_ABORTED, self.thread_aborted)
        
        self.InitUI()
        self.Centre()
        self.Show()

        
    def InitUI(self):
        panel = wx.Panel(self)
        settings_flexbox = wx.FlexGridSizer(5, 2, 10, 10)
        
        ## Add a status bar to the bottom for reporting messages.
        #self.statusbar = self.CreateStatusBar()
        
        ## Set default values for serial settings.
        ## Possible future improvement might be to make a seperate class to hold these values.
        self.baud_rate = 9600
        self.parity = "O"
        self.byte_size = 8
        self.stop_bits = 1
        self.selected_port = ""
        
        self.communication_thread = None
        self.keyboard = pynput.keyboard.Controller()
        
        
        ## Add drop down to select the port to use.
        port_st = wx.StaticText(panel, label="Port:")
        port_dropdown = wx.ComboBox(panel, style = wx.CB_DROPDOWN | wx.CB_READONLY)
        port_dropdown.Bind(wx.EVT_COMBOBOX, self.on_port_selection)
        port_dropdown.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.on_port_dropdown)
        
        ## Add dropdown to select the baud rate.
        baud_rate_st = wx.StaticText(panel, label="Baud Rate:")
        baud_rate_standards = ["300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "28800", "38400", "57600", "115200"]
        baud_rate_dropdown = wx.ComboBox(panel, value = "9600", style = wx.CB_DROPDOWN | wx.CB_READONLY, choices = baud_rate_standards)
        baud_rate_dropdown.Bind(wx.EVT_COMBOBOX, self.on_baud_rate_selection)
        ## Not giving the user the abaility to set the baud rate manually because I don't want to handle the input right now.
        #baud_rate_dropdown.Bind(wx.EVT_TEXT, self.on_manual_baud_rate)
        
        
        ## Add dropdown to select the byte size.
        byte_size_st = wx.StaticText(panel, label="Byte Size:")
        byte_size_standards = ["5", "6", "7", "8", "9"]
        byte_size_dropdown = wx.ComboBox(panel, value = "8", style = wx.CB_DROPDOWN | wx.CB_READONLY, choices = byte_size_standards)
        byte_size_dropdown.Bind(wx.EVT_COMBOBOX, self.on_byte_size_selection)
        
        
        ## Add dropdown to select parity.
        parity_st = wx.StaticText(panel, label="Parity:")
        parity_standards = ["Even", "Odd", "None", "Mark", "Space"]
        parity_dropdown = wx.ComboBox(panel, value = "Odd", style = wx.CB_DROPDOWN | wx.CB_READONLY, choices = parity_standards)
        parity_dropdown.Bind(wx.EVT_COMBOBOX, self.on_parity_selection)
        
        
        ## Add dropdown to select stop bits.
        stop_bits_st = wx.StaticText(panel, label="Stop Bits:")
        stop_bits_standards = ["1", "1.5", "2"]
        stop_bits_dropdown = wx.ComboBox(panel, value = "1", style = wx.CB_DROPDOWN | wx.CB_READONLY, choices = stop_bits_standards)
        stop_bits_dropdown.Bind(wx.EVT_COMBOBOX, self.on_stop_bits_selection)
        
        
        settings_flexbox.AddMany([(port_st, wx.ALIGN_BOTTOM | wx.EXPAND), (port_dropdown), 
                                  (baud_rate_st, wx.ALIGN_BOTTOM | wx.EXPAND), (baud_rate_dropdown), 
                                  (byte_size_st, wx.ALIGN_BOTTOM | wx.EXPAND), (byte_size_dropdown), 
                                  (parity_st, wx.ALIGN_BOTTOM | wx.EXPAND), (parity_dropdown), 
                                  (stop_bits_st, wx.ALIGN_BOTTOM | wx.EXPAND), (stop_bits_dropdown)])
        
        
        
        ## Add button to toggle communication with the serial port.
        self.toggle_button = wx.ToggleButton(panel, label = "Click to Connect")
        self.toggle_button.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggle)
        
        main_vbox = wx.BoxSizer(wx.VERTICAL)
        
        main_vbox.Add(settings_flexbox, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        main_vbox.Add(self.toggle_button, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        

        panel.SetSizer(main_vbox)
        panel.Fit()
        
        
        
        
    def OnToggle(self, event):
        
        button = event.GetEventObject()
        
        
        if button.GetValue() == True:
            
            if self.selected_port == "":
                message = "No Port Selected"
                msg_dlg = wx.MessageDialog(None, message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
                msg_dlg.ShowModal()
                msg_dlg.Destroy()
            
                button.SetValue(False)
                return
            
            
            try:
                ComPort = serial.Serial(self.selected_port)
                ComPort.baudrate = self.baud_rate
                ComPort.bytesize = self.byte_size
                ComPort.parity = self.parity
                ComPort.stopbits = self.stop_bits
                ComPort.timeout = 2
                
                self.ComPort = ComPort

            except serial.serialutil.SerialException:
                message = "Device Not Connected"
                msg_dlg = wx.MessageDialog(None, message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
                msg_dlg.ShowModal()
                msg_dlg.Destroy()
                
                button.SetValue(False)
                return
            
            if not self.communication_thread:
                self.communication_thread = CommunicationThread(self)
                button.SetLabel("Click to Disconnect")
            else:
                message = "Communication thread already started, something seriously wrong happened."
                msg_dlg = wx.MessageDialog(None, message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
                msg_dlg.ShowModal()
                msg_dlg.Destroy()
        
        else:
            
            if self.communication_thread:
                self.communication_thread.abort()
            else:
                message = "Communication thread already aborted, something seriously wrong happened."
                msg_dlg = wx.MessageDialog(None, message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
                msg_dlg.ShowModal()
                msg_dlg.Destroy()
            
    


    def on_port_selection(self, event):
        dropdown = event.GetEventObject()
        self.selected_port = dropdown.GetValue()



            
            
    def on_port_dropdown(self, event):
        dropdown = event.GetEventObject()
        ports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        ports = [name for name, value1, value2 in ports]
        dropdown.Clear()
        dropdown.AppendItems(ports)
        
        
  


    def on_baud_rate_selection(self, event):
        dropdown = event.GetEventObject()
        self.baud_rate = int(dropdown.GetValue())




## Not giving the user the option to manuall set baud rate because I don't want to filter the input right now.
#    def on_manual_baud_rate(self, event):
#        dropdown = event.GetEventObject()
#        self.baud_rate = int(dropdown.GetValue())





    def on_byte_size_selection(self, event):
        dropdown = event.GetEventObject()
        self.byte_size = int(dropdown.GetValue())


        


    def on_parity_selection(self, event):
        dropdown = event.GetEventObject()
        self.parity = dropdown.GetValue()


        
        

    def on_stop_bits_selection(self, event):
        dropdown = event.GetEventObject()
        self.stop_bits = float(dropdown.GetValue())



        
    def pulled_plug(self, event):
        self.ComPort.close()
        
        message = "Device Disconnected"
        msg_dlg = wx.MessageDialog(None, message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
        msg_dlg.ShowModal()
        msg_dlg.Destroy()
        
        self.toggle_button.SetValue(False)
        self.toggle_button.SetLabel("Click to Connect")
        
        self.communication_thread = None
   


    def thread_aborted(self, event):
        self.ComPort.close()
        
        self.toggle_button.SetValue(False)
        self.toggle_button.SetLabel("Click to Connect")
        
        self.communication_thread = None

    


def main():

    ex = wx.App(False)
    Wedge_GUI(None, title = "Keyboard Wedge")
    ex.MainLoop()    


if __name__ == '__main__':
    main()



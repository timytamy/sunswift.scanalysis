from ScandalWidgets import *

import Driver
import Configurator

from Drivers import ScandalDriver

import Scandal

import Graphing
import GraphingMPL

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import time

class TrackerStatusIndicator(NewListener, gtk.Label):
    def __init__(self, store, nodename, channame):
        NewListener.__init__(self, store, nodename, channame)
        gtk.Label.__init__(self, str="status")

    # Ugly!! Get rid of magic numbers. 
    def deliver(self, pkt):
        NewListener.deliver(self, pkt)
        string = ""
        if self.last_packet.get_raw_value() & 0x01:
            string = string + "T"
        if self.last_packet.get_raw_value() & 0x02: 
            string = "I" + string
        if self.last_packet.get_raw_value() & 0x04: 
            string = "O" + string
        self.set_text(string)

class IVData(Graphing.SeriesXY):
    def __init__(self, *args, **kwds):
        self.dispwidg = kwds["dispwidg"]
        del kwds["dispwidg"]
        Graphing.SeriesXY.__init__(self, *args, **kwds)
        
    def xdeliver(self,pkt):
        if pkt.get_value() != 0.0:
            Graphing.SeriesXY.xdeliver(self,pkt)
            
    def ydeliver(self,pkt):
        if pkt.get_value() != 0.0:
            Graphing.SeriesXY.ydeliver(self,pkt)
        else:
            px = self.get_xpoints()
            py = self.get_ypoints()
            pp = []

            voc = 0.0
            maxp = 0
            isc = 0.0
            for i in range(len(px)):
                p = px[i] * py[i]
                pp.append(p)

                if p > px[maxp] * py[maxp]:
                    maxp = i

                if py[i] > isc:
                    isc = py[i]


                if px[i] > voc:
                    voc = px[i]

            fillfactor = px[maxp] * py[maxp] / (isc * voc)

            self.dispwidg.vmp.set_text("%.02fV" % px[maxp]) 
            self.dispwidg.imp.set_text("%.02fA" % py[maxp]) 
            self.dispwidg.maxp.set_text("%.02fW" % (px[maxp] * py[maxp]))
            self.dispwidg.isc.set_text("%.02fV" % isc) 
            self.dispwidg.voc.set_text("%.02fV" % voc) 
            self.dispwidg.vocperc.set_text("%.01f%%" % (100.0 * px[maxp] / voc))
            self.dispwidg.fillfactor.set_text("%.01f%%" % (100.0 * fillfactor))
            
            self.dispwidg.powerseries.set_xpoints(px); 
            self.dispwidg.powerseries.set_ypoints(pp); 

            # Write out a file with the data. 
            (year,mon,day,hour,minute,second,_,_,_) = time.gmtime()
            myfilename = "last_sweep_%s_%04d%02d%02d_%02d%02d%02d.csv"%(self.dispwidg.nodename.replace(" ","_"),year,mon,day,hour,minute,second)
            myfile = file(myfilename, "w+");
            for i in range(len(px)):
                myfile.write("%d,%f,%f\n" % (i, px[i], py[i]))
            myfile.close()


class TrackerIVSweep(gtk.VBox):
    MPPTNG_IVSWEEP_COMMAND = 0

    def dosweep(self, button):
        # Clear the XY graph
        self.ivdata.clear_data()
#        self.powerseries.clear_data()
        
        # Send the message         
        nodeaddr = self.sa.get_scandal_node_addr(self.nodename, nodetype="MPPTNG")
	print "Node address is " + str(nodeaddr)
        if nodeaddr is not None:
            msg = Scandal.CommandPacket(destaddr=nodeaddr, \
                                            commandnum=TrackerIVSweep.MPPTNG_IVSWEEP_COMMAND)
            source = self.sa.store[self.nodename]
            source.get_scandal().send(msg)
        else:
            self.sa.console.write("TrackerIVSweep: could not find node " + self.nodename)

    def __init__(self, sa, nodename="MPPTNG"):
        gtk.VBox.__init__(self)

        self.sa = sa
        self.nodename = nodename

	ivplot = GraphingMPL.Graph(self.sa, \
                                       xlabel="Voltage (V)", \
                                       ylabel="Current (A)", 
                                   maxupdate=200)
        self.ivdata = ivdata = IVData(self.sa, nodename, "Sweep Input Voltage", 
                                      nodename, "Sweep Input Current",
                                      label="IV", 
                                      maxpoints=2000, 
                                      format={"color":"blue", 
                                              "marker":"o", 
                                              "linewidth":2.0}, 
                                      dispwidg=self) 
        self.powerseries = Graphing.SeriesStatic(self.sa, [], [], label="Power", format={"color":"green", "linewidth":2.0})

        ivplot.add_series(self.ivdata)
        ivplot.add_axis(axis=(1,2), ylabel="Power (W)")
        ivplot.add_series(self.powerseries, axis=(1,2))
        self.pack_start(ivplot.get_widget())

        # Display values generated by the sweep
        frame = gtk.Frame(label="Analysis")
        self.pack_start(frame, expand=False)

        self.nodename = nodename

        bigbox = gtk.VBox()
        frame.add(bigbox)
        
        box = gtk.HBox()
        bigbox.pack_start(box, expand=False)

        self.vmp = gtk.Entry(max=8)
        self.vmp.set_editable(False)
        self.vmp.set_width_chars(6)
        label = gtk.Label(str="Vmp")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.vmp)

        self.imp = gtk.Entry(max=8)
        self.imp.set_editable(False)
        self.imp.set_width_chars(6)
        label = gtk.Label(str="Imp")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.imp)

        self.maxp = gtk.Entry(max=8)
        self.maxp.set_editable(False)
        self.maxp.set_width_chars(6)
        label = gtk.Label(str="Pmp")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.maxp)

        # Next row
        box = gtk.HBox()
        bigbox.pack_start(box, expand=False)

        self.isc = gtk.Entry(max=8)
        self.isc.set_editable(False)
        self.isc.set_width_chars(6)
        label = gtk.Label(str="Isc")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.isc)

        self.voc = gtk.Entry(max=8)
        self.voc.set_editable(False)
        self.voc.set_width_chars(6)
        label = gtk.Label(str="Voc")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.voc)

        self.vocperc = gtk.Entry(max=8)
        self.vocperc.set_editable(False)
        self.vocperc.set_width_chars(6)
        label = gtk.Label(str="Voc%")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.vocperc)

        self.fillfactor = gtk.Entry(max=8)
        self.fillfactor.set_editable(False)
        self.fillfactor.set_width_chars(6)
        label = gtk.Label(str="FF")
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_alignment(1.0, 0.5)
        label.set_padding(1, 1)
        box.pack_start(label)
        box.pack_start(self.fillfactor)

        go = gtk.Button(label="Sweep")
        self.pack_start(go, expand=False)

        go.connect("clicked", self.dosweep)
        


class MPPTNGSummary(Driver.Driver):
    def __init__(self, sa, config, name="MPPTNG"):      
        Driver.Driver.__init__(self, sa, config, name)
        self.page = page = gtk.HBox()

        if "nodename" not in config:
            config["nodename"] = self.get_name()

        nodename = config["nodename"]

        col1 = gtk.VBox()
        page.pack_start(col1, expand=False)
        col2 = gtk.VBox()
        page.pack_start(col2)

### Voltage Graph
	graph = GraphingMPL.Graph(self.sa, \
                                      xlabel="Time (s)", \
                                      ylabel="Voltage (V)",\
                                  maxupdate=500)
        col2.pack_start(graph.get_widget())
        series = Graphing.SeriesTime(self.sa, nodename, "Input Voltage", \
                                               label="Input Voltage", \
                                              maxtimediff=1800.0) 
        graph.add_series(series)
        series = Graphing.SeriesTime(self.sa, nodename, "Output Voltage", \
                                               label="Output Voltage", \
                                              maxtimediff=1800.0) 
        graph.add_series(series)

### Current Graph
	graph = GraphingMPL.Graph(self.sa, \
                                      xlabel="Time (s)", \
                                      ylabel="Current (A)",\
                                  maxupdate=500)
        col2.pack_start(graph.get_widget())
        series = Graphing.SeriesTime(self.sa, nodename, "Input Current", \
                                               label="Input Current", \
                                              maxtimediff=1800.0) 
        graph.add_series(series)



        trackers = gtk.Table(rows=3, columns=6, homogeneous=False)
        col1.pack_start(trackers, expand=False)

        widg = gtk.Label(str="In Current")
        trackers.attach(widg, 3, 4, 0, 1) # Second column title

        widg = gtk.Label(str="In Power")
        trackers.attach(widg, 4, 5, 0, 1) # Second column title

        widg = gtk.Label(str="HS Temp")
        trackers.attach(widg, 5, 6, 0, 1) # Second column title

        widg = gtk.Label(str="Status")
        trackers.attach(widg, 6, 7, 0, 1) # Second column title

        widg = gtk.HSeparator()
        trackers.attach(widg, 0,7,1,2)

        widg = gtk.VSeparator()
        trackers.attach(widg, 1,2,0,8)

        def attach_tracker(row, nodename):
            # attach attaches the top edge to row, the bottom edge to 
            # row+1, the left to col, and the left to col+1

            widg = gtk.Label(str=nodename)
            trackers.attach(widg, 0, 1, row, row+1)

            widg = LabelIndicator(sa.store, nodename, "Input Voltage", units="V")
            trackers.attach(widg, 2, 3, row, row+1)

            widg = LabelIndicator(sa.store, nodename, "Input Current", units="A")
            trackers.attach(widg, 3, 4, row, row+1)

            widg = ProductLabelIndicator(sa.store, nodename, "Input Voltage",\
                                      nodename, "Input Current", units="W")
            trackers.attach(widg, 4, 5, row, row+1)

            widg = LabelIndicator(sa.store, nodename, "Heatsink Temp", units="deg")
            trackers.attach(widg, 5, 6, row, row+1)

            widg = TrackerStatusIndicator(sa.store, nodename, "Status")
            trackers.attach(widg, 6, 7, row, row+1)

        attach_tracker(2, nodename)

        sweeper = TrackerIVSweep(sa, nodename)
        col1.pack_start(sweeper)

        openloopconfig = UserConfigWidget(sa, nodename, \
              "Open-loop Ratio", label="Open-Loop Ratio", default="800")
        col1.pack_start(openloopconfig, expand=False)
        
        algconfig = UserConfigWidget(sa, nodename, "Algorithm", label="Algorithm")
        col1.pack_start(algconfig, expand=False)

        targv = CommandValueWidget(sa, nodename, "Set Target", default="40000", label="Manually Set Target Voltage")
        col1.pack_start(targv, expand=False)

        #c = UserConfigWidget(sa, nodename, \
        #      "Input KP", label="Input KP", default="20000")
        #col1.pack_start(c, expand=False)
        
        #c = UserConfigWidget(sa, nodename, \
        #      "Input KI", label="Input KI", default="400")
        #col1.pack_start(c, expand=False)
        
        #c = UserConfigWidget(sa, nodename, \
        #      "Input KD", label="Input KD", default="0")
        #col1.pack_start(c, expand=False)
        
        #c = UserConfigWidget(sa, nodename, \
        #      "Output KP", label="Output KP", default="0")
        #col1.pack_start(c, expand=False)
        
        #c = UserConfigWidget(sa, nodename, \
        #      "Output KI", label="Output KI", default="0")
        #col1.pack_start(c, expand=False)
        
       # c = UserConfigWidget(sa, nodename, \
        #      "Output KD", label="Output KD", default="0")
        #col1.pack_start(c, expand=False)

        c = UserConfigWidget(sa, nodename, \
              "Maximum Output Voltage", label="Maximum Output Voltage", default="136000")
        col1.pack_start(c, expand=False)

	c = UserConfigWidget(sa, nodename, \
              "Minimum Input Voltage", label="Minimum Input Voltage", default="17000")
        col1.pack_start(c, expand=False)
        
        class TuneWidget(CommandValueWidget):
            def do_set(self, *args, **kwargs):
                # create a new window
                self.graphwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
                self.graphwindow.set_default_size(600,600)
                self.graphwindow.set_position(gtk.WIN_POS_CENTER)
                
                graph = GraphingMPL.Graph(self.sa,\
                                              xlabel="Time (s)", \
                                              ylabel="Input Voltage",\
                                              maxupdate=1000)
                self.graphwindow.add(graph.get_widget())
                series = Graphing.SeriesTime(self.sa, self.nodename, "Tune Input Voltage", \
                                                 label="Tune Input Voltage", \
                                                 maxtimediff=100.0, \
                                                 format={"color":"blue"}) 
                graph.add_series(series)
                graph.add_axis(axis=(1,2), ylabel="Output Value")
                series = Graphing.SeriesTime(self.sa, self.nodename, "Tune Output Value", \
                                                 label="Tune Output Value", \
                                                 maxtimediff=100.0, 
                                                 format={"color":"red"})
                graph.add_series(series, axis=(1,2))
                
                self.graphwindow.show()
                self.graphwindow.show_all()

                CommandValueWidget.do_set(self, *args, **kwargs)

        targv = TuneWidget(sa, nodename, "Set and Tune", default="40000", label="Set and Tune")
        col1.pack_start(targv, expand=False)

        reset_button = ResetWidget(sa, nodename)
        col1.pack_start(reset_button, expand=False)

        self.sa.add_notebook_page(self.get_display_name(), self.page)

    def stop(self):
        Driver.Driver.stop(self)
        self.sa.remove_notebook_page(self.page)

    def configure(self):
        widg = Driver.Driver.configure(self)
        
        w = gtk.VBox()
        widg.pack_start(w)

        e = Configurator.TextConfig("nodename", self.config, "Node Name")
        w.pack_start(e, expand=False)

        return widg

# Register our driver with the driver module's module factory
Driver.modfac.add_type("MPPTNGSummary", MPPTNGSummary)

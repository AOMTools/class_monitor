"""
Python 2.7
Class Monitor v 1.00
Basically another implementation of USB Minicounter (with additional tools coming soon) with PyQt and PyQtgraph
Modified from Nick's program doing similar things 

Author: Adrian Utama 
Mar 2017
"""

import sys

import time
import glob
import serial
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QTimer
import pyqtgraph as pg
import minicounter as mc
import threading
import numpy as np

REFRESH_RATE = 100  #100 ms

form_class = uic.loadUiType("classmonitor.ui")[0] 

class MyWindowClass(QtGui.QMainWindow, form_class):

    def __init__(self, parent=None):
        # Program is starting
        self.running = 1
        # Declaring GUI window
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        # Bind event handlers
        self.ButtonStart.clicked.connect(self.ButtonStart_clicked)
        # Gets a list of avaliable serial ports to connect to and adds to combo box
        self.ports = glob.glob('/dev/serial/by-id/usb-Centre_for_Quantum_Technologies_USB_Counter_*')
        ports_disp = [x[-26:]for x in self.ports] # Such as not to display everything
        self.deviceBox.addItems(ports_disp)
        # Initialise plots
        self.plotWidget.plotItem.getAxis('left').setPen((0,0,0))
        self.plotWidget.plotItem.getAxis('bottom').setPen((0,0,0))
        self.plotWidget.setLabel('left', 'Counts', 'trigs')
        self.plotWidget.setLabel('bottom', 'Time', 's')
        # Initialise multithreading
        self.started = 0
        self.thread1 = threading.Thread(target=self.workerThread1_MC)
        self.thread1.start(  )
        # Set timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.setInterval(REFRESH_RATE)
        self.timer.start()
        # Update status
        self.statusbar.showMessage("Ready to run ... Select your device!")
    
    def initialise(self):
        self.bins = int(self.timebinBox.value())
        self.xdata = np.arange(0,self.bins*self.gatetime/1000,self.gatetime/1000)
        self.ydata1 = np.zeros(self.bins)
        self.ydata2 = np.zeros(self.bins)
        self.ydata3 = np.zeros(self.bins)
        self.ydata4 = np.zeros(self.bins)
        # Plotting
        self.plotWidget.clear()
        self.plotWidget.setLimits(xMin = self.xdata[0], xMax = self.xdata[-1], yMin = 0)
        self.plot1 = self.plotWidget.plot(self.xdata, self.ydata1, pen={'color':(255,0,0),'width':1})
        self.plot2 = self.plotWidget.plot(self.xdata, self.ydata2, pen={'color':(0,0,255),'width':1})
        self.plot3 = self.plotWidget.plot(self.xdata, self.ydata3, pen={'color':(0,120,0),'width':1})
        self.plot4 = self.plotWidget.plot(self.xdata, self.ydata4, pen={'color':(255,0,255),'width':1})

    def ButtonStart_clicked(self):
        if self.started == 0:
            # Connecting to device
            ports_idx = self.deviceBox.currentIndex()
            self.counter = mc.Countercomm(self.ports[ports_idx])
            self.gatetime = self.gatetimeBox.value()
            self.trig_logic = self.buttonGroup.checkedButton().text() 
            # Sending initialisation settings to device
            if self.trig_logic == "NIM":
                self.counter.set_NIM()
            else:
                self.counter.set_TTL()
            self.counter.set_gate_time(self.gatetime)
            self.statusbar.showMessage("Connected to device ... Acquiring data")
            # initialisation of data structure and data + starting measurement
            self.initialise()
            self.started = 1
            # Change button appearance
            self.ButtonStart.setText("Stop")
        elif self.started == 1:
            self.started = 0
            self.statusbar.showMessage("Measurement stopped ...")
            # Change button appearance
            self.ButtonStart.setText("Start")

    def update(self):
        if self.started:
            # Update the counter display
            self.counter1Val.setText('%d'%(self.ydata1[-1]))
            self.counter2Val.setText('%d'%(self.ydata2[-1]))
            self.counter3Val.setText('%d'%(self.ydata3[-1]))
            self.counter4Val.setText('%d'%(self.ydata4[-1]))
            # Update plot
            self.plot1.setData(self.xdata, self.ydata1)
            self.plot2.setData(self.xdata, self.ydata2)
            self.plot3.setData(self.xdata, self.ydata3)
            self.plot4.setData(self.xdata, self.ydata4)


        # self.plt = self.plotWidget
        # try:
        #   self.counts = self.counter.get_counts()
        #   self.count = float(self.counts.split(' ')[channel])
        #   self.freq = float(self.count*1000/gate_time)
        #   self.label_count.setText(str(self.count))
        #   self.label_freq.setText(str(self.freq))
        #   self.freq_samples.append(self.freq)
        #   self.time = float("{0:.3f}".format(time.time() - starttime))
        #   self.timedata.append(self.time)
        #   self.plt.plot(self.timedata[-300:],self.freq_samples[-300:],clear=True,pen={'color':'k','width':2})
        # except:
        #   pass

    def workerThread1_MC(self):
        while self.running:
            if self.started:
                string = self.counter.get_all_counts().split()
                self.ydata1 = np.concatenate((self.ydata1[1:], [int(string[0])]))
                self.ydata2 = np.concatenate((self.ydata2[1:], [int(string[1])]))
                self.ydata3 = np.concatenate((self.ydata3[1:], [int(string[2])]))
                self.ydata4 = np.concatenate((self.ydata4[1:], [int(string[3])]))
            else:
                time.sleep(0.1) # Such that the program does not run endlessly

    def cleanUp(self):
        print "Closing the program ... Good bye!"
        self.running = 0
        time.sleep(0.5)


app = QtGui.QApplication(sys.argv)
myWindow = MyWindowClass(None)
myWindow.show()
app.aboutToQuit.connect(myWindow.cleanUp)
sys.exit(app.exec_())

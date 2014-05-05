#!/usr/bin/env python
import numpy as np
from traits.api import HasTraits, Instance, Str, Enum
from traitsui.api import View, Item, VGroup, HGroup
from chaco.api import Plot, ArrayPlotData
from enable.component_editor import ComponentEditor
import os

temp = os.popen('cat /proc/meminfo').readlines()
memItem = [item.split(':')[0] for item in temp]
temp = os.popen('cat /proc/stat').readlines()
temp = [item.split() for item in temp]
cpuItem1 = [item[0] for item in temp]
cpuItem2 = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'stolestolen', 'guest']
cpuItem2 = cpuItem2[:len(temp[0])-2]

class PlotState(HasTraits):
    plot = Instance(Plot)
    data = Instance(ArrayPlotData)
    testItems = Enum(['memstate', 'cpustate'], default='memstate')
    mem = Enum(memItem)
    cpu = Enum(cpuItem1)
    cpuItems = Enum(cpuItem2)
    view = View(
            VGroup(Item('testItems', label=u'test items'),
                HGroup(Item('mem', label=u'mem'),
                    visible_when="testItems=='memstate'"),
                VGroup(Item('cpu', label=u'cpu items'),
                    Item('cpuItems', label=u'cpu cols'),
                    visible_when="testItems=='cpustate'"),
                Item('plot', editor=ComponentEditor(), show_label=False)),
            width = 500, height=500, resizable=True, title='AndTestPlot')

    def __init__(self, **traits):
        super(PlotState, self).__init__(**traits)
        self.fname = open(self.testItems)
        self.col = memItem.index(self.mem)
        self.plotdata()
    def _testItems_changed(self):
        self.fname = open(self.testItems)
    def _mem_changed(self):
        self.col = memItem.index(self.mem)
        self.plotdata()
    def _cpu_changed(self):
        self.col = 0
        temp_col = cpuItem1.index(self.cpu)
        if temp_col != 0:
            for i in range(temp_col):
                self.col += len(temp[i])
        self.plotdata()

    def plotdata(self):
        self.y = []
        self.x = []
        self.fname.seek(0)
        for line in self.fname:
            self.y.append(int(line.split()[self.col+1]))
        self.y = np.array(self.y)
        self.x = np.linspace(0, len(self.y)-1, len(self.y))
        print(self.x, self.y, type(self.x), type(self.y))
        data = ArrayPlotData(x=self.x, y=self.y)
        plot = Plot(data)
        plot.plot(("x", "y"), type="line", color="blue")
        plot.title = "%s . %s" % (self.testItems, self.mem)
        self.plot = plot
        self.data = data

if __name__ == '__main__':
    a = PlotState()
    a.configure_traits()

#!/usr/bin/env python3
import multiprocessing as mp
import time
import os
import matplotlib.pyplot as plt
import optparse

class Daemon(mp.Process):
    def __init__(self, tq, rq):
        mp.Process.__init__(self)
        self.tq = tq
        self.rq = rq
    def run(self):
        pn = self.name
        while True:
            nt = self.tq.get()
            if nt is None:
                print('exiting')
                self.tq.task_done()
                break
            answer = nt()
            self.tq.task_done()
            print('done %s' % nt)
            self.rq.put(answer)
        return

class MemTest(object):
    def __init__(self):
        self.cmd = 'adb shell cat /proc/meminfo'
    def __call__(self):
        temp = os.popen(self.cmd).readlines()
        timestamp = time.time()
        data = ' '.join([i.split(':')[1].replace('kB', '').strip() for i in temp])
        return ('mem', timestamp, data)
    def __str__(self):
        return 'excute memtest'

class CpuTest(object):
    def __init__(self):
        self.cmd = 'adb shell cat /proc/stat'
    def __call__(self):
        temp = os.popen(self.cmd).readlines()
        timestamp = time.time()
        data = ' '.join([' '.join(item.split()[1:]) for item in temp])
        return ('cpu', timestamp, data)
    def __str__(self):
        return 'excute cputest'

class ProcrankTest(object):
    def __init__(self):
        self.cmd = 'adb shell procrank'
    def __call__(self):
        temp = os.popen(self.cmd).readlines()
        timestamp = time.time()
        return ('procrank', timestamp, temp)
    def __str__(self):
        return 'excute procranktest'

class Task(mp.Process):
    def __init__(self, tq, time_sleep):
        mp.Process.__init__(self)
        self.tq = tq
        self.time_sleep = time_sleep
    def run(self):
        while True:
            time.sleep(self.time_sleep)
            self.tq.put(MemTest())
            print('put memtest')
            self.tq.put(CpuTest())
            print('put cputest')
            self.tq.put(ProcrankTest())
            print('put procranktest')

class DataStore(mp.Process):
    def __init__(self, rq, f):
        mp.Process.__init__(self)
        self.rq = rq
        self.f = f
    def run(self):
        while True:
            flags, timestamp, data = self.rq.get()
            fname = self.f[flags]
            fname.write(str(timestamp) + '\t')
            if flags == 'procrank':
                for item in data:
                    fname.write(item)
            else:
                fname.write(data)
            fname.write('\n')
            fname.flush()
            print('write %s data' % flags)


if __name__ == '__main__':
    usage = 'Usage: ./andtest [options]'
    parse = optparse.OptionParser(usage = usage)
    parse.add_option('-t', dest='time_run', default=1, type='int', help='how long you want to run the program, unit=minite, default 1')
    parse.add_option('-s', dest='time_sleep', default=1, type='int', help= 'sampling interval you want, unit=second, default 1')
    options, args = parse.parse_args()

    tasks = mp.JoinableQueue()
    results = mp.Queue()
    pin, pout = mp.Pipe()

    f1 = open('memstate', 'w')
    f2 = open('cpustate', 'w')
    f3 = open('procrank', 'w')
    f = {'mem':f1, 'cpu':f2, 'procrank':f3}

    num_daemons = mp.cpu_count()
    daemons = [Daemon(tasks, results) for i in range(num_daemons)]
    for w in daemons:
        w.start()

    taskproc = Task(tasks, options.time_sleep)
    taskproc.start()
    datastore = DataStore(results, f)
    datastore.start()

    time.sleep(options.time_run*60)
    taskproc.terminate()
    print('taskproc alive? %s' % taskproc.is_alive())
    taskproc.join()
    print('taskproc alive? %s' % taskproc.is_alive())
    for i in range(num_daemons):
        tasks.put(None)
    tasks.join()
    datastore.terminate()
    print('datastore alive? %s' % datastore.is_alive())
    datastore.join()
    print('datastore alive? %s' % datastore.is_alive())
    for k in f:
        f[k].close()

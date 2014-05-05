#!/usr/bin/env python3
import os
def dataget(fpipe, fcmd):
    data = os.popen(fcmd)
    data = data.readlines()
    fpipe.send(data)
    fpipe.close()
if __name__ == '__main__':
    import multiprocessing as mp
    pin, pout = mp.Pipe()
    mp.Process(target=dataget, args=(pout,'ls')).start()
    print(pin.recv())

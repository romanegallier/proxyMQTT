# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import benchmark
# We open the log file in writting mode
configuration = [
    [50, 1000],
    [100, 1000],
    [250, 1000],
    [500, 1000],
    [750, 1000],
    [1000, 1000]  
]


with open('myLogFile', 'w') as fichieryu:
    sys.stdout = fichieryu
    for c in configuration:
        print('$' + str(c[0])+' ' + str(c[1]))

        for i in range(0, 2):
            benchmark.main(c[0], c[1])
            print('#')
            
fichieryu.close()
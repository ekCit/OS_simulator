#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# 
# Author:           Anna Cristina Karingal
# Name:             pcb.py
# Created:          February 27, 2015
# Last Updated:     April 19, 2015
# Description:      Class for the PCB (Process Control Block) that contains and
#                   sets all information about a process, its state and any
#                   parameters passed to it by a system call

import sys
from functools import total_ordering
import msg

param_fields = ["file_name","mem_loc","rw","file_len", "cylinder"]

@total_ordering
class PCB:

    def __init__(self, id_num, alpha, tau, p_loc="ready"): 
        """
        Initialize with new pid & location, empty system call params.
        Calculate next burst based on given history parameter alpha and inital
        burst estimate T.

        """
        self.pid = id_num
        self.proc_loc = p_loc

        #Set params & burst history
        self.params = dict.fromkeys(param_fields)
        self.a = alpha
        self.burst_history = []
        self.next_est_burst = alpha * tau
        self.total_cpu_time = 0

    def set_proc_loc(self, p_loc):
        """ Sets location of process, i.e. which queue/device it is in"""
        self.proc_loc = p_loc

    ## Methods to print out contents/properties of PCB

    def __repr__(self):
    	return "process #" + str(self.pid) 

    def __str__(self):
    	return "process #" + str(self.pid)

    def status(self):
        return "{a!s} is in {q!s} queue".format(a = str(self).capitalize(), q = self.proc_loc.lower())


    ## Methods to compare PCBs

    def __eq__(self, other):
        """
        Compares equality based on different parameters that depend on which
        queue PCB is in.

        If in ready queue, compare based on next estimated burst time.
        If in disk drive queue, compare based on requested cylinder.
        Else, compare by PID.
        """
        if (self.proc_loc.lower() == "ready"):
            return self.next_est_burst == other.next_est_burst
        elif (self.proc_loc.lower() == "disk drive"):
            return self.params["cylinder"] == other.params["cylinder"]
        else:
            return self.pid == other.pid

    def __lt__(self, other):
        """
        Compares PCBs based on different parameters depending on which queue PCB
        is in.

        All other comparisons (>, <= and >=) are generated by
        functools/total_ordering

        """
        if (self.proc_loc.lower() == "ready"):
            return self.next_est_burst < other.next_est_burst
        elif (self.proc_loc.lower() == "disk drive"):
            return self.params["cylinder"] < other.params["cylinder"]
        else:
            return self.pid < other.pid


    ## Calculating burst time

    def calc_next_est_burst (self):
        """
        Calculates next estimated burst time based on previous estimated burst
        time, last recorded burst time, and history parameter alpha

        """
        self.last_est_burst = nself.ext_est_burst
        self.next_est_burst = (self.burst_history[-1]* (1-self.a)) + (self.a * self.last_est_burst)

    def record_burst_time(self, burst): 
        self.burst_history.append(burst)
        self.total_cpu_time += burst
        self.calc_next_est_burst(self)

    def avg_burst_time(self):
        return self.total_cpu_time / len(self.burst_history) if self.burst_history else 0

    ## Setting/clearing system call params for pcb

    def set_syst_call_params(self):
        """
        Sets system call params for file name & starting memory location

        """
        self.params["file_name"] = raw_input("File Name >>> ")
        msg.set_valid_int(self.params, "mem_loc", "Starting Memory Location")

    def set_read_write_params(self, dev_type):

        """
        Sets system call params for read/write and file length (if write)

        """
        if (dev_type.lower() == "printer"):
            self.params["rw"] = "w"
        else: 
            while self.params["rw"] == None:
                rw = raw_input("Read or Write? >>> ")
                if rw.lower() in ["r", "read"]:
                    self.params["rw"] = "r"
                elif rw.lower() in ["w", "write"]:
                    self.params["rw"] = "w"
                else: 
                    print msg.err("Invalid read/write parameters")
                    print "Please enter either 'r', 'read', 'w' or 'write'"

        if self.params["rw"] == "w":
            msg.set_valid_int(self.params, "file_len", "File Length")

    def set_cylinder_params(self, max_num_cylinders):
        if (dev_type.lower() == "disk drive"):
            cyl = raw_input("Cylinder >>> ")
            if cyl > max_num_cylinders: 
                raise IndexError
            else: 
                self.params["cylinder"] = cyl

    def clear_params(self):
        """ Clears all system call & read/write params """
        for p in self.params:
            self.params[p] = None

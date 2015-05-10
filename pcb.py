#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# 
# Author:           Anna Cristina Karingal
# Name:             pcb.py
# Created:          February 27, 2015
# Last Updated:     May 10, 2015
# Description:      Class for the PCB (Process Control Block) that contains and
#                   sets all information about a process, its state and any
#                   parameters passed to it by a system call

from __future__ import division
import sys
from functools import total_ordering
from math import floor
import io

param_fields = ["file","log", "phys" ,"rw","len", "cyl"]

@total_ordering
class PCB:

    def __init__(self, id_num, size, pages, alpha, tau, loc="ready"): 
        """
        Initialize with new pid & location, empty system call params.
        Calculate next burst based on given history parameter alpha and inital
        burst estimate tau.
        """
        self.pid = id_num
        self.proc_loc = loc
        self.proc_size = size
        self.proc_pages = pages
        self.pg_size = size / pages

        # Set params & burst history
        self.params = dict.fromkeys(param_fields)
        self.alpha = alpha
        self.burst_history = []
        self.last_est_burst = tau
        self.next_est_burst = tau
        self.curr_burst = 0

        # Set up empty page table
        self.page_table = dict.fromkeys(range(pages))

    def set_proc_loc(self, p_loc):
        """ Sets location of process, i.e. which queue/device it is in"""
        self.proc_loc = p_loc

    def get_proc_size(self):
        return self.proc_size

    ## Methods to print out contents/properties of PCB

    def __repr__(self):
    	return "process #" + str(self.pid) 

    def __str__(self):
    	return "process #" + str(self.pid)

    def status(self):
        """ Prints which queue/device process is currently in """
        if self.proc_loc.lower()== "cpu" or self.proc_loc.lower() == "job pool":
            return "{a!s} is in {q!s}".format(a = str(self).capitalize(), q = self.proc_loc.upper())
        else: 
            return "{a!s} is in {q!s} Queue".format(a = str(self).capitalize(), q = self.proc_loc.upper())

    def snapshot(self):
        """
        Prints PCB attributes and any current system call parameters in a 
        formatted fashion, on a single line
        """

        print "{:<3}".format(str(self.pid)),

        for key, val in self.params.iteritems():
            if self.proc_loc.lower()[0]!="d" and key=="cylinder":
                continue
            print"{:^{w}}".format(str(val)[:6] if val else "--", w=len(key)+2),

        print "{:^5}".format(str(self.avg_burst_time())),
        print "{:^5}".format(str(sum(self.burst_history))),
        print "{:^6}".format(str(self.proc_size)),

        self.display_page_table()

    def display_page_table(self):
        l = 0
        for page,frame in self.page_table.iteritems(): 
            l += 1
            if l > 1: 
                print "{:^8}{:^8}".format(page,frame).rjust(76)
            else: 
                print "{:^8}{:^8}".format(page,frame)
        print ""


    def headers(self):
        """
        Prints name of system call parameters and PCB attributes in formatted
        fashion, on a single line
        """
        print "{:<4}{:^30}|{:^5}|{:^18}|{:^18}".format("", "FILE", " DISK", "CPU BURST", "MEM")
        print "{:<4}".format("PID"),
        for key,val in self.params.iteritems():
            if self.proc_loc.lower()[0]!="d" and key=="cylinder":
                continue
            print"{:<{w}}|".format(str(key).replace("_"," ").capitalize()[:10], w=len(key)+1),

        print "{:^4}|".format("Avg"),
        print "{:^4}|".format("Tot"),
        print "{:^5}|".format("Size"), 
        print "{:^5}|".format ("Page"), 
        print "{:^6}".format ("Frame")


    ## Methods to compare PCBs

    def __eq__(self, other):
        """
        Compares equality based on different parameters that depend on which
        queue PCB is in.

        If in ready queue, compare based on next estimated burst time.
        If in disk drive queue, compare based on requested cylinder.
        Else, compare by PID.
        """
        # If process is in ready queue or CPU, compare using next est burst
        if self.proc_loc.lower()[0] == "r" or self.proc_loc.lower() == "cpu":
            return self.next_est_burst == other.next_est_burst

        # If process is in disk drive, compare using cylinder number
        elif self.proc_loc.lower()[0] is "d":
            return self.params["cyl"] == other.params["cyl"]

        # If process is in job pool, compare using process size
        elif self.proc_loc.lower()[0] is "j":
            return self.proc_size == other.proc_size

        # All other locations, compare using PID
        else:
            return self.pid == other.pid

    def __lt__(self, other):
        """
        Compares PCBs based on different parameters depending on which queue PCB
        is in.

        All other comparisons (>, <= and >=) are generated by
        functools/total_ordering
        """
        # If process is in ready queue or CPU, compare using next est burst
        if self.proc_loc.lower()[0] == "r" or self.proc_loc.lower() == "cpu":
            return self.next_est_burst < other.next_est_burst
        
        # If process is in disk drive, compare using cylinder number
        elif self.proc_loc.lower()[0] is "d":
            return self.params["cyl"] < other.params["cyl"]

        # If process is in job pool, compare using process size
        elif self.proc_loc.lower()[0] is "j":
            return self.proc_size < other.proc_size

        # All other locations, compare using PID
        else:
            return self.pid < other.pid


    ## Calculating burst times

    def calc_next_est_burst (self):
        """
        Calculates next estimated burst time based on previous estimated burst
        time, last recorded burst time, and history parameter alpha
        """
        self.next_est_burst = (self.burst_history[-1] * (1-self.alpha)) + (self.last_est_burst * self.alpha)
        self.last_est_burst = self.next_est_burst

    def record_burst_time(self, burst): 
        """
        Updates burst history, total CPU time and calculates next estimated
        burst time with given input
        """
        self.curr_burst += burst
        self.burst_history.append(self.curr_burst)
        self.calc_next_est_burst()

    def update_burst_time(self, elapsed):
        """
        Given an elapsed amount of time, updates current CPU burst time used
        and next_est_burst based on how much time elapsed. 
        """
        # Update current burst record with elapsed CPU time
        self.curr_burst += elapsed

        # Next est burst cannot be less than 0
        if self.next_est_burst - elapsed >= 0: 
            self.next_est_burst -= elapsed
        else: 
            self.next_est_burst = 0

    def avg_burst_time(self):
        """
        Returns average burst time for each CPU burst
        """
        return sum(self.burst_history) / len(self.burst_history) if self.burst_history else 0

    def tot_burst_time(self):
        """ 
        Returns total of all CPU bursts
        """
        return sum(self.burst_history)

    def clear_curr_burst (self):
        """
        Resets current bust time to zero
        """
        self.curr_burst = 0

    ## Allocating Memory
    def allocate_memory(self, page, frame): 
        if page in self.page_table:
            self.page_table[page] = frame
        else: 
            raise IndexError


    ## Setting/clearing system call params for pcb
    def set_syst_call_params(self):
        """
        Sets system call params for file name & starting memory location
        """
        self.params["file"] = raw_input("File Name >>> ")
        for p, f in self.page_table.items():
            print type(p),
            print p

        l = io.get_valid_hex("Starting Memory Location")
        offset = int(l % self.pg_size)
        pg = int(floor(l / self.pg_size))
        self.params["log"] = l
        self.params["phys"] = (self.pg_size * self.page_table[pg]) + offset

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
                    print io.err("Invalid read/write parameters")
                    print "Please enter either 'r', 'read', 'w' or 'write'"

        if self.params["rw"] == "w":
            l = io.get_valid_int("File Length")

            if l + self.params["log"]<= self.proc_size: 
                self.params["len"] = l
            else: 
                pass


    def set_cylinder_params(self, max_num_cylinders):
        """
        Prompts user for which disk drive cylinder to access, validates 
        input and sets appropriate system call parameter.

        Precondition: Process is in disk drive
        """
        while self.params["cyl"] == None:
            c = io.get_valid_int("Cylinder")
            if c > max_num_cylinders: 
                print "Invalid cylinder number. Please try again."
            else: 
                self.params["cyl"] = c

    def clear_params(self):
        """ Clears all system call & read/write params """
        for p in self.params:
            self.params[p] = None

#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# 
# Author:           Anna Cristina Karingal
# Name:             memory.py
# Created:          May 4, 2015
# Last Updated:     May 10, 2015
# Description:      Classes for long term scheduling and memory management

from __future__ import division
import sys 
from collections import deque
from math import ceil
from bisect import insort
import heapq
import io
from pcb import PCB
from queues import Queue

class LongTermScheduler:

    def __init__(self, mem_size, pg_size):
        self.ram = Memory(mem_size, pg_size)
        self.job_pool = JobPool()

    def schedule(self, proc):
        try: 
            self.ram.allocate(proc)
            return True

        except InsufficientMemory:
            self.job_pool.enqueue(proc)
            return False

    def terminate(self, pid):

        """
        Look for given process in memory or job pool and terminates process.
        If process was in memory, allocates any freed memory to largest job
        in job pool, until no more freed memory can be allocated. Returns list
        of new processes allocated
        Else, if process was in job pool, removes from job pool, terminates
        process and returns None.
        Precondition: pid is a valid integer
        """
        if self.ram.is_in_mem(pid):
            # Deallocate process
            self.ram.deallocate(pid)

            procs  = []
            # Try to allocate any processes in job queue
            while self.ram.free_mem() > 0: 
                try:
                    procs.append(self.job_pool.dequeue_largest(self.ram.free_mem()))
                    self.ram.allocate(procs[-1])
                except (InsufficientMemory, InvalidProcess, IndexError): 
                    # Either no more jobs or not enough free mem to allocate
                    # any processes in queue
                    break
            return procs

        else:
            # Not in memory, try the job pool
            # Return no processes, because no new processes were allocated mto
            # free memory
            try: 
                p = self.job_pool.dequeue(pid)
                
                # Print stats
                print "\n" + "{:-^78}".format(" Terminated Process Report ")
                print "PID: {:<4} Avg CPU Burst Time: {:<5} Total CPU Time: {:<5}".format(p.pid, p.avg_burst_time(), p.tot_burst_time()).center(78," ")
                
                del p
                return None
            except: 
                raise InvalidProcess(str(pid))

    def kill(self, proc):
        pass

    def show_job_pool(self):
        self.job_pool.snapshot()

    def snapshot(self):
        self.ram.snapshot()


class Memory: 

    def __init__(self, s, p):
        self._size = s
        self._page_size = p

        # Create empty frame table & free frame list containing all frames
        self._frame_table = dict.fromkeys(range(int(s/p)))
        self._free_frames = deque(self._frame_table.keys())

    def free_mem(self):
        return int(len(self._free_frames) * self._page_size)

    def page_size(self): 
        return self._page_size

    def is_in_mem(self, pid):
        for f,p in self._frame_table.items(): 
            if p:
                if p[0] is pid: 
                    return True

        return False

    def allocate(self, proc):
        """
        Allocates memory to a process if there is enough free memory (else
        throws exception). If enough memory, breaks process up into pages,
        assigns pages to frames in frame table and updates free frame list. 
        """
        if proc.proc_size > self.free_mem():
            raise InsufficientMemory(proc)
            
        # For every page needed for process, insert into first free frame from
        # free frames list and update free frames list
        for p in proc.page_table.keys():
            f = self._free_frames.popleft()
            self._frame_table[f] = (proc.pid, p)
            proc.allocate_memory(p,f)

    def deallocate(self, pid):
        """
        Deallocates framesin mem for a given process and updates frame table & 
        free frames list. If process not in memory, throws exception. 
        """

        if not self.is_in_mem(pid):
            raise InvalidProcess

        for k,v in self._frame_table.iteritems(): 
            if v:
                if v[0] is pid: 
                    self._frame_table[k] = None
                    self._free_frames.append(k)

    def snapshot(self):
        print io.snapshot_header("Frame Table")
        print "{:^10}{:^10}{:^10}".format("FRAME", "PID", "PAGE")
        print io.ruler()
        for frame, proc in self._frame_table.iteritems():
            print "{:^10}".format(hex(frame)),
            if proc: 
                print "{:^8}{:^12}".format(proc[0], hex(proc[1]))
            else: 
                print "{:^8}".format("None")

        print io.snapshot_header("Free Frames")
        n = 0
        for f in self._free_frames:
            n += 1
            if (n%6) is 0: # Print 6 frames per row
                print "{:<10}".format(hex(f))
            else:    
                print "{:<10}".format(hex(f)),

class JobPool(Queue):

    def __init__(self):
        self._q = []
        self._dev_name = "job pool"

    def enqueue(self, proc): 
        """ Add process to job pool, maintaining sorted order """
        proc.set_proc_loc(self._dev_name)
        insort(self._q, proc)
        print proc.status()

    def dequeue_largest(self, free_mem):
        """
        Dequeue and return largest job in job pool that will fit in given 
        memory.
        """
        # Nothing to dequeue
        if not self._q: 
            raise IndexError

        # Traverse list from largest first
        # Pop & return process that is the largest that will fit in given memory
        for p in reversed(self._q):
            if p.proc_size <= free_mem:
                return self._q.pop(self._q.index(p))

        # No process in queue will fit in given memory
        raise InvalidProcess

    def dequeue(self, pid):
        """ Dequeue and return given process from job pool """
        # Nothing to dequeue
        if not self._q: 
            raise IndexError

        for p in self._q:
                if p.pid == pid:
                    return self._q.pop(self._q.index(p))
        # Process not in queue
        raise InvalidProcess

    def snapshot(self):
        print " JOB POOL ".center(78, "-")
        if self._q:
            n=0
            for p in self._q: 
                n += 1
                if (n%5) is 0: # Print 5 jobs per row
                    print "P#" + str(p.pid) + " [Size: " + str(p.proc_size) + "] "
                else:
                    print "P#" + str(p.pid) + " [Size: " + str(p.proc_size) + "] ",
            print "\n"
        else: 
            print "Job pool is empty".center(78)

class InsufficientMemory(Exception):
    """
    Exception raised for trying to enqueue while there is not enough free mem
    """
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class InvalidProcess(Exception):
    """
    Exception raised when requested process does not exist
    """
    def __init__(self, value="Process does not exist"):
        self.value = value
    def __str__(self):
        return repr(self.value)
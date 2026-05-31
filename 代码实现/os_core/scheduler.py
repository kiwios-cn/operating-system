#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程调度器模块
Process Scheduler Module
"""

from typing import Optional
from collections import deque
from os_core.process import Process, ProcessState


class RoundRobinScheduler:
    """时间片轮转调度器"""

    def __init__(self, time_quantum: int = 3):
        self.time_quantum = time_quantum
        self.ready_queue = deque()
        self.current_process: Optional[Process] = None
        self.total_context_switches = 0
        self.clock = 0

    def add_process(self, process: Process, verbose: bool = False):
        """添加进程到就绪队列"""
        if process.state == ProcessState.TERMINATED:
            return

        process.state = ProcessState.READY
        process.time_slice = self.time_quantum
        self.ready_queue.append(process)

        if verbose:
            print(f"    [Scheduler] 进程P{process.pid} ({process.name}) 加入就绪队列")

    def schedule(self, verbose: bool = False) -> Optional[Process]:
        """调度下一个进程"""
        # 当前进程还有时间片
        if self.current_process:
            if (self.current_process.state == ProcessState.RUNNING and
                self.current_process.time_slice > 0):
                return self.current_process

            # 时间片用完或被阻塞
            if self.current_process.state == ProcessState.RUNNING:
                self.add_process(self.current_process, verbose)
                if verbose:
                    print(f"    [Scheduler] P{self.current_process.pid} 时间片用完")
            elif self.current_process.state == ProcessState.TERMINATED:
                if verbose:
                    print(f"    [Scheduler] P{self.current_process.pid} 已终止")

        # 从就绪队列选择
        if not self.ready_queue:
            self.current_process = None
            return None

        next_process = self.ready_queue.popleft()

        if self.current_process and self.current_process.pid != next_process.pid:
            self.context_switch(self.current_process, next_process, verbose)

        next_process.state = ProcessState.RUNNING
        next_process.time_slice = self.time_quantum
        self.current_process = next_process

        if verbose:
            print(f"    [Scheduler] 调度P{next_process.pid} ({next_process.name})")

        return next_process

    def context_switch(self, old: Process, new: Process, verbose: bool = False):
        """上下文切换"""
        if verbose:
            print(f"    [Scheduler] 上下文切换: P{old.pid} -> P{new.pid}")
        self.total_context_switches += 1

    def tick(self):
        """时钟滴答"""
        self.clock += 1
        if self.current_process and self.current_process.state == ProcessState.RUNNING:
            self.current_process.time_slice -= 1
            self.current_process.cpu_time += 1

        for process in self.ready_queue:
            process.wait_time += 1

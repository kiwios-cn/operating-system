#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理模块
Process Management Module
"""

from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from os_core.cpu import CPUContext


class ProcessState(Enum):
    """进程状态"""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


@dataclass
class Process:
    """进程控制块"""
    pid: int
    name: str
    state: ProcessState = ProcessState.NEW
    priority: int = 0

    # CPU上下文
    context: CPUContext = field(default_factory=CPUContext)

    # 内存信息
    num_pages: int = 8  # 虚拟页数

    # 调度信息
    time_slice: int = 0
    cpu_time: int = 0
    wait_time: int = 0

    # 程序
    program: Optional[Callable] = None
    program_counter: int = 0

    def __str__(self):
        return f"Process(pid={self.pid}, name={self.name}, state={self.state.value})"

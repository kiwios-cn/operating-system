#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU管理模块
CPU Management Module
"""

from enum import Enum
from dataclasses import dataclass


class CPUMode(Enum):
    """CPU模式"""
    USER_MODE = 0
    KERNEL_MODE = 1


@dataclass
class CPUContext:
    """CPU上下文"""
    eax: int = 0
    ebx: int = 0
    ecx: int = 0
    edx: int = 0

    def copy(self):
        return CPUContext(eax=self.eax, ebx=self.ebx, ecx=self.ecx, edx=self.edx)


class CPU:
    """CPU"""

    def __init__(self):
        self.mode = CPUMode.USER_MODE
        self.context = CPUContext()
        self.saved_context = None
        self.interrupt_count = 0

    def switch_to_kernel_mode(self):
        """切换到内核态"""
        if self.mode == CPUMode.KERNEL_MODE:
            return False
        self.mode = CPUMode.KERNEL_MODE
        self.saved_context = self.context.copy()
        self.interrupt_count += 1
        return True

    def switch_to_user_mode(self):
        """切换回用户态"""
        if self.mode == CPUMode.USER_MODE:
            return False
        self.mode = CPUMode.USER_MODE
        if self.saved_context:
            return_value = self.context.eax
            self.context = self.saved_context
            self.context.eax = return_value
            self.saved_context = None
        return True

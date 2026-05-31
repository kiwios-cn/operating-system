#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统调用模块
System Call Module
"""

from typing import Callable, Any
from os_core.cpu import CPU
from os_core.scheduler import RoundRobinScheduler
from os_core.filesystem import VirtualFileSystem
from os_core.memory import MemoryManagementUnit


class Kernel:
    """操作系统内核"""

    def __init__(self, cpu: CPU, mmu: MemoryManagementUnit,
                 scheduler: RoundRobinScheduler, vfs: VirtualFileSystem):
        self.cpu = cpu
        self.mmu = mmu
        self.scheduler = scheduler
        self.vfs = vfs
        self.syscall_count = 0

    def _syscall_wrapper(self, syscall_func: Callable, *args, verbose: bool = False) -> Any:
        """
        系统调用包装器 - 处理用户态/内核态切换

        Args:
            syscall_func: 系统调用函数
            *args: 系统调用参数
            verbose: 是否显示详细信息

        Returns:
            系统调用返回值
        """
        # 1. 触发软中断，切换到内核态
        if verbose:
            print(f"      [CPU] 触发软中断 int 0x80")
        self.cpu.switch_to_kernel_mode()

        if verbose:
            print(f"      [CPU] 用户态 → 内核态")

        # 2. 执行系统调用
        self.syscall_count += 1
        result = syscall_func(*args)

        # 3. 切换回用户态
        self.cpu.context.eax = result  # 将返回值放入eax寄存器
        self.cpu.switch_to_user_mode()

        if verbose:
            print(f"      [CPU] 内核态 → 用户态 (返回值: {result})")

        return result

    def sys_getpid(self, verbose: bool = False) -> int:
        """获取进程ID"""
        def _impl():
            current = self.scheduler.current_process
            return current.pid if current else -1

        return self._syscall_wrapper(_impl, verbose=verbose)

    def sys_open(self, filename: str, verbose: bool = False) -> int:
        """打开文件"""
        def _impl():
            if verbose:
                print(f"      [Kernel] sys_open('{filename}')")
            return self.vfs.open_file(filename)

        return self._syscall_wrapper(_impl, verbose=verbose)

    def sys_read(self, fd: int, size: int, verbose: bool = False) -> int:
        """读取文件"""
        def _impl():
            if verbose:
                print(f"      [Kernel] sys_read(fd={fd}, size={size})")
            data = self.vfs.read_file(fd, size)
            return len(data) if data else -1

        return self._syscall_wrapper(_impl, verbose=verbose)

    def sys_write(self, fd: int, data: bytes, verbose: bool = False) -> int:
        """写入文件"""
        def _impl():
            if verbose:
                print(f"      [Kernel] sys_write(fd={fd}, size={len(data)})")
            return self.vfs.write_file(fd, data)

        return self._syscall_wrapper(_impl, verbose=verbose)

    def sys_close(self, fd: int, verbose: bool = False) -> int:
        """关闭文件"""
        def _impl():
            if verbose:
                print(f"      [Kernel] sys_close(fd={fd})")
            return self.vfs.close_file(fd)

        return self._syscall_wrapper(_impl, verbose=verbose)

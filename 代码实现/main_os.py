#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块化操作系统 - 主程序
Modular Operating System - Main Program

集成所有核心模块和扩展模块
"""

from typing import Dict, Optional, Callable
from os_core import (
    CPU, MemoryManagementUnit, RoundRobinScheduler,
    VirtualFileSystem, Kernel, Process, ProcessState,
    NUM_PHYSICAL_FRAMES
)


class ModularOS:
    """模块化操作系统"""

    def __init__(self, time_quantum: int = 3, num_frames: int = NUM_PHYSICAL_FRAMES):
        """
        初始化操作系统

        Args:
            time_quantum: 时间片大小
            num_frames: 物理页框数
        """
        # 初始化核心模块
        self.cpu = CPU()
        self.mmu = MemoryManagementUnit(num_frames)
        self.scheduler = RoundRobinScheduler(time_quantum)
        self.vfs = VirtualFileSystem()
        self.kernel = Kernel(self.cpu, self.mmu, self.scheduler, self.vfs)

        self.processes: Dict[int, Process] = {}
        self.next_pid = 1
        self.time_quantum = time_quantum

        print("\n" + "=" * 70)
        print("模块化操作系统启动")
        print("=" * 70)
        print(f"时间片大小: {time_quantum} 时间单位")
        print(f"页面大小: 4KB")
        print(f"物理页框数: {num_frames}")
        print(f"物理内存: {num_frames * 4}KB")
        print("=" * 70)

    def create_process(self, name: str, num_pages: int = 8,
                      program: Optional[Callable] = None) -> Process:
        """创建进程"""
        pid = self.next_pid
        self.next_pid += 1

        process = Process(
            pid=pid,
            name=name,
            num_pages=num_pages,
            program=program
        )

        self.processes[pid] = process

        # 创建页表
        self.mmu.create_page_table(pid, num_pages)

        # 加入调度队列
        self.scheduler.add_process(process, verbose=False)

        print(f"\n[OS] 创建进程P{pid} ({name}), 虚拟空间: {num_pages}页 ({num_pages * 4}KB)")

        return process

    def run_process(self, process: Process, steps: int = 1, verbose: bool = False):
        """运行进程"""
        if not process.program:
            return

        for _ in range(steps):
            if process.state != ProcessState.RUNNING:
                break

            try:
                process.program(self, process, verbose)
                process.program_counter += 1
            except StopIteration:
                process.state = ProcessState.TERMINATED
                break

    def memory_access(self, process_id: int, virtual_address: int,
                     is_write: bool = False, verbose: bool = False) -> bool:
        """内存访问"""
        if verbose:
            print(f"      [OS] P{process_id} {'写' if is_write else '读'}内存: "
                  f"VA=0x{virtual_address:08x}")

        physical_address = self.mmu.translate_address(
            process_id, virtual_address, is_write, verbose
        )

        return physical_address is not None

    def run(self, total_time: int = 30, verbose: bool = True):
        """运行操作系统"""
        print("\n" + "=" * 70)
        print("开始运行")
        print("=" * 70)

        for t in range(total_time):
            if verbose:
                print(f"\n{'='*70}")
                print(f"时钟周期 {t}")
                print(f"{'='*70}")

            # 调度
            current = self.scheduler.schedule(verbose)

            if not current:
                if verbose:
                    print("    [OS] CPU空闲")
                self.scheduler.tick()
                continue

            if verbose:
                print(f"    [OS] 运行P{current.pid} ({current.name}), 时间片: {current.time_slice}")

            # 运行进程
            self.run_process(current, steps=1, verbose=verbose)

            # 时钟滴答
            self.scheduler.tick()

        # 显示统计
        self.show_statistics()

    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 70)
        print("运行统计")
        print("=" * 70)

        # 调度统计
        print(f"\n【调度统计】")
        print(f"总时钟周期:     {self.scheduler.clock}")
        print(f"上下文切换:     {self.scheduler.total_context_switches}")
        print(f"系统调用:       {self.kernel.syscall_count}")

        # 内存统计
        mem_stats = self.mmu.get_statistics()
        print(f"\n【内存统计】")
        print(f"总访问次数:     {mem_stats['total_accesses']}")
        print(f"页面命中:       {mem_stats['page_hits']}")
        print(f"缺页次数:       {mem_stats['page_faults']}")
        print(f"页面置换:       {mem_stats['page_replacements']}")
        print(f"命中率:         {mem_stats['hit_rate']:.2f}%")

        # 进程统计
        print(f"\n【进程统计】")
        print("-" * 70)
        print(f"{'PID':<6} {'名称':<15} {'状态':<12} {'CPU时间':<10} {'等待时间'}")
        print("-" * 70)

        for pid, process in self.processes.items():
            print(f"{process.pid:<6} {process.name:<15} {process.state.value:<12} "
                  f"{process.cpu_time:<10} {process.wait_time}")

        print("-" * 70)
        print(f"总进程数: {len(self.processes)}")
        print("=" * 70)


# ============================================================================
# 示例程序
# ============================================================================

def program_compute(os: ModularOS, process: Process, verbose: bool = False):
    """计算密集型程序"""
    step = process.program_counter

    if step < 5:
        # 访问内存
        va = step * 0x1000  # 访问不同页
        os.memory_access(process.pid, va, is_write=False, verbose=verbose)
        if verbose:
            print(f"      [P{process.pid}] 计算任务 (步骤 {step + 1}/5)")
    else:
        if verbose:
            print(f"      [P{process.pid}] 计算完成")
        raise StopIteration


def program_syscall_demo(os: ModularOS, process: Process, verbose: bool = False):
    """系统调用演示程序"""
    step = process.program_counter

    if step == 0:
        # 创建文件
        if verbose:
            print(f"      [P{process.pid}] 创建测试文件")
        os.vfs.create_file(f"test_p{process.pid}.txt", b"Hello from process!")
    elif step == 1:
        # 打开文件
        if verbose:
            print(f"      [P{process.pid}] 调用 sys_open()")
        fd = os.kernel.sys_open(f"test_p{process.pid}.txt", verbose=verbose)
        process.context.ebx = fd  # 保存文件描述符
    elif step == 2:
        # 读取文件
        if verbose:
            print(f"      [P{process.pid}] 调用 sys_read()")
        fd = process.context.ebx
        bytes_read = os.kernel.sys_read(fd, 10, verbose=verbose)
    elif step == 3:
        # 写入文件
        if verbose:
            print(f"      [P{process.pid}] 调用 sys_write()")
        fd = process.context.ebx
        bytes_written = os.kernel.sys_write(fd, b"New data!", verbose=verbose)
    elif step == 4:
        # 关闭文件
        if verbose:
            print(f"      [P{process.pid}] 调用 sys_close()")
        fd = process.context.ebx
        os.kernel.sys_close(fd, verbose=verbose)
    elif step == 5:
        # 获取进程ID
        if verbose:
            print(f"      [P{process.pid}] 调用 sys_getpid()")
        pid = os.kernel.sys_getpid(verbose=verbose)
        if verbose:
            print(f"      [P{process.pid}] 系统调用演示完成")
        raise StopIteration
    else:
        raise StopIteration


def program_mixed(os: ModularOS, process: Process, verbose: bool = False):
    """混合型程序"""
    step = process.program_counter

    if step < 6:
        # 访问多个页
        va = (step % 3) * 0x1000
        os.memory_access(process.pid, va, is_write=(step % 2 == 0), verbose=verbose)
        if verbose:
            print(f"      [P{process.pid}] 混合任务 (步骤 {step + 1}/6)")
    else:
        if verbose:
            print(f"      [P{process.pid}] 任务完成")
        raise StopIteration


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("模块化操作系统演示")
    print("多道程序设计 + 分页存储管理 + 系统调用机制")
    print("=" * 70)

    # 创建操作系统
    os = ModularOS(time_quantum=3, num_frames=16)

    # 创建进程
    print("\n创建进程...")
    os.create_process("ComputeTask", num_pages=6, program=program_compute)
    os.create_process("SyscallDemo", num_pages=4, program=program_syscall_demo)
    os.create_process("MixedTask", num_pages=4, program=program_mixed)

    # 运行
    os.run(total_time=30, verbose=True)

    print("\n" + "=" * 70)
    print("模块化操作系统演示完成")
    print("=" * 70)
    print("\n核心模块:")
    print("  - os_core.cpu          : CPU管理")
    print("  - os_core.memory       : 内存管理（分页+LRU）")
    print("  - os_core.process      : 进程管理")
    print("  - os_core.scheduler    : 进程调度")
    print("  - os_core.filesystem   : 文件系统")
    print("  - os_core.syscall      : 系统调用")
    print("\n扩展模块:")
    print("  - os_modules.thread_manager    : 线程管理")
    print("  - os_modules.deadlock_manager  : 死锁管理")
    print("  - os_modules.device_manager    : 设备管理")
    print("  - os_modules.interrupt_manager : 中断管理")
    print("=" * 70)


if __name__ == "__main__":
    main()

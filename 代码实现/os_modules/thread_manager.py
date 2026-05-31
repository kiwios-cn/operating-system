#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程管理模块
Thread Management Module

实现：
1. 用户级线程（User-Level Thread）
2. 内核级线程（Kernel-Level Thread）
3. 线程调度
4. 线程同步（互斥锁、信号量）
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
import threading as py_threading  # 用于模拟真实并发


# ============================================================================
# 线程状态和上下文
# ============================================================================

class ThreadState(Enum):
    """线程状态"""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


@dataclass
class ThreadContext:
    """线程上下文（寄存器状态）"""
    eax: int = 0
    ebx: int = 0
    ecx: int = 0
    edx: int = 0
    esp: int = 0  # 栈指针
    eip: int = 0  # 指令指针

    def copy(self):
        return ThreadContext(
            eax=self.eax, ebx=self.ebx, ecx=self.ecx,
            edx=self.edx, esp=self.esp, eip=self.eip
        )


# ============================================================================
# 用户级线程
# ============================================================================

@dataclass
class UserThread:
    """用户级线程（User-Level Thread）"""
    thread_id: int
    process_id: int
    name: str
    state: ThreadState = ThreadState.NEW

    # 线程上下文
    context: ThreadContext = field(default_factory=ThreadContext)

    # 栈信息
    stack_base: int = 0
    stack_size: int = 4096  # 4KB栈

    # 调度信息
    time_slice: int = 0
    cpu_time: int = 0
    wait_time: int = 0

    # 线程函数
    thread_func: Optional[Callable] = None
    func_args: tuple = ()
    program_counter: int = 0

    def __str__(self):
        return f"UserThread(tid={self.thread_id}, pid={self.process_id}, name={self.name}, state={self.state.value})"


class UserThreadScheduler:
    """用户级线程调度器（在用户空间运行）"""

    def __init__(self, time_quantum: int = 2):
        """
        初始化用户级线程调度器

        Args:
            time_quantum: 时间片大小
        """
        self.time_quantum = time_quantum
        self.ready_queue = deque()
        self.current_thread: Optional[UserThread] = None
        self.threads: Dict[int, UserThread] = {}
        self.next_tid = 1
        self.context_switches = 0
        self.clock = 0

    def create_thread(self, process_id: int, name: str,
                     thread_func: Callable, args: tuple = ()) -> UserThread:
        """创建用户级线程"""
        tid = self.next_tid
        self.next_tid += 1

        thread = UserThread(
            thread_id=tid,
            process_id=process_id,
            name=name,
            thread_func=thread_func,
            func_args=args,
            stack_base=tid * 0x1000,
            stack_size=4096
        )

        self.threads[tid] = thread
        self.ready_queue.append(thread)
        thread.state = ThreadState.READY

        return thread

    def schedule(self, verbose: bool = False) -> Optional[UserThread]:
        """调度下一个线程"""
        # 当前线程还有时间片
        if self.current_thread:
            if (self.current_thread.state == ThreadState.RUNNING and
                self.current_thread.time_slice > 0):
                return self.current_thread

            # 时间片用完
            if self.current_thread.state == ThreadState.RUNNING:
                self.current_thread.state = ThreadState.READY
                self.ready_queue.append(self.current_thread)
                if verbose:
                    print(f"      [UserScheduler] T{self.current_thread.thread_id} 时间片用完")

        # 从就绪队列选择
        if not self.ready_queue:
            self.current_thread = None
            return None

        next_thread = self.ready_queue.popleft()

        # 上下文切换
        if self.current_thread and self.current_thread.thread_id != next_thread.thread_id:
            if verbose:
                print(f"      [UserScheduler] 线程切换: T{self.current_thread.thread_id} -> T{next_thread.thread_id}")
            self.context_switches += 1

        next_thread.state = ThreadState.RUNNING
        next_thread.time_slice = self.time_quantum
        self.current_thread = next_thread

        return next_thread

    def tick(self):
        """时钟滴答"""
        self.clock += 1
        if self.current_thread and self.current_thread.state == ThreadState.RUNNING:
            self.current_thread.time_slice -= 1
            self.current_thread.cpu_time += 1

        for thread in self.ready_queue:
            thread.wait_time += 1

    def terminate_thread(self, thread_id: int):
        """终止线程"""
        if thread_id in self.threads:
            thread = self.threads[thread_id]
            thread.state = ThreadState.TERMINATED


# ============================================================================
# 内核级线程
# ============================================================================

@dataclass
class KernelThread:
    """内核级线程（Kernel-Level Thread）"""
    thread_id: int
    process_id: int
    name: str
    state: ThreadState = ThreadState.NEW
    priority: int = 0

    # 线程上下文
    context: ThreadContext = field(default_factory=ThreadContext)

    # 栈信息
    kernel_stack_base: int = 0
    kernel_stack_size: int = 8192  # 8KB内核栈
    user_stack_base: int = 0
    user_stack_size: int = 4096  # 4KB用户栈

    # 调度信息
    time_slice: int = 0
    cpu_time: int = 0
    wait_time: int = 0

    # 线程函数
    thread_func: Optional[Callable] = None
    func_args: tuple = ()
    program_counter: int = 0

    # 内核级线程特有
    can_block: bool = True  # 可以独立阻塞

    def __str__(self):
        return f"KernelThread(tid={self.thread_id}, pid={self.process_id}, name={self.name}, state={self.state.value}, priority={self.priority})"


class KernelThreadScheduler:
    """内核级线程调度器（在内核空间运行）"""

    def __init__(self, time_quantum: int = 3):
        """
        初始化内核级线程调度器

        Args:
            time_quantum: 时间片大小
        """
        self.time_quantum = time_quantum
        self.ready_queue = deque()
        self.current_thread: Optional[KernelThread] = None
        self.threads: Dict[int, KernelThread] = {}
        self.next_tid = 1
        self.context_switches = 0
        self.clock = 0

    def create_thread(self, process_id: int, name: str, priority: int = 0,
                     thread_func: Callable = None, args: tuple = ()) -> KernelThread:
        """创建内核级线程"""
        tid = self.next_tid
        self.next_tid += 1

        thread = KernelThread(
            thread_id=tid,
            process_id=process_id,
            name=name,
            priority=priority,
            thread_func=thread_func,
            func_args=args,
            kernel_stack_base=tid * 0x2000,
            user_stack_base=tid * 0x1000
        )

        self.threads[tid] = thread
        self.ready_queue.append(thread)
        thread.state = ThreadState.READY

        return thread

    def schedule(self, verbose: bool = False) -> Optional[KernelThread]:
        """调度下一个线程（支持优先级）"""
        # 当前线程还有时间片
        if self.current_thread:
            if (self.current_thread.state == ThreadState.RUNNING and
                self.current_thread.time_slice > 0):
                return self.current_thread

            # 时间片用完或被阻塞
            if self.current_thread.state == ThreadState.RUNNING:
                self.current_thread.state = ThreadState.READY
                self.ready_queue.append(self.current_thread)
                if verbose:
                    print(f"      [KernelScheduler] T{self.current_thread.thread_id} 时间片用完")
            elif self.current_thread.state == ThreadState.BLOCKED:
                if verbose:
                    print(f"      [KernelScheduler] T{self.current_thread.thread_id} 被阻塞")

        # 从就绪队列选择（优先级调度）
        if not self.ready_queue:
            self.current_thread = None
            return None

        # 选择优先级最高的线程
        next_thread = max(self.ready_queue, key=lambda t: t.priority)
        self.ready_queue.remove(next_thread)

        # 上下文切换
        if self.current_thread and self.current_thread.thread_id != next_thread.thread_id:
            if verbose:
                print(f"      [KernelScheduler] 线程切换: T{self.current_thread.thread_id} -> T{next_thread.thread_id}")
            self.context_switches += 1

        next_thread.state = ThreadState.RUNNING
        next_thread.time_slice = self.time_quantum
        self.current_thread = next_thread

        return next_thread

    def tick(self):
        """时钟滴答"""
        self.clock += 1
        if self.current_thread and self.current_thread.state == ThreadState.RUNNING:
            self.current_thread.time_slice -= 1
            self.current_thread.cpu_time += 1

        for thread in self.ready_queue:
            thread.wait_time += 1

    def block_thread(self, thread_id: int):
        """阻塞线程"""
        if thread_id in self.threads:
            thread = self.threads[thread_id]
            thread.state = ThreadState.BLOCKED

    def unblock_thread(self, thread_id: int):
        """解除阻塞"""
        if thread_id in self.threads:
            thread = self.threads[thread_id]
            if thread.state == ThreadState.BLOCKED:
                thread.state = ThreadState.READY
                self.ready_queue.append(thread)

    def terminate_thread(self, thread_id: int):
        """终止线程"""
        if thread_id in self.threads:
            thread = self.threads[thread_id]
            thread.state = ThreadState.TERMINATED


# ============================================================================
# 线程同步原语
# ============================================================================

class Mutex:
    """互斥锁"""

    def __init__(self, name: str = "mutex"):
        self.name = name
        self.locked = False
        self.owner_thread_id: Optional[int] = None
        self.waiting_threads: deque = deque()

    def acquire(self, thread_id: int, verbose: bool = False) -> bool:
        """获取锁"""
        if not self.locked:
            self.locked = True
            self.owner_thread_id = thread_id
            if verbose:
                print(f"      [Mutex] T{thread_id} 获取锁 '{self.name}'")
            return True
        else:
            self.waiting_threads.append(thread_id)
            if verbose:
                print(f"      [Mutex] T{thread_id} 等待锁 '{self.name}' (持有者: T{self.owner_thread_id})")
            return False

    def release(self, thread_id: int, verbose: bool = False) -> Optional[int]:
        """释放锁"""
        if self.owner_thread_id != thread_id:
            if verbose:
                print(f"      [Mutex] 错误: T{thread_id} 不是锁 '{self.name}' 的持有者")
            return None

        if verbose:
            print(f"      [Mutex] T{thread_id} 释放锁 '{self.name}'")

        if self.waiting_threads:
            # 唤醒等待的线程
            next_thread = self.waiting_threads.popleft()
            self.owner_thread_id = next_thread
            if verbose:
                print(f"      [Mutex] T{next_thread} 被唤醒并获取锁 '{self.name}'")
            return next_thread
        else:
            self.locked = False
            self.owner_thread_id = None
            return None


class Semaphore:
    """信号量"""

    def __init__(self, name: str, initial_value: int):
        self.name = name
        self.value = initial_value
        self.waiting_threads: deque = deque()

    def P(self, thread_id: int, verbose: bool = False) -> bool:
        """P操作（wait）"""
        if self.value > 0:
            self.value -= 1
            if verbose:
                print(f"      [Semaphore] T{thread_id} P操作成功 '{self.name}' (value={self.value})")
            return True
        else:
            self.waiting_threads.append(thread_id)
            if verbose:
                print(f"      [Semaphore] T{thread_id} 阻塞在 '{self.name}' (value={self.value})")
            return False

    def V(self, thread_id: int, verbose: bool = False) -> Optional[int]:
        """V操作（signal）"""
        if self.waiting_threads:
            # 唤醒等待的线程
            next_thread = self.waiting_threads.popleft()
            if verbose:
                print(f"      [Semaphore] T{thread_id} V操作，唤醒T{next_thread} '{self.name}' (value={self.value})")
            return next_thread
        else:
            self.value += 1
            if verbose:
                print(f"      [Semaphore] T{thread_id} V操作 '{self.name}' (value={self.value})")
            return None


# ============================================================================
# 线程管理器
# ============================================================================

class ThreadManager:
    """线程管理器 - 统一管理用户级和内核级线程"""

    def __init__(self, use_kernel_threads: bool = True):
        """
        初始化线程管理器

        Args:
            use_kernel_threads: True=使用内核级线程，False=使用用户级线程
        """
        self.use_kernel_threads = use_kernel_threads

        if use_kernel_threads:
            self.scheduler = KernelThreadScheduler(time_quantum=3)
            self.thread_type = "内核级线程"
        else:
            self.scheduler = UserThreadScheduler(time_quantum=2)
            self.thread_type = "用户级线程"

        # 同步原语
        self.mutexes: Dict[str, Mutex] = {}
        self.semaphores: Dict[str, Semaphore] = {}

    def create_thread(self, process_id: int, name: str,
                     thread_func: Callable = None, args: tuple = (),
                     priority: int = 0):
        """创建线程"""
        if self.use_kernel_threads:
            return self.scheduler.create_thread(process_id, name, priority, thread_func, args)
        else:
            return self.scheduler.create_thread(process_id, name, thread_func, args)

    def create_mutex(self, name: str) -> Mutex:
        """创建互斥锁"""
        mutex = Mutex(name)
        self.mutexes[name] = mutex
        return mutex

    def create_semaphore(self, name: str, initial_value: int) -> Semaphore:
        """创建信号量"""
        sem = Semaphore(name, initial_value)
        self.semaphores[name] = sem
        return sem

    def run(self, total_time: int = 20, verbose: bool = True):
        """运行线程调度"""
        print("\n" + "=" * 70)
        print(f"线程管理系统启动 - {self.thread_type}")
        print("=" * 70)

        for t in range(total_time):
            if verbose:
                print(f"\n{'='*70}")
                print(f"时钟周期 {t}")
                print(f"{'='*70}")

            # 调度线程
            current = self.scheduler.schedule(verbose)

            if not current:
                if verbose:
                    print("      [ThreadMgr] 没有就绪线程")
                self.scheduler.tick()
                continue

            if verbose:
                print(f"      [ThreadMgr] 运行 {current}")

            # 执行线程函数
            if current.thread_func and current.state == ThreadState.RUNNING:
                try:
                    current.thread_func(self, current, verbose)
                    current.program_counter += 1
                except StopIteration:
                    current.state = ThreadState.TERMINATED
                    if verbose:
                        print(f"      [ThreadMgr] T{current.thread_id} 终止")

            # 时钟滴答
            self.scheduler.tick()

        # 显示统计
        self.show_statistics()

    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 70)
        print("线程统计")
        print("=" * 70)
        print(f"线程类型:       {self.thread_type}")
        print(f"总时钟周期:     {self.scheduler.clock}")
        print(f"上下文切换:     {self.scheduler.context_switches}")

        print("\n线程详情:")
        print("-" * 70)
        print(f"{'TID':<6} {'进程':<8} {'名称':<15} {'状态':<12} {'CPU时间':<10} {'等待时间'}")
        print("-" * 70)

        for tid, thread in self.scheduler.threads.items():
            print(f"{thread.thread_id:<6} P{thread.process_id:<7} {thread.name:<15} "
                  f"{thread.state.value:<12} {thread.cpu_time:<10} {thread.wait_time}")

        print("-" * 70)
        print(f"总线程数: {len(self.scheduler.threads)}")
        print("=" * 70)


# ============================================================================
# 示例线程函数
# ============================================================================

def thread_compute(mgr: ThreadManager, thread, verbose: bool = False):
    """计算线程"""
    step = thread.program_counter

    if step < 3:
        if verbose:
            print(f"        [T{thread.thread_id}] 执行计算任务 (步骤 {step + 1}/3)")
    else:
        if verbose:
            print(f"        [T{thread.thread_id}] 计算完成")
        raise StopIteration


def thread_io(mgr: ThreadManager, thread, verbose: bool = False):
    """I/O线程"""
    step = thread.program_counter

    if step < 4:
        if verbose:
            print(f"        [T{thread.thread_id}] 执行I/O操作 (步骤 {step + 1}/4)")
    else:
        if verbose:
            print(f"        [T{thread.thread_id}] I/O完成")
        raise StopIteration


def thread_with_mutex(mgr: ThreadManager, thread, verbose: bool = False):
    """使用互斥锁的线程"""
    step = thread.program_counter

    if step == 0:
        # 获取锁
        mutex = mgr.mutexes.get("shared_resource")
        if mutex:
            mutex.acquire(thread.thread_id, verbose)
    elif step < 3:
        if verbose:
            print(f"        [T{thread.thread_id}] 访问共享资源 (步骤 {step}/3)")
    elif step == 3:
        # 释放锁
        mutex = mgr.mutexes.get("shared_resource")
        if mutex:
            mutex.release(thread.thread_id, verbose)
        if verbose:
            print(f"        [T{thread.thread_id}] 完成")
        raise StopIteration


# ============================================================================
# 演示程序
# ============================================================================

def demo_user_threads():
    """演示用户级线程"""
    print("\n" + "=" * 70)
    print("用户级线程演示")
    print("=" * 70)

    mgr = ThreadManager(use_kernel_threads=False)

    # 创建线程
    mgr.create_thread(1, "ComputeThread1", thread_compute)
    mgr.create_thread(1, "ComputeThread2", thread_compute)
    mgr.create_thread(1, "IOThread", thread_io)

    # 运行
    mgr.run(total_time=15, verbose=True)


def demo_kernel_threads():
    """演示内核级线程"""
    print("\n" + "=" * 70)
    print("内核级线程演示")
    print("=" * 70)

    mgr = ThreadManager(use_kernel_threads=True)

    # 创建不同优先级的线程
    mgr.create_thread(1, "HighPriority", thread_compute, priority=10)
    mgr.create_thread(1, "MediumPriority", thread_io, priority=5)
    mgr.create_thread(2, "LowPriority", thread_compute, priority=1)

    # 运行
    mgr.run(total_time=15, verbose=True)


def demo_thread_sync():
    """演示线程同步"""
    print("\n" + "=" * 70)
    print("线程同步演示 - 互斥锁")
    print("=" * 70)

    mgr = ThreadManager(use_kernel_threads=True)

    # 创建互斥锁
    mgr.create_mutex("shared_resource")

    # 创建竞争线程
    mgr.create_thread(1, "Thread1", thread_with_mutex)
    mgr.create_thread(1, "Thread2", thread_with_mutex)

    # 运行
    mgr.run(total_time=15, verbose=True)


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("线程管理系统演示")
    print("=" * 70)

    # 1. 用户级线程
    demo_user_threads()

    # 2. 内核级线程
    demo_kernel_threads()

    # 3. 线程同步
    demo_thread_sync()


if __name__ == "__main__":
    main()

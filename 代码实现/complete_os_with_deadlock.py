#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整操作系统实现
- 多道程序设计（时间片轮转调度）
- 分页存储管理（LRU页面置换）
- 系统调用机制
Complete Operating System Implementation
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, OrderedDict


# ============================================================================
# 内存管理常量
# ============================================================================

PAGE_SIZE = 4096  # 页面大小：4KB
PHYSICAL_MEMORY_SIZE = 64 * 1024  # 物理内存：64KB
NUM_PHYSICAL_FRAMES = PHYSICAL_MEMORY_SIZE // PAGE_SIZE  # 16个页框
VIRTUAL_MEMORY_SIZE = 256 * 1024  # 虚拟内存：256KB


# ============================================================================
# 页表和内存管理
# ============================================================================

@dataclass
class PageTableEntry:
    """页表项"""
    virtual_page_number: int
    physical_frame_number: int = -1
    valid: bool = False
    dirty: bool = False
    referenced: bool = False
    last_access_time: float = 0.0

    def __str__(self):
        status = "在内存" if self.valid else "不在内存"
        frame = f"Frame#{self.physical_frame_number}" if self.valid else "N/A"
        return f"VPage#{self.virtual_page_number} -> {frame} [{status}]"


class PageTable:
    """页表"""

    def __init__(self, process_id: int, num_pages: int):
        self.process_id = process_id
        self.entries: List[PageTableEntry] = []
        for vpn in range(num_pages):
            self.entries.append(PageTableEntry(virtual_page_number=vpn))

    def get_entry(self, virtual_page_number: int) -> Optional[PageTableEntry]:
        if 0 <= virtual_page_number < len(self.entries):
            return self.entries[virtual_page_number]
        return None

    def update_entry(self, virtual_page_number: int,
                    physical_frame_number: int, valid: bool = True):
        entry = self.get_entry(virtual_page_number)
        if entry:
            entry.physical_frame_number = physical_frame_number
            entry.valid = valid
            entry.last_access_time = time.time()

    def invalidate_entry(self, virtual_page_number: int):
        entry = self.get_entry(virtual_page_number)
        if entry:
            entry.valid = False
            entry.physical_frame_number = -1


@dataclass
class PhysicalFrame:
    """物理页框"""
    frame_number: int
    process_id: int = -1
    virtual_page_number: int = -1
    last_access_time: float = 0.0
    reference_count: int = 0

    def is_free(self) -> bool:
        return self.process_id == -1

    def allocate(self, process_id: int, virtual_page_number: int):
        self.process_id = process_id
        self.virtual_page_number = virtual_page_number
        self.last_access_time = time.time()
        self.reference_count = 0

    def free(self):
        self.process_id = -1
        self.virtual_page_number = -1
        self.last_access_time = 0.0
        self.reference_count = 0


class LRUPageReplacement:
    """LRU页面置换算法"""

    def __init__(self):
        self.access_order: OrderedDict[Tuple[int, int], float] = OrderedDict()

    def access(self, process_id: int, frame_number: int):
        """记录页面访问"""
        key = (process_id, frame_number)
        if key in self.access_order:
            del self.access_order[key]
        self.access_order[key] = time.time()

    def select_victim(self) -> Optional[Tuple[int, int]]:
        """选择被置换的页框"""
        if not self.access_order:
            return None
        victim_key, _ = next(iter(self.access_order.items()))
        return victim_key

    def remove(self, process_id: int, frame_number: int):
        key = (process_id, frame_number)
        if key in self.access_order:
            del self.access_order[key]


class MemoryManagementUnit:
    """内存管理单元"""

    def __init__(self, num_frames: int = NUM_PHYSICAL_FRAMES):
        self.num_frames = num_frames
        self.physical_frames: List[PhysicalFrame] = []
        self.page_tables: Dict[int, PageTable] = {}
        self.lru = LRUPageReplacement()

        # 统计信息
        self.page_faults = 0
        self.page_hits = 0
        self.page_replacements = 0

        # 初始化物理页框
        for i in range(num_frames):
            self.physical_frames.append(PhysicalFrame(frame_number=i))

    def create_page_table(self, process_id: int, num_pages: int) -> PageTable:
        """为进程创建页表"""
        page_table = PageTable(process_id, num_pages)
        self.page_tables[process_id] = page_table
        return page_table

    def translate_address(self, process_id: int, virtual_address: int,
                         is_write: bool = False, verbose: bool = False) -> Optional[int]:
        """地址转换：虚拟地址 -> 物理地址"""
        virtual_page_number = virtual_address // PAGE_SIZE
        page_offset = virtual_address % PAGE_SIZE

        if verbose:
            print(f"      [MMU] 地址转换: VA=0x{virtual_address:08x} "
                  f"-> VPN={virtual_page_number}, Offset=0x{page_offset:03x}")

        page_table = self.page_tables.get(process_id)
        if not page_table:
            return None

        pte = page_table.get_entry(virtual_page_number)
        if not pte:
            return None

        # 检查页面是否在内存中
        if not pte.valid:
            if verbose:
                print(f"      [MMU] 缺页! VPN={virtual_page_number}")
            self.page_faults += 1

            if not self.handle_page_fault(process_id, virtual_page_number, verbose):
                return None

            pte = page_table.get_entry(virtual_page_number)
        else:
            self.page_hits += 1
            if verbose:
                print(f"      [MMU] 命中! VPN={virtual_page_number} -> Frame={pte.physical_frame_number}")

        # 更新访问信息
        pte.referenced = True
        pte.last_access_time = time.time()
        if is_write:
            pte.dirty = True

        self.lru.access(process_id, pte.physical_frame_number)

        physical_address = pte.physical_frame_number * PAGE_SIZE + page_offset
        return physical_address

    def handle_page_fault(self, process_id: int, virtual_page_number: int,
                         verbose: bool = False) -> bool:
        """处理缺页"""
        free_frame = self.find_free_frame()

        if free_frame is None:
            if verbose:
                print(f"      [MMU] 需要页面置换")
            free_frame = self.replace_page(verbose)
            if free_frame is None:
                return False

        self.physical_frames[free_frame].allocate(process_id, virtual_page_number)
        page_table = self.page_tables[process_id]
        page_table.update_entry(virtual_page_number, free_frame, valid=True)
        self.lru.access(process_id, free_frame)

        if verbose:
            print(f"      [MMU] 页面加载: VPN={virtual_page_number} -> Frame={free_frame}")
        return True

    def find_free_frame(self) -> Optional[int]:
        """查找空闲页框"""
        for frame in self.physical_frames:
            if frame.is_free():
                return frame.frame_number
        return None

    def replace_page(self, verbose: bool = False) -> Optional[int]:
        """页面置换（LRU）"""
        self.page_replacements += 1

        victim = self.lru.select_victim()
        if victim is None:
            return None

        old_process_id, victim_frame_number = victim
        victim_frame = self.physical_frames[victim_frame_number]
        old_vpn = victim_frame.virtual_page_number

        if verbose:
            print(f"      [MMU] 置换: Frame={victim_frame_number}, P{old_process_id} VPN={old_vpn}")

        # 使旧页表项无效
        if old_process_id in self.page_tables:
            old_page_table = self.page_tables[old_process_id]
            old_page_table.invalidate_entry(old_vpn)

        self.lru.remove(old_process_id, victim_frame_number)
        victim_frame.free()

        return victim_frame_number

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self.page_hits + self.page_faults
        hit_rate = (self.page_hits / total * 100) if total > 0 else 0
        return {
            'page_faults': self.page_faults,
            'page_hits': self.page_hits,
            'page_replacements': self.page_replacements,
            'total_accesses': total,
            'hit_rate': hit_rate
        }


# ============================================================================
# CPU和进程
# ============================================================================

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
        if self.mode == CPUMode.KERNEL_MODE:
            return False
        self.mode = CPUMode.KERNEL_MODE
        self.saved_context = self.context.copy()
        self.interrupt_count += 1
        return True

    def switch_to_user_mode(self):
        if self.mode == CPUMode.USER_MODE:
            return False
        self.mode = CPUMode.USER_MODE
        if self.saved_context:
            return_value = self.context.eax
            self.context = self.saved_context
            self.context.eax = return_value
            self.saved_context = None
        return True


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


# ============================================================================
# 时间片轮转调度器
# ============================================================================

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


# ============================================================================
# 虚拟文件系统
# ============================================================================

@dataclass
class VirtualFile:
    """虚拟文件"""
    name: str
    content: bytes = b""
    position: int = 0

    def read(self, size: int) -> bytes:
        data = self.content[self.position:self.position + size]
        self.position += len(data)
        return data

    def write(self, data: bytes) -> int:
        before = self.content[:self.position]
        after = self.content[self.position + len(data):]
        self.content = before + data + after
        self.position += len(data)
        return len(data)


class VirtualFileSystem:
    """虚拟文件系统"""

    def __init__(self):
        self.files: Dict[str, VirtualFile] = {}
        self.open_files: Dict[int, VirtualFile] = {}
        self.next_fd = 3

        # 标准流
        self.files["stdin"] = VirtualFile("stdin")
        self.files["stdout"] = VirtualFile("stdout")
        self.files["stderr"] = VirtualFile("stderr")
        self.open_files[0] = self.files["stdin"]
        self.open_files[1] = self.files["stdout"]
        self.open_files[2] = self.files["stderr"]

    def create_file(self, filename: str, content: bytes = b"") -> bool:
        if filename in self.files:
            return False
        self.files[filename] = VirtualFile(filename, content)
        return True

    def open_file(self, filename: str) -> int:
        if filename not in self.files:
            return -1
        fd = self.next_fd
        self.next_fd += 1
        self.open_files[fd] = self.files[filename]
        return fd

    def close_file(self, fd: int) -> int:
        if fd not in self.open_files or fd < 3:
            return -1
        del self.open_files[fd]
        return 0

    def read_file(self, fd: int, size: int) -> Optional[bytes]:
        if fd not in self.open_files:
            return None
        return self.open_files[fd].read(size)

    def write_file(self, fd: int, data: bytes) -> int:
        if fd not in self.open_files:
            return -1
        return self.open_files[fd].write(data)


# ============================================================================
# 内核
# ============================================================================

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


# ============================================================================
# 完整操作系统
# ============================================================================

class CompleteOS:
    """完整操作系统 - 集成调度和内存管理"""

    def __init__(self, time_quantum: int = 3, num_frames: int = NUM_PHYSICAL_FRAMES):
        """
        初始化操作系统

        Args:
            time_quantum: 时间片大小
            num_frames: 物理页框数
        """
        self.cpu = CPU()
        self.mmu = MemoryManagementUnit(num_frames)
        self.scheduler = RoundRobinScheduler(time_quantum)
        self.vfs = VirtualFileSystem()
        self.kernel = Kernel(self.cpu, self.mmu, self.scheduler, self.vfs)

        self.processes: Dict[int, Process] = {}
        self.next_pid = 1
        self.time_quantum = time_quantum

        print("\n" + "=" * 70)
        print("完整操作系统启动")
        print("=" * 70)
        print(f"时间片大小: {time_quantum} 时间单位")
        print(f"页面大小: {PAGE_SIZE} 字节 (4KB)")
        print(f"物理页框数: {num_frames}")
        print(f"物理内存: {num_frames * PAGE_SIZE} 字节 ({num_frames * 4}KB)")
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
            print(f"      [OS] P{process_id} {'写' if is_write else '读'}内存: VA=0x{virtual_address:08x}")

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

def program_compute(os: CompleteOS, process: Process, verbose: bool = False):
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


def program_io(os: CompleteOS, process: Process, verbose: bool = False):
    """I/O密集型程序"""
    step = process.program_counter

    if step < 4:
        # 访问内存
        va = step * 0x1000
        os.memory_access(process.pid, va, is_write=True, verbose=verbose)
        if verbose:
            print(f"      [P{process.pid}] I/O操作 (步骤 {step + 1}/4)")
    else:
        if verbose:
            print(f"      [P{process.pid}] I/O完成")
        raise StopIteration


def program_mixed(os: CompleteOS, process: Process, verbose: bool = False):
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


def program_syscall_demo(os: CompleteOS, process: Process, verbose: bool = False):
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


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("完整操作系统演示")
    print("多道程序设计 + 分页存储管理 + 系统调用机制")
    print("=" * 70)

    # 创建操作系统
    os = CompleteOS(time_quantum=3, num_frames=16)

    # 创建进程
    print("\n创建进程...")
    os.create_process("ComputeTask", num_pages=6, program=program_compute)
    os.create_process("SyscallDemo", num_pages=4, program=program_syscall_demo)
    os.create_process("MixedTask", num_pages=4, program=program_mixed)

    # 运行
    os.run(total_time=30, verbose=True)


if __name__ == "__main__":
    main()

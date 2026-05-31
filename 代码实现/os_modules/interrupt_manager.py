#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中断管理系统
Interrupt Management System

实现：
1. 中断向量表（IVT）
2. 中断类型（硬件中断、软件中断、异常）
3. 中断处理程序（ISR）
4. 中断优先级
5. 中断屏蔽
6. 中断嵌套
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque


# ============================================================================
# 中断类型
# ============================================================================

class InterruptType(Enum):
    """中断类型"""
    HARDWARE = "硬件中断"    # 外部设备产生
    SOFTWARE = "软件中断"    # 程序主动触发（如系统调用）
    EXCEPTION = "异常"       # 错误条件（如除零、缺页）


class InterruptPriority(Enum):
    """中断优先级"""
    CRITICAL = 0    # 最高优先级（如电源故障）
    HIGH = 1        # 高优先级（如时钟中断）
    MEDIUM = 2      # 中等优先级（如磁盘I/O）
    LOW = 3         # 低优先级（如键盘输入）


# ============================================================================
# 中断向量
# ============================================================================

@dataclass
class InterruptVector:
    """中断向量（中断向量表中的一项）"""
    vector_number: int          # 中断向量号
    interrupt_type: InterruptType
    priority: InterruptPriority
    handler: Optional[Callable] = None  # 中断处理程序
    description: str = ""
    enabled: bool = True        # 是否启用
    count: int = 0             # 触发次数

    def __str__(self):
        status = "启用" if self.enabled else "禁用"
        return f"INT#{self.vector_number:02X}: {self.description} [{self.interrupt_type.value}, 优先级={self.priority.value}, {status}]"


# ============================================================================
# 中断请求
# ============================================================================

@dataclass
class InterruptRequest:
    """中断请求"""
    vector_number: int
    interrupt_type: InterruptType
    priority: InterruptPriority
    timestamp: float = field(default_factory=time.time)
    process_id: int = 0
    data: Any = None  # 中断相关数据

    def __lt__(self, other):
        """用于优先队列排序（优先级高的先处理）"""
        return self.priority.value < other.priority.value


# ============================================================================
# 中断向量表
# ============================================================================

class InterruptVectorTable:
    """中断向量表（IVT）"""

    def __init__(self):
        """初始化中断向量表"""
        self.vectors: Dict[int, InterruptVector] = {}
        self._initialize_standard_vectors()

    def _initialize_standard_vectors(self):
        """初始化标准中断向量"""
        # 异常（0x00-0x1F）
        self.register_vector(0x00, InterruptType.EXCEPTION, InterruptPriority.CRITICAL,
                           "除零错误", None)
        self.register_vector(0x01, InterruptType.EXCEPTION, InterruptPriority.CRITICAL,
                           "调试异常", None)
        self.register_vector(0x0E, InterruptType.EXCEPTION, InterruptPriority.HIGH,
                           "缺页异常", None)

        # 硬件中断（0x20-0x2F）
        self.register_vector(0x20, InterruptType.HARDWARE, InterruptPriority.HIGH,
                           "时钟中断", None)
        self.register_vector(0x21, InterruptType.HARDWARE, InterruptPriority.LOW,
                           "键盘中断", None)
        self.register_vector(0x23, InterruptType.HARDWARE, InterruptPriority.MEDIUM,
                           "串口中断", None)
        self.register_vector(0x2E, InterruptType.HARDWARE, InterruptPriority.MEDIUM,
                           "磁盘中断", None)

        # 软件中断（0x80）
        self.register_vector(0x80, InterruptType.SOFTWARE, InterruptPriority.MEDIUM,
                           "系统调用", None)

    def register_vector(self, vector_number: int, interrupt_type: InterruptType,
                       priority: InterruptPriority, description: str,
                       handler: Optional[Callable]) -> bool:
        """注册中断向量"""
        if vector_number in self.vectors:
            return False

        vector = InterruptVector(
            vector_number=vector_number,
            interrupt_type=interrupt_type,
            priority=priority,
            handler=handler,
            description=description
        )

        self.vectors[vector_number] = vector
        return True

    def set_handler(self, vector_number: int, handler: Callable) -> bool:
        """设置中断处理程序"""
        if vector_number in self.vectors:
            self.vectors[vector_number].handler = handler
            return True
        return False

    def get_vector(self, vector_number: int) -> Optional[InterruptVector]:
        """获取中断向量"""
        return self.vectors.get(vector_number)

    def enable_interrupt(self, vector_number: int):
        """启用中断"""
        if vector_number in self.vectors:
            self.vectors[vector_number].enabled = True

    def disable_interrupt(self, vector_number: int):
        """禁用中断（屏蔽）"""
        if vector_number in self.vectors:
            self.vectors[vector_number].enabled = False

    def list_vectors(self):
        """列出所有中断向量"""
        print("\n" + "=" * 70)
        print("中断向量表")
        print("=" * 70)
        for vector_number in sorted(self.vectors.keys()):
            vector = self.vectors[vector_number]
            print(f"{vector} (触发次数: {vector.count})")
        print("=" * 70)


# ============================================================================
# 中断控制器
# ============================================================================

class InterruptController:
    """中断控制器（类似8259A PIC）"""

    def __init__(self, ivt: InterruptVectorTable):
        """
        初始化中断控制器

        Args:
            ivt: 中断向量表
        """
        self.ivt = ivt
        self.interrupt_queue: List[InterruptRequest] = []  # 中断请求队列
        self.current_interrupt: Optional[InterruptRequest] = None
        self.interrupt_stack: List[InterruptRequest] = []  # 中断嵌套栈

        # 全局中断标志
        self.interrupts_enabled = True

        # 统计信息
        self.total_interrupts = 0
        self.nested_interrupts = 0

    def trigger_interrupt(self, vector_number: int, process_id: int = 0,
                         data: Any = None, verbose: bool = False) -> bool:
        """
        触发中断

        Args:
            vector_number: 中断向量号
            process_id: 触发中断的进程ID
            data: 中断相关数据
            verbose: 是否显示详细信息

        Returns:
            是否成功触发
        """
        # 检查全局中断标志
        if not self.interrupts_enabled:
            if verbose:
                print(f"    [IntCtrl] 中断被禁止，忽略 INT#{vector_number:02X}")
            return False

        # 获取中断向量
        vector = self.ivt.get_vector(vector_number)
        if not vector:
            if verbose:
                print(f"    [IntCtrl] 未定义的中断向量 INT#{vector_number:02X}")
            return False

        # 检查中断是否被屏蔽
        if not vector.enabled:
            if verbose:
                print(f"    [IntCtrl] 中断被屏蔽 INT#{vector_number:02X}")
            return False

        # 创建中断请求
        request = InterruptRequest(
            vector_number=vector_number,
            interrupt_type=vector.interrupt_type,
            priority=vector.priority,
            process_id=process_id,
            data=data
        )

        # 加入中断队列（按优先级排序）
        self.interrupt_queue.append(request)
        self.interrupt_queue.sort()  # 按优先级排序

        if verbose:
            print(f"    [IntCtrl] 触发中断 INT#{vector_number:02X}: {vector.description}")

        return True

    def handle_interrupts(self, cpu, verbose: bool = False) -> bool:
        """
        处理中断队列

        Args:
            cpu: CPU对象
            verbose: 是否显示详细信息

        Returns:
            是否处理了中断
        """
        if not self.interrupts_enabled or not self.interrupt_queue:
            return False

        # 获取最高优先级的中断
        request = self.interrupt_queue.pop(0)
        vector = self.ivt.get_vector(request.vector_number)

        if not vector or not vector.handler:
            if verbose:
                print(f"    [IntCtrl] 中断 INT#{request.vector_number:02X} 没有处理程序")
            return False

        # 检查中断嵌套
        if self.current_interrupt:
            # 只有更高优先级的中断才能嵌套
            if request.priority.value < self.current_interrupt.priority.value:
                self.interrupt_stack.append(self.current_interrupt)
                self.nested_interrupts += 1
                if verbose:
                    print(f"    [IntCtrl] 中断嵌套: INT#{request.vector_number:02X} 抢占 INT#{self.current_interrupt.vector_number:02X}")
            else:
                # 优先级不够，放回队列
                self.interrupt_queue.insert(0, request)
                return False

        # 保存当前中断
        self.current_interrupt = request

        # 切换到内核态
        cpu.switch_to_kernel_mode()

        if verbose:
            print(f"    [IntCtrl] 处理中断 INT#{request.vector_number:02X}: {vector.description}")

        # 执行中断处理程序
        try:
            vector.handler(request, cpu, verbose)
            vector.count += 1
            self.total_interrupts += 1
        except Exception as e:
            if verbose:
                print(f"    [IntCtrl] 中断处理程序异常: {e}")

        # 恢复中断嵌套
        if self.interrupt_stack:
            self.current_interrupt = self.interrupt_stack.pop()
        else:
            self.current_interrupt = None

        # 返回用户态
        cpu.switch_to_user_mode()

        return True

    def cli(self):
        """关中断（Clear Interrupt Flag）"""
        self.interrupts_enabled = False

    def sti(self):
        """开中断（Set Interrupt Flag）"""
        self.interrupts_enabled = True

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_interrupts': self.total_interrupts,
            'nested_interrupts': self.nested_interrupts,
            'pending_interrupts': len(self.interrupt_queue),
            'interrupts_enabled': self.interrupts_enabled
        }


# ============================================================================
# CPU（增强版，支持中断）
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
    eip: int = 0  # 指令指针
    eflags: int = 0  # 标志寄存器

    def copy(self):
        return CPUContext(
            eax=self.eax, ebx=self.ebx, ecx=self.ecx,
            edx=self.edx, eip=self.eip, eflags=self.eflags
        )


class CPU:
    """CPU（支持中断）"""

    def __init__(self):
        self.mode = CPUMode.USER_MODE
        self.context = CPUContext()
        self.saved_context = None
        self.interrupt_flag = True  # IF标志位

    def switch_to_kernel_mode(self):
        """切换到内核态"""
        if self.mode == CPUMode.KERNEL_MODE:
            return False
        self.mode = CPUMode.KERNEL_MODE
        self.saved_context = self.context.copy()
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

    def cli(self):
        """关中断指令"""
        self.interrupt_flag = False

    def sti(self):
        """开中断指令"""
        self.interrupt_flag = True


# ============================================================================
# 中断处理程序（ISR）
# ============================================================================

def isr_timer(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """时钟中断处理程序"""
    if verbose:
        print(f"      [ISR] 时钟中断处理: 时间片到期")
    # 这里可以触发进程调度


def isr_keyboard(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """键盘中断处理程序"""
    if verbose:
        key = request.data if request.data else "?"
        print(f"      [ISR] 键盘中断处理: 按键 '{key}'")


def isr_disk(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """磁盘中断处理程序"""
    if verbose:
        print(f"      [ISR] 磁盘中断处理: I/O完成")


def isr_page_fault(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """缺页异常处理程序"""
    if verbose:
        address = request.data if request.data else 0
        print(f"      [ISR] 缺页异常处理: 地址=0x{address:08X}")
    # 这里可以触发页面调入


def isr_divide_by_zero(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """除零异常处理程序"""
    if verbose:
        print(f"      [ISR] 除零异常处理: 终止进程P{request.process_id}")


def isr_syscall(request: InterruptRequest, cpu: CPU, verbose: bool = False):
    """系统调用中断处理程序"""
    if verbose:
        syscall_num = cpu.context.eax
        print(f"      [ISR] 系统调用处理: 调用号={syscall_num}")


# ============================================================================
# 中断管理系统
# ============================================================================

class InterruptManager:
    """中断管理系统"""

    def __init__(self):
        """初始化中断管理系统"""
        self.cpu = CPU()
        self.ivt = InterruptVectorTable()
        self.controller = InterruptController(self.ivt)

        # 注册中断处理程序
        self._register_handlers()

        print("\n" + "=" * 70)
        print("中断管理系统初始化")
        print("=" * 70)

    def _register_handlers(self):
        """注册中断处理程序"""
        self.ivt.set_handler(0x00, isr_divide_by_zero)
        self.ivt.set_handler(0x0E, isr_page_fault)
        self.ivt.set_handler(0x20, isr_timer)
        self.ivt.set_handler(0x21, isr_keyboard)
        self.ivt.set_handler(0x2E, isr_disk)
        self.ivt.set_handler(0x80, isr_syscall)

    def trigger_interrupt(self, vector_number: int, process_id: int = 0,
                         data: Any = None, verbose: bool = False):
        """触发中断"""
        self.controller.trigger_interrupt(vector_number, process_id, data, verbose)

    def process_interrupts(self, verbose: bool = False):
        """处理中断"""
        self.controller.handle_interrupts(self.cpu, verbose)

    def show_statistics(self):
        """显示统计信息"""
        stats = self.controller.get_statistics()

        print("\n" + "=" * 70)
        print("中断统计")
        print("=" * 70)
        print(f"总中断次数:     {stats['total_interrupts']}")
        print(f"中断嵌套次数:   {stats['nested_interrupts']}")
        print(f"待处理中断:     {stats['pending_interrupts']}")
        print(f"中断状态:       {'开启' if stats['interrupts_enabled'] else '关闭'}")
        print("=" * 70)


# ============================================================================
# 演示程序
# ============================================================================

def demo_interrupt_handling():
    """演示中断处理"""
    print("\n" + "=" * 70)
    print("中断处理演示")
    print("=" * 70)

    mgr = InterruptManager()

    # 显示中断向量表
    mgr.ivt.list_vectors()

    print("\n" + "=" * 70)
    print("触发各种中断")
    print("=" * 70)

    # 1. 时钟中断
    mgr.trigger_interrupt(0x20, process_id=1, verbose=True)
    mgr.process_interrupts(verbose=True)

    # 2. 键盘中断
    mgr.trigger_interrupt(0x21, process_id=1, data='A', verbose=True)
    mgr.process_interrupts(verbose=True)

    # 3. 磁盘中断
    mgr.trigger_interrupt(0x2E, process_id=2, verbose=True)
    mgr.process_interrupts(verbose=True)

    # 4. 缺页异常
    mgr.trigger_interrupt(0x0E, process_id=1, data=0x12345678, verbose=True)
    mgr.process_interrupts(verbose=True)

    # 5. 系统调用
    mgr.cpu.context.eax = 1  # 系统调用号
    mgr.trigger_interrupt(0x80, process_id=1, verbose=True)
    mgr.process_interrupts(verbose=True)

    # 显示统计
    mgr.show_statistics()


def demo_interrupt_priority():
    """演示中断优先级"""
    print("\n" + "=" * 70)
    print("中断优先级演示")
    print("=" * 70)

    mgr = InterruptManager()

    print("\n触发多个不同优先级的中断:")

    # 触发多个中断（不立即处理）
    mgr.trigger_interrupt(0x21, process_id=1, data='A', verbose=True)  # 低优先级
    mgr.trigger_interrupt(0x2E, process_id=1, verbose=True)            # 中优先级
    mgr.trigger_interrupt(0x20, process_id=1, verbose=True)            # 高优先级

    print("\n按优先级顺序处理:")
    while mgr.controller.interrupt_queue:
        mgr.process_interrupts(verbose=True)

    mgr.show_statistics()


def demo_interrupt_masking():
    """演示中断屏蔽"""
    print("\n" + "=" * 70)
    print("中断屏蔽演示")
    print("=" * 70)

    mgr = InterruptManager()

    # 屏蔽键盘中断
    print("\n屏蔽键盘中断 (INT#21):")
    mgr.ivt.disable_interrupt(0x21)

    mgr.trigger_interrupt(0x21, process_id=1, data='A', verbose=True)
    mgr.process_interrupts(verbose=True)

    # 启用键盘中断
    print("\n启用键盘中断:")
    mgr.ivt.enable_interrupt(0x21)

    mgr.trigger_interrupt(0x21, process_id=1, data='B', verbose=True)
    mgr.process_interrupts(verbose=True)

    mgr.show_statistics()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("中断管理系统演示")
    print("=" * 70)

    # 1. 基本中断处理
    demo_interrupt_handling()

    # 2. 中断优先级
    demo_interrupt_priority()

    # 3. 中断屏蔽
    demo_interrupt_masking()


if __name__ == "__main__":
    main()

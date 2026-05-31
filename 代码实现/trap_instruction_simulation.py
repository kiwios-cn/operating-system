#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trap Instruction Simulation
陷入指令模拟程序 - 完整的陷入处理机制
"""

import time
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field


# ============================================================================
# 陷入类型定义
# ============================================================================

class TrapType(Enum):
    """陷入类型枚举"""
    # 异常（Exception）- 同步，由程序执行引起
    DIVIDE_BY_ZERO = 0          # 除零异常
    OVERFLOW = 1                # 溢出异常
    INVALID_OPCODE = 2          # 非法指令
    GENERAL_PROTECTION = 3      # 一般保护异常
    PAGE_FAULT = 14             # 缺页异常
    STACK_OVERFLOW = 12         # 栈溢出

    # 系统调用（Trap/Software Interrupt）- 同步，程序主动触发
    SYSCALL = 0x80              # 系统调用（int 0x80）

    # 硬件中断（Hardware Interrupt）- 异步，外部设备触发
    TIMER = 0x20                # 时钟中断
    KEYBOARD = 0x21             # 键盘中断
    DISK = 0x2E                 # 磁盘中断
    NETWORK = 0x2F              # 网络中断


class TrapPriority(Enum):
    """陷入优先级"""
    CRITICAL = 0    # 最高优先级（硬件故障）
    HIGH = 1        # 高优先级（异常）
    MEDIUM = 2      # 中优先级（硬件中断）
    LOW = 3         # 低优先级（系统调用）


class CPUMode(Enum):
    """CPU运行模式"""
    USER_MODE = 0       # 用户态
    KERNEL_MODE = 1     # 内核态


# ============================================================================
# CPU上下文和状态
# ============================================================================

@dataclass
class CPUContext:
    """CPU上下文（寄存器状态）"""
    eax: int = 0        # 累加器
    ebx: int = 0        # 基址寄存器
    ecx: int = 0        # 计数寄存器
    edx: int = 0        # 数据寄存器
    esi: int = 0        # 源索引
    edi: int = 0        # 目的索引
    ebp: int = 0        # 基址指针
    esp: int = 0        # 栈指针
    eip: int = 0        # 指令指针
    eflags: int = 0     # 标志寄存器

    def copy(self):
        """复制上下文"""
        return CPUContext(
            eax=self.eax, ebx=self.ebx, ecx=self.ecx, edx=self.edx,
            esi=self.esi, edi=self.edi, ebp=self.ebp, esp=self.esp,
            eip=self.eip, eflags=self.eflags
        )


@dataclass
class TrapFrame:
    """陷入帧 - 保存陷入发生时的完整状态"""
    trap_type: TrapType
    trap_number: int
    error_code: int = 0
    context: CPUContext = field(default_factory=CPUContext)
    timestamp: float = field(default_factory=time.time)


class CPU:
    """模拟CPU，支持完整的陷入处理"""

    def __init__(self):
        self.mode = CPUMode.USER_MODE
        self.context = CPUContext()
        self.trap_stack: List[TrapFrame] = []  # 陷入栈（支持嵌套）
        self.interrupt_enabled = True           # 中断使能标志
        self.trap_count = 0

    def switch_to_kernel_mode(self) -> bool:
        """切换到内核态"""
        if self.mode == CPUMode.KERNEL_MODE:
            return False

        print(f"  [CPU] 用户态 → 内核态")
        self.mode = CPUMode.KERNEL_MODE
        return True

    def switch_to_user_mode(self) -> bool:
        """切换回用户态"""
        if self.mode == CPUMode.USER_MODE:
            return False

        print(f"  [CPU] 内核态 → 用户态")
        self.mode = CPUMode.USER_MODE
        return True

    def disable_interrupt(self):
        """关中断（CLI指令）"""
        self.interrupt_enabled = False
        print("  [CPU] 中断已屏蔽")

    def enable_interrupt(self):
        """开中断（STI指令）"""
        self.interrupt_enabled = True
        print("  [CPU] 中断已使能")

    def push_trap_frame(self, trap_frame: TrapFrame):
        """压入陷入帧"""
        self.trap_stack.append(trap_frame)
        print(f"  [CPU] 陷入帧入栈，当前嵌套层数：{len(self.trap_stack)}")

    def pop_trap_frame(self) -> Optional[TrapFrame]:
        """弹出陷入帧"""
        if self.trap_stack:
            frame = self.trap_stack.pop()
            print(f"  [CPU] 陷入帧出栈，剩余嵌套层数：{len(self.trap_stack)}")
            return frame
        return None

    def get_trap_nesting_level(self) -> int:
        """获取陷入嵌套层数"""
        return len(self.trap_stack)


# ============================================================================
# 陷入向量表
# ============================================================================

class TrapVectorTable:
    """陷入向量表 - 管理所有陷入处理程序"""

    def __init__(self):
        self.handlers: Dict[int, Callable] = {}         # 陷入号 -> 处理函数
        self.priorities: Dict[int, TrapPriority] = {}   # 陷入号 -> 优先级
        self.masked: set = set()                        # 被屏蔽的陷入

    def register(self, trap_number: int, handler: Callable,
                priority: TrapPriority = TrapPriority.MEDIUM):
        """注册陷入处理程序"""
        self.handlers[trap_number] = handler
        self.priorities[trap_number] = priority
        print(f"  [IVT] 注册陷入处理程序：0x{trap_number:02x} (优先级: {priority.name})")

    def get_handler(self, trap_number: int) -> Optional[Callable]:
        """获取陷入处理程序"""
        return self.handlers.get(trap_number)

    def get_priority(self, trap_number: int) -> TrapPriority:
        """获取陷入优先级"""
        return self.priorities.get(trap_number, TrapPriority.LOW)

    def mask_trap(self, trap_number: int):
        """屏蔽陷入"""
        self.masked.add(trap_number)
        print(f"  [IVT] 屏蔽陷入：0x{trap_number:02x}")

    def unmask_trap(self, trap_number: int):
        """取消屏蔽陷入"""
        self.masked.discard(trap_number)
        print(f"  [IVT] 取消屏蔽陷入：0x{trap_number:02x}")

    def is_masked(self, trap_number: int) -> bool:
        """检查陷入是否被屏蔽"""
        return trap_number in self.masked


# ============================================================================
# 陷入处理器
# ============================================================================

class TrapHandler:
    """陷入处理器 - 核心陷入处理逻辑"""

    def __init__(self, cpu: CPU):
        self.cpu = cpu
        self.ivt = TrapVectorTable()
        self.trap_statistics: Dict[int, int] = {}  # 陷入统计

        # 注册所有陷入处理程序
        self._register_all_handlers()

    def _register_all_handlers(self):
        """注册所有陷入处理程序"""
        # 异常处理程序（高优先级）
        self.ivt.register(TrapType.DIVIDE_BY_ZERO.value,
                         self.handle_divide_by_zero, TrapPriority.HIGH)
        self.ivt.register(TrapType.OVERFLOW.value,
                         self.handle_overflow, TrapPriority.HIGH)
        self.ivt.register(TrapType.INVALID_OPCODE.value,
                         self.handle_invalid_opcode, TrapPriority.HIGH)
        self.ivt.register(TrapType.PAGE_FAULT.value,
                         self.handle_page_fault, TrapPriority.HIGH)
        self.ivt.register(TrapType.STACK_OVERFLOW.value,
                         self.handle_stack_overflow, TrapPriority.HIGH)

        # 系统调用（低优先级）
        self.ivt.register(TrapType.SYSCALL.value,
                         self.handle_syscall, TrapPriority.LOW)

        # 硬件中断（中优先级）
        self.ivt.register(TrapType.TIMER.value,
                         self.handle_timer_interrupt, TrapPriority.MEDIUM)
        self.ivt.register(TrapType.KEYBOARD.value,
                         self.handle_keyboard_interrupt, TrapPriority.MEDIUM)
        self.ivt.register(TrapType.DISK.value,
                         self.handle_disk_interrupt, TrapPriority.MEDIUM)

    def trigger_trap(self, trap_type: TrapType, error_code: int = 0) -> bool:
        """触发陷入"""
        trap_number = trap_type.value

        print(f"\n{'='*70}")
        print(f"[Trap] 触发陷入：{trap_type.name} (0x{trap_number:02x})")
        print(f"{'='*70}")

        # 检查是否被屏蔽
        if self.ivt.is_masked(trap_number):
            print(f"  [Trap] 陷入被屏蔽，忽略")
            return False

        # 对于硬件中断，检查中断使能标志
        if trap_number >= 0x20 and not self.cpu.interrupt_enabled:
            print(f"  [Trap] 中断被禁止，忽略")
            return False

        # 统计
        self.trap_statistics[trap_number] = self.trap_statistics.get(trap_number, 0) + 1
        self.cpu.trap_count += 1

        # 1. 保存当前上下文
        trap_frame = TrapFrame(
            trap_type=trap_type,
            trap_number=trap_number,
            error_code=error_code,
            context=self.cpu.context.copy()
        )

        print(f"  [Trap] 保存现场（陷入帧）")
        print(f"    EIP=0x{trap_frame.context.eip:08x}, "
              f"ESP=0x{trap_frame.context.esp:08x}")

        # 2. 切换到内核态
        self.cpu.switch_to_kernel_mode()

        # 3. 压入陷入帧（支持嵌套）
        self.cpu.push_trap_frame(trap_frame)

        # 4. 查找并执行处理程序
        handler = self.ivt.get_handler(trap_number)
        if handler is None:
            print(f"  [Trap] 错误：未找到处理程序")
            return False

        priority = self.ivt.get_priority(trap_number)
        print(f"  [Trap] 执行处理程序（优先级：{priority.name}）")

        # 执行处理程序
        result = handler(trap_frame)

        # 5. 恢复现场
        self._restore_context(trap_frame)

        print(f"  [Trap] 陷入处理完成，返回")
        print(f"{'='*70}\n")

        return result

    def _restore_context(self, trap_frame: TrapFrame):
        """恢复上下文"""
        # 弹出陷入帧
        self.cpu.pop_trap_frame()

        # 如果陷入栈为空，返回用户态
        if self.cpu.get_trap_nesting_level() == 0:
            self.cpu.switch_to_user_mode()

        print(f"  [Trap] 恢复现场")

    # ========================================================================
    # 异常处理程序
    # ========================================================================

    def handle_divide_by_zero(self, trap_frame: TrapFrame) -> bool:
        """处理除零异常"""
        print(f"    [Exception] 除零异常处理")
        print(f"    发生位置：EIP=0x{trap_frame.context.eip:08x}")
        print(f"    处理方式：终止进程或发送信号")
        # 实际系统中会终止进程或发送SIGFPE信号
        return True

    def handle_overflow(self, trap_frame: TrapFrame) -> bool:
        """处理溢出异常"""
        print(f"    [Exception] 溢出异常处理")
        print(f"    EAX=0x{trap_frame.context.eax:08x}")
        print(f"    处理方式：设置溢出标志")
        return True

    def handle_invalid_opcode(self, trap_frame: TrapFrame) -> bool:
        """处理非法指令异常"""
        print(f"    [Exception] 非法指令异常")
        print(f"    指令地址：EIP=0x{trap_frame.context.eip:08x}")
        print(f"    处理方式：终止进程")
        return True

    def handle_page_fault(self, trap_frame: TrapFrame) -> bool:
        """处理缺页异常"""
        print(f"    [Exception] 缺页异常处理")
        print(f"    缺页地址：0x{trap_frame.error_code:08x}")
        print(f"    处理步骤：")
        print(f"      1. 检查页表")
        print(f"      2. 分配物理页面")
        print(f"      3. 从磁盘加载页面")
        print(f"      4. 更新页表")
        print(f"      5. 返回重新执行指令")
        # 模拟页面加载延迟
        time.sleep(0.01)
        print(f"    页面加载完成")
        return True

    def handle_stack_overflow(self, trap_frame: TrapFrame) -> bool:
        """处理栈溢出异常"""
        print(f"    [Exception] 栈溢出异常")
        print(f"    ESP=0x{trap_frame.context.esp:08x}")
        print(f"    处理方式：扩展栈空间或终止进程")
        return True

    # ========================================================================
    # 系统调用处理
    # ========================================================================

    def handle_syscall(self, trap_frame: TrapFrame) -> bool:
        """处理系统调用"""
        syscall_number = trap_frame.context.eax
        print(f"    [Syscall] 系统调用处理")
        print(f"    系统调用号：{syscall_number}")
        print(f"    参数：EBX=0x{trap_frame.context.ebx:08x}, "
              f"ECX=0x{trap_frame.context.ecx:08x}")
        print(f"    执行内核服务...")
        return True

    # ========================================================================
    # 硬件中断处理
    # ========================================================================

    def handle_timer_interrupt(self, trap_frame: TrapFrame) -> bool:
        """处理时钟中断"""
        print(f"    [Interrupt] 时钟中断处理")
        print(f"    时间片到期，进行进程调度")
        print(f"    当前进程：PID=1")
        print(f"    调度算法：时间片轮转")
        return True

    def handle_keyboard_interrupt(self, trap_frame: TrapFrame) -> bool:
        """处理键盘中断"""
        print(f"    [Interrupt] 键盘中断处理")
        print(f"    读取键盘扫描码")
        print(f"    将字符放入输入缓冲区")
        return True

    def handle_disk_interrupt(self, trap_frame: TrapFrame) -> bool:
        """处理磁盘中断"""
        print(f"    [Interrupt] 磁盘中断处理")
        print(f"    磁盘I/O操作完成")
        print(f"    唤醒等待进程")
        return True

    def print_statistics(self):
        """打印陷入统计信息"""
        print("\n" + "="*70)
        print("陷入统计信息")
        print("="*70)
        print(f"总陷入次数：{self.cpu.trap_count}")
        print(f"陷入类型分布：")
        for trap_num, count in sorted(self.trap_statistics.items()):
            trap_name = self._get_trap_name(trap_num)
            print(f"  0x{trap_num:02x} ({trap_name}): {count}次")
        print("="*70)

    def _get_trap_name(self, trap_number: int) -> str:
        """获取陷入名称"""
        for trap_type in TrapType:
            if trap_type.value == trap_number:
                return trap_type.name
        return "UNKNOWN"


# ============================================================================
# 演示程序
# ============================================================================

def demo_exception_handling(handler: TrapHandler):
    """演示异常处理"""
    print("\n" + "="*70)
    print("演示1：异常处理")
    print("="*70)

    # 除零异常
    handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)

    time.sleep(0.5)

    # 缺页异常
    handler.trigger_trap(TrapType.PAGE_FAULT, error_code=0x12345000)

    time.sleep(0.5)

    # 非法指令
    handler.trigger_trap(TrapType.INVALID_OPCODE)


def demo_syscall_handling(handler: TrapHandler):
    """演示系统调用"""
    print("\n" + "="*70)
    print("演示2：系统调用陷入")
    print("="*70)

    # 设置系统调用参数
    handler.cpu.context.eax = 1  # write系统调用
    handler.cpu.context.ebx = 1  # stdout
    handler.cpu.context.ecx = 0x1000  # buffer地址

    handler.trigger_trap(TrapType.SYSCALL)


def demo_hardware_interrupt(handler: TrapHandler):
    """演示硬件中断"""
    print("\n" + "="*70)
    print("演示3：硬件中断处理")
    print("="*70)

    # 时钟中断
    handler.trigger_trap(TrapType.TIMER)

    time.sleep(0.5)

    # 键盘中断
    handler.trigger_trap(TrapType.KEYBOARD)

    time.sleep(0.5)

    # 磁盘中断
    handler.trigger_trap(TrapType.DISK)


def demo_interrupt_masking(handler: TrapHandler):
    """演示中断屏蔽"""
    print("\n" + "="*70)
    print("演示4：中断屏蔽机制")
    print("="*70)

    # 屏蔽键盘中断
    handler.ivt.mask_trap(TrapType.KEYBOARD.value)

    print("\n尝试触发被屏蔽的键盘中断：")
    handler.trigger_trap(TrapType.KEYBOARD)

    # 取消屏蔽
    handler.ivt.unmask_trap(TrapType.KEYBOARD.value)

    print("\n取消屏蔽后再次触发：")
    handler.trigger_trap(TrapType.KEYBOARD)


def demo_interrupt_disable(handler: TrapHandler):
    """演示关中断"""
    print("\n" + "="*70)
    print("演示5：关中断/开中断")
    print("="*70)

    # 关中断
    handler.cpu.disable_interrupt()

    print("\n关中断后尝试触发时钟中断：")
    handler.trigger_trap(TrapType.TIMER)

    # 开中断
    handler.cpu.enable_interrupt()

    print("\n开中断后再次触发：")
    handler.trigger_trap(TrapType.TIMER)


def demo_nested_traps(handler: TrapHandler):
    """演示陷入嵌套"""
    print("\n" + "="*70)
    print("演示6：陷入嵌套处理")
    print("="*70)

    print("\n场景：处理缺页异常时发生时钟中断")

    # 模拟：在缺页异常处理过程中触发时钟中断
    print("\n1. 触发缺页异常")
    handler.cpu.context.eip = 0x1000

    # 手动模拟嵌套
    trap_frame1 = TrapFrame(
        trap_type=TrapType.PAGE_FAULT,
        trap_number=TrapType.PAGE_FAULT.value,
        error_code=0x2000,
        context=handler.cpu.context.copy()
    )

    handler.cpu.switch_to_kernel_mode()
    handler.cpu.push_trap_frame(trap_frame1)

    print(f"  [Trap] 开始处理缺页异常")
    print(f"  [Trap] 当前嵌套层数：{handler.cpu.get_trap_nesting_level()}")

    # 在处理过程中触发时钟中断
    print("\n2. 在缺页处理过程中触发时钟中断")
    handler.trigger_trap(TrapType.TIMER)

    # 继续处理缺页
    print("\n3. 继续处理缺页异常")
    handler.cpu.pop_trap_frame()
    handler.cpu.switch_to_user_mode()
    print(f"  [Trap] 缺页异常处理完成")


def demo_trap_priority(handler: TrapHandler):
    """演示陷入优先级"""
    print("\n" + "="*70)
    print("演示7：陷入优先级")
    print("="*70)

    print("\n各类陷入的优先级：")
    traps = [
        (TrapType.DIVIDE_BY_ZERO, "除零异常"),
        (TrapType.PAGE_FAULT, "缺页异常"),
        (TrapType.TIMER, "时钟中断"),
        (TrapType.SYSCALL, "系统调用"),
    ]

    for trap_type, name in traps:
        priority = handler.ivt.get_priority(trap_type.value)
        print(f"  {name}: {priority.name}")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("陷入指令模拟程序")
    print("Trap Instruction Simulation")
    print("="*70)

    # 初始化系统
    cpu = CPU()
    handler = TrapHandler(cpu)

    # 运行演示
    demo_exception_handling(handler)
    demo_syscall_handling(handler)
    demo_hardware_interrupt(handler)
    demo_interrupt_masking(handler)
    demo_interrupt_disable(handler)
    demo_nested_traps(handler)
    demo_trap_priority(handler)

    # 统计信息
    handler.print_statistics()

    print("\n" + "="*70)
    print("✓ 所有演示完成")
    print("="*70)


if __name__ == "__main__":
    main()

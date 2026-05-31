#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Trap Instruction Simulation
陷入指令模拟程序的测试套件
"""

import unittest
from trap_instruction_simulation import (
    CPU, CPUMode, TrapType, TrapPriority, TrapVectorTable,
    TrapHandler, TrapFrame, CPUContext
)


class TestCPU(unittest.TestCase):
    """测试CPU类"""

    def setUp(self):
        self.cpu = CPU()

    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)
        self.assertTrue(self.cpu.interrupt_enabled)
        self.assertEqual(len(self.cpu.trap_stack), 0)

    def test_mode_switching(self):
        """测试模式切换"""
        # 切换到内核态
        result = self.cpu.switch_to_kernel_mode()
        self.assertTrue(result)
        self.assertEqual(self.cpu.mode, CPUMode.KERNEL_MODE)

        # 切换回用户态
        result = self.cpu.switch_to_user_mode()
        self.assertTrue(result)
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

    def test_interrupt_control(self):
        """测试中断控制"""
        # 关中断
        self.cpu.disable_interrupt()
        self.assertFalse(self.cpu.interrupt_enabled)

        # 开中断
        self.cpu.enable_interrupt()
        self.assertTrue(self.cpu.interrupt_enabled)

    def test_trap_stack(self):
        """测试陷入栈"""
        frame1 = TrapFrame(TrapType.DIVIDE_BY_ZERO, 0)
        frame2 = TrapFrame(TrapType.PAGE_FAULT, 14)

        # 压栈
        self.cpu.push_trap_frame(frame1)
        self.assertEqual(self.cpu.get_trap_nesting_level(), 1)

        self.cpu.push_trap_frame(frame2)
        self.assertEqual(self.cpu.get_trap_nesting_level(), 2)

        # 出栈
        popped = self.cpu.pop_trap_frame()
        self.assertEqual(popped.trap_type, TrapType.PAGE_FAULT)
        self.assertEqual(self.cpu.get_trap_nesting_level(), 1)

        popped = self.cpu.pop_trap_frame()
        self.assertEqual(popped.trap_type, TrapType.DIVIDE_BY_ZERO)
        self.assertEqual(self.cpu.get_trap_nesting_level(), 0)


class TestCPUContext(unittest.TestCase):
    """测试CPU上下文"""

    def test_context_copy(self):
        """测试上下文复制"""
        ctx = CPUContext(eax=100, ebx=200, eip=0x1000)
        ctx_copy = ctx.copy()

        # 验证复制正确
        self.assertEqual(ctx_copy.eax, 100)
        self.assertEqual(ctx_copy.ebx, 200)
        self.assertEqual(ctx_copy.eip, 0x1000)

        # 验证是独立副本
        ctx.eax = 999
        self.assertEqual(ctx_copy.eax, 100)


class TestTrapVectorTable(unittest.TestCase):
    """测试陷入向量表"""

    def setUp(self):
        self.ivt = TrapVectorTable()

    def test_register_handler(self):
        """测试注册处理程序"""
        def dummy_handler(frame):
            return True

        self.ivt.register(0x00, dummy_handler, TrapPriority.HIGH)

        handler = self.ivt.get_handler(0x00)
        self.assertEqual(handler, dummy_handler)

        priority = self.ivt.get_priority(0x00)
        self.assertEqual(priority, TrapPriority.HIGH)

    def test_mask_unmask(self):
        """测试屏蔽和取消屏蔽"""
        trap_num = 0x21

        # 初始未屏蔽
        self.assertFalse(self.ivt.is_masked(trap_num))

        # 屏蔽
        self.ivt.mask_trap(trap_num)
        self.assertTrue(self.ivt.is_masked(trap_num))

        # 取消屏蔽
        self.ivt.unmask_trap(trap_num)
        self.assertFalse(self.ivt.is_masked(trap_num))


class TestTrapHandler(unittest.TestCase):
    """测试陷入处理器"""

    def setUp(self):
        self.cpu = CPU()
        self.handler = TrapHandler(self.cpu)

    def test_exception_handling(self):
        """测试异常处理"""
        # 触发除零异常
        result = self.handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)
        self.assertTrue(result)

        # 验证统计
        self.assertEqual(self.handler.trap_statistics[TrapType.DIVIDE_BY_ZERO.value], 1)

    def test_syscall_handling(self):
        """测试系统调用"""
        self.cpu.context.eax = 1  # 系统调用号

        result = self.handler.trigger_trap(TrapType.SYSCALL)
        self.assertTrue(result)

        # 验证返回用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

    def test_interrupt_handling(self):
        """测试硬件中断"""
        result = self.handler.trigger_trap(TrapType.TIMER)
        self.assertTrue(result)

        result = self.handler.trigger_trap(TrapType.KEYBOARD)
        self.assertTrue(result)

    def test_masked_trap(self):
        """测试屏蔽的陷入"""
        # 屏蔽键盘中断
        self.handler.ivt.mask_trap(TrapType.KEYBOARD.value)

        # 触发被屏蔽的中断
        result = self.handler.trigger_trap(TrapType.KEYBOARD)
        self.assertFalse(result)

        # 验证未执行
        self.assertNotIn(TrapType.KEYBOARD.value, self.handler.trap_statistics)

    def test_disabled_interrupt(self):
        """测试关中断"""
        # 关中断
        self.cpu.disable_interrupt()

        # 触发硬件中断
        result = self.handler.trigger_trap(TrapType.TIMER)
        self.assertFalse(result)

    def test_page_fault_handling(self):
        """测试缺页异常"""
        result = self.handler.trigger_trap(TrapType.PAGE_FAULT, error_code=0x12345000)
        self.assertTrue(result)

        # 验证返回用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)


class TestTrapNesting(unittest.TestCase):
    """测试陷入嵌套"""

    def setUp(self):
        self.cpu = CPU()
        self.handler = TrapHandler(self.cpu)

    def test_nested_traps(self):
        """测试陷入嵌套"""
        # 第一层陷入
        frame1 = TrapFrame(TrapType.PAGE_FAULT, TrapType.PAGE_FAULT.value)
        self.cpu.switch_to_kernel_mode()
        self.cpu.push_trap_frame(frame1)

        self.assertEqual(self.cpu.get_trap_nesting_level(), 1)

        # 第二层陷入（在第一层处理过程中）
        result = self.handler.trigger_trap(TrapType.TIMER)
        self.assertTrue(result)

        # 验证第二层处理完成后，仍在内核态（因为第一层未完成）
        self.assertEqual(self.cpu.mode, CPUMode.KERNEL_MODE)
        self.assertEqual(self.cpu.get_trap_nesting_level(), 1)

        # 完成第一层
        self.cpu.pop_trap_frame()
        self.cpu.switch_to_user_mode()
        self.assertEqual(self.cpu.get_trap_nesting_level(), 0)


class TestTrapPriority(unittest.TestCase):
    """测试陷入优先级"""

    def setUp(self):
        self.cpu = CPU()
        self.handler = TrapHandler(self.cpu)

    def test_priority_levels(self):
        """测试优先级级别"""
        # 异常 - 高优先级
        priority = self.handler.ivt.get_priority(TrapType.DIVIDE_BY_ZERO.value)
        self.assertEqual(priority, TrapPriority.HIGH)

        # 硬件中断 - 中优先级
        priority = self.handler.ivt.get_priority(TrapType.TIMER.value)
        self.assertEqual(priority, TrapPriority.MEDIUM)

        # 系统调用 - 低优先级
        priority = self.handler.ivt.get_priority(TrapType.SYSCALL.value)
        self.assertEqual(priority, TrapPriority.LOW)


class TestTrapStatistics(unittest.TestCase):
    """测试陷入统计"""

    def setUp(self):
        self.cpu = CPU()
        self.handler = TrapHandler(self.cpu)

    def test_statistics_counting(self):
        """测试统计计数"""
        # 触发多次陷入
        self.handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)
        self.handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)
        self.handler.trigger_trap(TrapType.PAGE_FAULT)

        # 验证统计
        self.assertEqual(self.handler.trap_statistics[TrapType.DIVIDE_BY_ZERO.value], 2)
        self.assertEqual(self.handler.trap_statistics[TrapType.PAGE_FAULT.value], 1)
        self.assertEqual(self.cpu.trap_count, 3)


class TestTrapFrame(unittest.TestCase):
    """测试陷入帧"""

    def test_trap_frame_creation(self):
        """测试陷入帧创建"""
        ctx = CPUContext(eax=100, eip=0x1000)
        frame = TrapFrame(
            trap_type=TrapType.PAGE_FAULT,
            trap_number=14,
            error_code=0x2000,
            context=ctx
        )

        self.assertEqual(frame.trap_type, TrapType.PAGE_FAULT)
        self.assertEqual(frame.trap_number, 14)
        self.assertEqual(frame.error_code, 0x2000)
        self.assertEqual(frame.context.eax, 100)
        self.assertEqual(frame.context.eip, 0x1000)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        self.cpu = CPU()
        self.handler = TrapHandler(self.cpu)

    def test_complete_trap_flow(self):
        """测试完整的陷入流程"""
        # 初始状态：用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

        # 触发陷入
        result = self.handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)
        self.assertTrue(result)

        # 验证：返回用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

        # 验证：陷入栈为空
        self.assertEqual(self.cpu.get_trap_nesting_level(), 0)

    def test_multiple_trap_types(self):
        """测试多种陷入类型"""
        # 异常
        self.handler.trigger_trap(TrapType.DIVIDE_BY_ZERO)
        self.handler.trigger_trap(TrapType.PAGE_FAULT)

        # 系统调用
        self.handler.trigger_trap(TrapType.SYSCALL)

        # 硬件中断
        self.handler.trigger_trap(TrapType.TIMER)
        self.handler.trigger_trap(TrapType.KEYBOARD)

        # 验证统计
        self.assertEqual(self.cpu.trap_count, 5)


def run_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("陷入指令模拟程序测试套件")
    print("Test Suite for Trap Instruction Simulation")
    print("="*70 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCPU))
    suite.addTests(loader.loadTestsFromTestCase(TestCPUContext))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapVectorTable))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapNesting))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapPriority))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestTrapFrame))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"运行测试数：{result.testsRun}")
    print(f"成功：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败：{len(result.failures)}")
    print(f"错误：{len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ 所有测试通过！陷入处理机制实现正确。")
    else:
        print("\n✗ 部分测试失败，请检查实现。")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

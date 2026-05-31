#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Simulated System Call Implementation
系统调用模拟程序的测试套件
"""

import unittest
from simulated_syscall import (
    CPU, CPUMode, Kernel, LibraryWrapper,
    VirtualFileSystem, ProcessManager, SystemCallTable
)


class TestCPU(unittest.TestCase):
    """测试CPU状态切换"""

    def setUp(self):
        self.cpu = CPU()

    def test_initial_state(self):
        """测试初始状态为用户态"""
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)
        self.assertEqual(self.cpu.interrupt_count, 0)

    def test_switch_to_kernel_mode(self):
        """测试切换到内核态"""
        result = self.cpu.switch_to_kernel_mode()
        self.assertTrue(result)
        self.assertEqual(self.cpu.mode, CPUMode.KERNEL_MODE)
        self.assertIsNotNone(self.cpu.saved_context)

    def test_switch_to_user_mode(self):
        """测试切换回用户态"""
        self.cpu.switch_to_kernel_mode()
        result = self.cpu.switch_to_user_mode()
        self.assertTrue(result)
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

    def test_context_save_restore(self):
        """测试上下文保存和恢复"""
        # 设置用户态寄存器
        self.cpu.context.eax = 100
        self.cpu.context.ebx = 200

        # 切换到内核态
        self.cpu.switch_to_kernel_mode()

        # 修改寄存器（模拟内核操作）
        self.cpu.context.eax = 999

        # 切换回用户态
        self.cpu.switch_to_user_mode()

        # 验证：eax应该是新值（返回值），ebx应该恢复
        self.assertEqual(self.cpu.context.eax, 999)
        self.assertEqual(self.cpu.context.ebx, 200)

    def test_privilege_check(self):
        """测试特权级检查"""
        # 用户态
        self.assertTrue(self.cpu.check_privilege(CPUMode.USER_MODE))
        self.assertFalse(self.cpu.check_privilege(CPUMode.KERNEL_MODE))

        # 切换到内核态
        self.cpu.switch_to_kernel_mode()
        self.assertFalse(self.cpu.check_privilege(CPUMode.USER_MODE))
        self.assertTrue(self.cpu.check_privilege(CPUMode.KERNEL_MODE))

    def test_interrupt_count(self):
        """测试中断计数"""
        self.cpu.trigger_interrupt(0x80)
        self.assertEqual(self.cpu.interrupt_count, 1)

        self.cpu.switch_to_user_mode()
        self.cpu.trigger_interrupt(0x80)
        self.assertEqual(self.cpu.interrupt_count, 2)


class TestVirtualFileSystem(unittest.TestCase):
    """测试虚拟文件系统"""

    def setUp(self):
        self.vfs = VirtualFileSystem()

    def test_standard_streams(self):
        """测试标准输入输出流"""
        self.assertIn(0, self.vfs.open_files)  # stdin
        self.assertIn(1, self.vfs.open_files)  # stdout
        self.assertIn(2, self.vfs.open_files)  # stderr

    def test_create_file(self):
        """测试创建文件"""
        result = self.vfs.create_file("test.txt", b"Hello")
        self.assertTrue(result)
        self.assertIn("test.txt", self.vfs.files)
        self.assertEqual(self.vfs.files["test.txt"].content, b"Hello")

    def test_create_duplicate_file(self):
        """测试创建重复文件"""
        self.vfs.create_file("test.txt")
        result = self.vfs.create_file("test.txt")
        self.assertFalse(result)

    def test_open_file(self):
        """测试打开文件"""
        self.vfs.create_file("test.txt")
        fd = self.vfs.open_file("test.txt")
        self.assertGreaterEqual(fd, 3)
        self.assertIn(fd, self.vfs.open_files)

    def test_open_nonexistent_file(self):
        """测试打开不存在的文件"""
        fd = self.vfs.open_file("nonexistent.txt")
        self.assertEqual(fd, -1)

    def test_close_file(self):
        """测试关闭文件"""
        self.vfs.create_file("test.txt")
        fd = self.vfs.open_file("test.txt")
        result = self.vfs.close_file(fd)
        self.assertEqual(result, 0)
        self.assertNotIn(fd, self.vfs.open_files)

    def test_close_invalid_fd(self):
        """测试关闭无效的文件描述符"""
        result = self.vfs.close_file(999)
        self.assertEqual(result, -1)

    def test_read_file(self):
        """测试读取文件"""
        self.vfs.create_file("test.txt", b"Hello, World!")
        fd = self.vfs.open_file("test.txt")
        data = self.vfs.read_file(fd, 5)
        self.assertEqual(data, b"Hello")

    def test_write_file(self):
        """测试写入文件"""
        self.vfs.create_file("test.txt", b"Hello")
        fd = self.vfs.open_file("test.txt")
        bytes_written = self.vfs.write_file(fd, b"World")
        self.assertEqual(bytes_written, 5)
        self.assertEqual(self.vfs.files["test.txt"].content, b"World")

    def test_file_position(self):
        """测试文件位置指针"""
        self.vfs.create_file("test.txt", b"0123456789")
        fd = self.vfs.open_file("test.txt")

        # 读取5字节
        data1 = self.vfs.read_file(fd, 5)
        self.assertEqual(data1, b"01234")

        # 继续读取5字节
        data2 = self.vfs.read_file(fd, 5)
        self.assertEqual(data2, b"56789")


class TestProcessManager(unittest.TestCase):
    """测试进程管理器"""

    def setUp(self):
        self.pm = ProcessManager()

    def test_create_process(self):
        """测试创建进程"""
        process = self.pm.create_process("test_process")
        self.assertIsNotNone(process)
        self.assertEqual(process.name, "test_process")
        self.assertIn(process.pid, self.pm.processes)

    def test_unique_pid(self):
        """测试进程ID唯一性"""
        p1 = self.pm.create_process("proc1")
        p2 = self.pm.create_process("proc2")
        self.assertNotEqual(p1.pid, p2.pid)

    def test_get_process(self):
        """测试获取进程"""
        process = self.pm.create_process("test")
        retrieved = self.pm.get_process(process.pid)
        self.assertEqual(retrieved, process)

    def test_get_nonexistent_process(self):
        """测试获取不存在的进程"""
        result = self.pm.get_process(999)
        self.assertIsNone(result)

    def test_terminate_process(self):
        """测试终止进程"""
        process = self.pm.create_process("test")
        result = self.pm.terminate_process(process.pid)
        self.assertTrue(result)
        self.assertEqual(process.state, "TERMINATED")

    def test_parent_child_relationship(self):
        """测试父子进程关系"""
        parent = self.pm.create_process("parent")
        child = self.pm.create_process("child", parent_pid=parent.pid)
        self.assertEqual(child.parent_pid, parent.pid)


class TestSystemCallTable(unittest.TestCase):
    """测试系统调用表"""

    def setUp(self):
        self.table = SystemCallTable()

    def test_register_syscall(self):
        """测试注册系统调用"""
        def dummy_handler():
            return 0

        self.table.register(100, dummy_handler)
        handler = self.table.get_handler(100)
        self.assertEqual(handler, dummy_handler)

    def test_get_nonexistent_handler(self):
        """测试获取不存在的处理函数"""
        handler = self.table.get_handler(999)
        self.assertIsNone(handler)


class TestKernel(unittest.TestCase):
    """测试内核系统调用"""

    def setUp(self):
        self.cpu = CPU()
        self.kernel = Kernel(self.cpu)

    def test_kernel_initialization(self):
        """测试内核初始化"""
        self.assertIsNotNone(self.kernel.vfs)
        self.assertIsNotNone(self.kernel.process_manager)
        self.assertIsNotNone(self.kernel.syscall_table)
        self.assertIsNotNone(self.kernel.process_manager.current_process)

    def test_sys_open(self):
        """测试sys_open系统调用"""
        self.cpu.switch_to_kernel_mode()
        self.kernel.vfs.create_file("test.txt")
        fd = self.kernel.sys_open("test.txt", 0, 0)
        self.assertGreaterEqual(fd, 3)

    def test_sys_read(self):
        """测试sys_read系统调用"""
        self.cpu.switch_to_kernel_mode()
        self.kernel.vfs.create_file("test.txt", b"Hello")
        fd = self.kernel.sys_open("test.txt", 0, 0)
        bytes_read = self.kernel.sys_read(fd, None, 5)
        self.assertEqual(bytes_read, 5)

    def test_sys_write(self):
        """测试sys_write系统调用"""
        self.cpu.switch_to_kernel_mode()
        self.kernel.vfs.create_file("test.txt")
        fd = self.kernel.sys_open("test.txt", 0, 0)
        bytes_written = self.kernel.sys_write(fd, b"Hello", 5)
        self.assertEqual(bytes_written, 5)

    def test_sys_close(self):
        """测试sys_close系统调用"""
        self.cpu.switch_to_kernel_mode()
        self.kernel.vfs.create_file("test.txt")
        fd = self.kernel.sys_open("test.txt", 0, 0)
        result = self.kernel.sys_close(fd)
        self.assertEqual(result, 0)

    def test_sys_getpid(self):
        """测试sys_getpid系统调用"""
        self.cpu.switch_to_kernel_mode()
        pid = self.kernel.sys_getpid()
        self.assertGreater(pid, 0)

    def test_sys_fork(self):
        """测试sys_fork系统调用"""
        self.cpu.switch_to_kernel_mode()
        parent_pid = self.kernel.process_manager.current_process.pid
        child_pid = self.kernel.sys_fork()
        self.assertNotEqual(child_pid, parent_pid)
        self.assertIn(child_pid, self.kernel.process_manager.processes)

    def test_sys_exec(self):
        """测试sys_exec系统调用"""
        self.cpu.switch_to_kernel_mode()
        old_name = self.kernel.process_manager.current_process.name
        result = self.kernel.sys_exec("new_program")
        self.assertEqual(result, 0)
        self.assertEqual(self.kernel.process_manager.current_process.name, "new_program")

    def test_sys_exit(self):
        """测试sys_exit系统调用"""
        self.cpu.switch_to_kernel_mode()
        pid = self.kernel.process_manager.current_process.pid
        self.kernel.sys_exit(0)
        process = self.kernel.process_manager.get_process(pid)
        self.assertEqual(process.state, "TERMINATED")

    def test_sys_brk(self):
        """测试sys_brk系统调用"""
        self.cpu.switch_to_kernel_mode()
        process = self.kernel.process_manager.current_process
        new_addr = process.memory_base + 0x2000
        result = self.kernel.sys_brk(new_addr)
        self.assertEqual(result, new_addr)
        self.assertEqual(process.memory_size, 0x2000)

    def test_sys_time(self):
        """测试sys_time系统调用"""
        self.cpu.switch_to_kernel_mode()
        timestamp = self.kernel.sys_time()
        self.assertGreater(timestamp, 0)

    def test_dispatch_without_kernel_mode(self):
        """测试在用户态调用系统调用（应该失败）"""
        # 确保在用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)
        result = self.kernel.dispatch_syscall(SystemCallTable.SYS_GETPID)
        self.assertEqual(result, -1)

    def test_dispatch_invalid_syscall(self):
        """测试调用无效的系统调用号"""
        self.cpu.switch_to_kernel_mode()
        result = self.kernel.dispatch_syscall(999)
        self.assertEqual(result, -1)


class TestLibraryWrapper(unittest.TestCase):
    """测试库函数封装层"""

    def setUp(self):
        self.cpu = CPU()
        self.kernel = Kernel(self.cpu)
        self.lib = LibraryWrapper(self.cpu, self.kernel)

    def test_open(self):
        """测试open库函数"""
        self.kernel.vfs.create_file("test.txt")
        fd = self.lib.open("test.txt")
        self.assertGreaterEqual(fd, 3)
        # 验证返回用户态
        self.assertEqual(self.cpu.mode, CPUMode.USER_MODE)

    def test_read(self):
        """测试read库函数"""
        self.kernel.vfs.create_file("test.txt", b"Hello")
        fd = self.lib.open("test.txt")
        bytes_read = self.lib.read(fd, 5)
        self.assertEqual(bytes_read, 5)

    def test_write(self):
        """测试write库函数"""
        self.kernel.vfs.create_file("test.txt")
        fd = self.lib.open("test.txt")
        bytes_written = self.lib.write(fd, b"Hello")
        self.assertEqual(bytes_written, 5)

    def test_close(self):
        """测试close库函数"""
        self.kernel.vfs.create_file("test.txt")
        fd = self.lib.open("test.txt")
        result = self.lib.close(fd)
        self.assertEqual(result, 0)

    def test_getpid(self):
        """测试getpid库函数"""
        pid = self.lib.getpid()
        self.assertGreater(pid, 0)

    def test_fork(self):
        """测试fork库函数"""
        child_pid = self.lib.fork()
        self.assertGreater(child_pid, 0)

    def test_complete_file_workflow(self):
        """测试完整的文件操作流程"""
        # 创建文件
        self.kernel.vfs.create_file("workflow.txt", b"Initial content")

        # 打开
        fd = self.lib.open("workflow.txt")
        self.assertGreaterEqual(fd, 3)

        # 读取
        bytes_read = self.lib.read(fd, 7)
        self.assertEqual(bytes_read, 7)

        # 写入
        bytes_written = self.lib.write(fd, b"New data")
        self.assertEqual(bytes_written, 8)

        # 关闭
        result = self.lib.close(fd)
        self.assertEqual(result, 0)

        # 验证文件内容
        file_content = self.kernel.vfs.files["workflow.txt"].content
        self.assertIn(b"New data", file_content)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        self.cpu = CPU()
        self.kernel = Kernel(self.cpu)
        self.lib = LibraryWrapper(self.cpu, self.kernel)

    def test_multiple_syscalls(self):
        """测试多次系统调用"""
        # 执行多个系统调用
        pid = self.lib.getpid()
        timestamp = self.lib.time()
        child_pid = self.lib.fork()

        # 验证系统调用计数
        self.assertEqual(self.kernel.syscall_count, 3)
        self.assertEqual(self.cpu.interrupt_count, 3)

    def test_process_lifecycle(self):
        """测试进程生命周期"""
        # 获取初始进程
        pid1 = self.lib.getpid()

        # 创建子进程
        child_pid = self.lib.fork()
        self.assertNotEqual(child_pid, pid1)

        # 执行新程序
        result = self.lib.exec("new_program")
        self.assertEqual(result, 0)

        # 验证进程名称改变
        current = self.kernel.process_manager.current_process
        self.assertEqual(current.name, "new_program")

    def test_file_descriptor_management(self):
        """测试文件描述符管理"""
        # 创建多个文件
        self.kernel.vfs.create_file("file1.txt")
        self.kernel.vfs.create_file("file2.txt")
        self.kernel.vfs.create_file("file3.txt")

        # 打开多个文件
        fd1 = self.lib.open("file1.txt")
        fd2 = self.lib.open("file2.txt")
        fd3 = self.lib.open("file3.txt")

        # 验证文件描述符唯一
        self.assertNotEqual(fd1, fd2)
        self.assertNotEqual(fd2, fd3)
        self.assertNotEqual(fd1, fd3)

        # 关闭文件
        self.lib.close(fd1)
        self.lib.close(fd2)
        self.lib.close(fd3)

        # 验证文件描述符已释放
        self.assertNotIn(fd1, self.kernel.vfs.open_files)
        self.assertNotIn(fd2, self.kernel.vfs.open_files)
        self.assertNotIn(fd3, self.kernel.vfs.open_files)

    def test_memory_expansion(self):
        """测试内存扩展"""
        process = self.kernel.process_manager.current_process
        initial_size = process.memory_size

        # 扩展内存
        new_addr = process.memory_base + initial_size + 0x1000
        result = self.lib.brk(new_addr)

        # 验证内存已扩展
        self.assertEqual(result, new_addr)
        self.assertGreater(process.memory_size, initial_size)


def run_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("系统调用模拟程序测试套件")
    print("Test Suite for Simulated System Call Implementation")
    print("="*70 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCPU))
    suite.addTests(loader.loadTestsFromTestCase(TestVirtualFileSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemCallTable))
    suite.addTests(loader.loadTestsFromTestCase(TestKernel))
    suite.addTests(loader.loadTestsFromTestCase(TestLibraryWrapper))
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
        print("\n✓ 所有测试通过！系统调用模拟实现正确。")
    else:
        print("\n✗ 部分测试失败，请检查实现。")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

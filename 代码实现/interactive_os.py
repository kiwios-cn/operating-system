#!/usr/bin/env python3
"""
交互式微型操作系统
Interactive Mini Operating System

允许用户手动执行系统调用，体验操作系统的工作原理
"""

from simulated_syscall import CPU, Kernel, LibraryWrapper, SystemCallTable, CPUMode
import sys


class InteractiveOS:
    """交互式操作系统界面"""

    def __init__(self):
        """初始化操作系统"""
        self.cpu = CPU()
        self.kernel = Kernel(self.cpu)
        self.lib = LibraryWrapper(self.cpu, self.kernel)
        self.running = True

        # 创建一些测试文件
        self.kernel.vfs.create_file("hello.txt", b"Hello, World!")
        self.kernel.vfs.create_file("data.txt", b"Sample data content")

        print("=" * 70)
        print("欢迎使用交互式微型操作系统")
        print("Interactive Mini Operating System")
        print("=" * 70)
        print("\n已创建测试文件: hello.txt, data.txt")
        print("输入 'help' 查看可用命令\n")

    def show_help(self, args=None):
        """显示帮助信息"""
        print("\n" + "=" * 70)
        print("可用命令列表")
        print("=" * 70)
        print("\n【文件操作】")
        print("  open <filename>           - 打开文件")
        print("  read <fd> <count>         - 读取文件（fd=文件描述符，count=字节数）")
        print("  write <fd> <data>         - 写入文件")
        print("  close <fd>                - 关闭文件")
        print("  list                      - 列出所有文件")
        print("  create <filename> <data>  - 创建新文件")

        print("\n【进程管理】")
        print("  getpid                    - 获取当前进程ID")
        print("  fork                      - 创建子进程")
        print("  exec <program>            - 执行新程序")
        print("  wait <pid>                - 等待子进程")
        print("  ps                        - 显示所有进程")

        print("\n【内存管理】")
        print("  brk <addr>                - 调整数据段（十六进制地址，如 0x3000）")
        print("  mem                       - 显示当前进程内存信息")

        print("\n【系统信息】")
        print("  time                      - 获取系统时间")
        print("  status                    - 显示系统状态")
        print("  cpu                       - 显示CPU状态")

        print("\n【其他】")
        print("  help                      - 显示此帮助")
        print("  clear                     - 清屏")
        print("  exit / quit               - 退出系统")
        print("=" * 70 + "\n")

    def cmd_open(self, args):
        """打开文件"""
        if len(args) < 1:
            print("❌ 用法: open <filename>")
            return

        filename = args[0]
        fd = self.lib.open(filename)
        if fd >= 0:
            print(f"✓ 文件已打开，文件描述符: {fd}")
        else:
            print(f"❌ 打开文件失败")

    def cmd_read(self, args):
        """读取文件"""
        if len(args) < 2:
            print("❌ 用法: read <fd> <count>")
            return

        try:
            fd = int(args[0])
            count = int(args[1])
            bytes_read = self.lib.read(fd, count)

            if bytes_read >= 0:
                # 获取实际读取的数据
                file_obj = self.kernel.vfs.open_files.get(fd)
                if file_obj:
                    pos = file_obj.position
                    data = file_obj.content[max(0, pos-bytes_read):pos]
                    print(f"✓ 读取了 {bytes_read} 字节")
                    print(f"  数据: {data}")
            else:
                print("❌ 读取失败")
        except ValueError:
            print("❌ 参数必须是数字")

    def cmd_write(self, args):
        """写入文件"""
        if len(args) < 2:
            print("❌ 用法: write <fd> <data>")
            return

        try:
            fd = int(args[0])
            data = ' '.join(args[1:]).encode()
            bytes_written = self.lib.write(fd, data)

            if bytes_written >= 0:
                print(f"✓ 写入了 {bytes_written} 字节")
            else:
                print("❌ 写入失败")
        except ValueError:
            print("❌ 文件描述符必须是数字")

    def cmd_close(self, args):
        """关闭文件"""
        if len(args) < 1:
            print("❌ 用法: close <fd>")
            return

        try:
            fd = int(args[0])
            result = self.lib.close(fd)
            if result == 0:
                print(f"✓ 文件描述符 {fd} 已关闭")
            else:
                print("❌ 关闭失败")
        except ValueError:
            print("❌ 文件描述符必须是数字")

    def cmd_list(self, args):
        """列出所有文件"""
        print("\n文件列表:")
        print("-" * 50)
        for filename, file_obj in self.kernel.vfs.files.items():
            size = len(file_obj.content)
            print(f"  {filename:<20} {size:>8} 字节")
        print("-" * 50)
        print(f"总计: {len(self.kernel.vfs.files)} 个文件\n")

    def cmd_create(self, args):
        """创建新文件"""
        if len(args) < 2:
            print("❌ 用法: create <filename> <data>")
            return

        filename = args[0]
        data = ' '.join(args[1:]).encode()
        self.kernel.vfs.create_file(filename, data)
        print(f"✓ 文件 '{filename}' 已创建，大小: {len(data)} 字节")

    def cmd_getpid(self, args):
        """获取进程ID"""
        pid = self.lib.getpid()
        print(f"✓ 当前进程ID: {pid}")

    def cmd_fork(self, args):
        """创建子进程"""
        child_pid = self.lib.fork()
        if child_pid > 0:
            print(f"✓ 子进程已创建，PID: {child_pid}")
        else:
            print("❌ 创建子进程失败")

    def cmd_exec(self, args):
        """执行程序"""
        if len(args) < 1:
            print("❌ 用法: exec <program>")
            return

        program = args[0]
        result = self.lib.exec(program)
        if result == 0:
            print(f"✓ 程序 '{program}' 已执行")
        else:
            print("❌ 执行失败")

    def cmd_wait(self, args):
        """等待子进程"""
        if len(args) < 1:
            print("❌ 用法: wait <pid>")
            return

        try:
            pid = int(args[0])
            result = self.lib.wait(pid)
            if result == 0:
                print(f"✓ 进程 {pid} 已结束")
            else:
                print("❌ 等待失败")
        except ValueError:
            print("❌ PID必须是数字")

    def cmd_ps(self, args):
        """显示所有进程"""
        print("\n进程列表:")
        print("-" * 70)
        print(f"{'PID':<6} {'名称':<20} {'状态':<12} {'父PID':<8} {'内存'}")
        print("-" * 70)

        for pid, process in self.kernel.process_manager.processes.items():
            mem_info = f"0x{process.memory_base:08x} - 0x{process.memory_base + process.memory_size:08x}"
            print(f"{process.pid:<6} {process.name:<20} {process.state:<12} "
                  f"{process.parent_pid if process.parent_pid else 'N/A':<8} {mem_info}")

        print("-" * 70)
        print(f"总计: {len(self.kernel.process_manager.processes)} 个进程\n")

    def cmd_brk(self, args):
        """调整数据段"""
        if len(args) < 1:
            print("❌ 用法: brk <addr> (例如: brk 0x3000)")
            return

        try:
            addr = int(args[0], 16) if args[0].startswith('0x') else int(args[0])
            result = self.lib.brk(addr)
            if result >= 0:
                print(f"✓ 数据段已调整到: 0x{result:08x}")
            else:
                print("❌ 调整失败")
        except ValueError:
            print("❌ 地址格式错误（使用十六进制，如 0x3000）")

    def cmd_mem(self, args):
        """显示内存信息"""
        process = self.kernel.process_manager.current_process
        print("\n当前进程内存信息:")
        print("-" * 50)
        print(f"  进程ID:     {process.pid}")
        print(f"  进程名:     {process.name}")
        print(f"  内存基址:   0x{process.memory_base:08x}")
        print(f"  内存大小:   0x{process.memory_size:08x} ({process.memory_size} 字节)")
        print(f"  结束地址:   0x{process.memory_base + process.memory_size:08x}")
        print("-" * 50 + "\n")

    def cmd_time(self, args):
        """获取系统时间"""
        timestamp = self.lib.time()
        print(f"✓ 系统时间戳: {timestamp}")

    def cmd_status(self, args):
        """显示系统状态"""
        print("\n系统状态:")
        print("=" * 70)
        print(f"  总系统调用次数:   {self.kernel.syscall_count}")
        print(f"  总中断次数:       {self.cpu.interrupt_count}")
        print(f"  当前CPU模式:      {'内核态' if self.cpu.mode == CPUMode.KERNEL_MODE else '用户态'}")
        print(f"  总进程数:         {len(self.kernel.process_manager.processes)}")
        print(f"  当前进程:         {self.kernel.process_manager.current_process.name} (PID={self.kernel.process_manager.current_process.pid})")
        print(f"  打开的文件数:     {len(self.kernel.vfs.open_files)}")
        print(f"  文件系统文件数:   {len(self.kernel.vfs.files)}")
        print("=" * 70 + "\n")

    def cmd_cpu(self, args):
        """显示CPU状态"""
        print("\nCPU状态:")
        print("-" * 50)
        print(f"  模式:         {'内核态' if self.cpu.mode == CPUMode.KERNEL_MODE else '用户态'}")
        print(f"  特权级:       {self.cpu.mode.value}")
        print(f"  中断次数:     {self.cpu.interrupt_count}")
        print("\n  寄存器:")
        print(f"    eax = 0x{self.cpu.context.eax if isinstance(self.cpu.context.eax, int) else 0:08x}")
        print(f"    ebx = {self.cpu.context.ebx}")
        print(f"    ecx = {self.cpu.context.ecx}")
        print(f"    edx = {self.cpu.context.edx}")
        print("-" * 50 + "\n")

    def cmd_clear(self, args):
        """清屏"""
        import os
        os.system('clear' if sys.platform != 'win32' else 'cls')

    def process_command(self, command_line):
        """处理命令"""
        command_line = command_line.strip()
        if not command_line:
            return

        parts = command_line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # 命令映射
        commands = {
            'help': self.show_help,
            'open': self.cmd_open,
            'read': self.cmd_read,
            'write': self.cmd_write,
            'close': self.cmd_close,
            'list': self.cmd_list,
            'create': self.cmd_create,
            'getpid': self.cmd_getpid,
            'fork': self.cmd_fork,
            'exec': self.cmd_exec,
            'wait': self.cmd_wait,
            'ps': self.cmd_ps,
            'brk': self.cmd_brk,
            'mem': self.cmd_mem,
            'time': self.cmd_time,
            'status': self.cmd_status,
            'cpu': self.cmd_cpu,
            'clear': self.cmd_clear,
            'exit': lambda args: self.exit_system(),
            'quit': lambda args: self.exit_system(),
        }

        if cmd in commands:
            try:
                commands[cmd](args)
            except Exception as e:
                print(f"❌ 执行命令时出错: {e}")
        else:
            print(f"❌ 未知命令: {cmd}")
            print("   输入 'help' 查看可用命令")

    def exit_system(self):
        """退出系统"""
        print("\n感谢使用交互式微型操作系统！")
        print("系统统计:")
        print(f"  总系统调用: {self.kernel.syscall_count}")
        print(f"  总中断次数: {self.cpu.interrupt_count}")
        print("\n再见！\n")
        self.running = False

    def run(self):
        """运行交互式系统"""
        while self.running:
            try:
                command = input("OS> ")
                print()  # 空行
                self.process_command(command)
            except KeyboardInterrupt:
                print("\n\n使用 'exit' 或 'quit' 退出系统")
            except EOFError:
                self.exit_system()


def main():
    """主函数"""
    os = InteractiveOS()
    os.run()


if __name__ == "__main__":
    main()

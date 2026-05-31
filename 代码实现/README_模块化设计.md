# 模块化操作系统

## 📚 项目结构

```
代码实现/
├── os_core/                    # 核心模块包 ⭐
│   ├── __init__.py            # 模块导出
│   ├── cpu.py                 # CPU管理
│   ├── memory.py              # 内存管理（分页+LRU）
│   ├── process.py             # 进程管理
│   ├── scheduler.py           # 进程调度器
│   ├── filesystem.py          # 文件系统
│   └── syscall.py             # 系统调用
│
├── os_modules/                 # 扩展模块包 ⭐
│   ├── __init__.py
│   ├── thread_manager.py      # 线程管理
│   ├── deadlock_manager.py    # 死锁管理
│   ├── device_manager.py      # 设备管理
│   └── interrupt_manager.py   # 中断管理
│
├── main_os.py                  # 主程序（集成所有模块）⭐
├── complete_os.py              # 原完整版本（保留）
└── interactive_os.py           # 交互式界面
```

---

## 🎯 核心模块详解

### 1. `os_core.cpu` - CPU管理
```python
from os_core.cpu import CPU, CPUMode, CPUContext

cpu = CPU()
cpu.switch_to_kernel_mode()  # 切换到内核态
cpu.switch_to_user_mode()    # 切换回用户态
```

**功能**：
- CPU模式管理（用户态/内核态）
- CPU上下文保存/恢复
- 中断计数

---

### 2. `os_core.memory` - 内存管理
```python
from os_core.memory import MemoryManagementUnit, PAGE_SIZE

mmu = MemoryManagementUnit(num_frames=16)
mmu.create_page_table(process_id=1, num_pages=8)
physical_addr = mmu.translate_address(process_id=1, virtual_address=0x1000)
```

**功能**：
- 分页存储管理（4KB页面）
- 页表管理
- 地址转换（虚拟→物理）
- LRU页面置换算法
- 缺页处理

---

### 3. `os_core.process` - 进程管理
```python
from os_core.process import Process, ProcessState

process = Process(pid=1, name="MyProcess", num_pages=8)
process.state = ProcessState.RUNNING
```

**功能**：
- 进程控制块（PCB）
- 进程状态管理
- CPU上下文管理

---

### 4. `os_core.scheduler` - 进程调度
```python
from os_core.scheduler import RoundRobinScheduler

scheduler = RoundRobinScheduler(time_quantum=3)
scheduler.add_process(process)
current = scheduler.schedule()
scheduler.tick()
```

**功能**：
- 时间片轮转调度
- 就绪队列管理
- 上下文切换
- 调度统计

---

### 5. `os_core.filesystem` - 文件系统
```python
from os_core.filesystem import VirtualFileSystem

vfs = VirtualFileSystem()
vfs.create_file("test.txt", b"Hello")
fd = vfs.open_file("test.txt")
data = vfs.read_file(fd, 10)
vfs.close_file(fd)
```

**功能**：
- 虚拟文件系统
- 文件创建、打开、读写、关闭
- 文件描述符管理
- 标准I/O流

---

### 6. `os_core.syscall` - 系统调用
```python
from os_core.syscall import Kernel

kernel = Kernel(cpu, mmu, scheduler, vfs)
fd = kernel.sys_open("file.txt", verbose=True)
bytes_read = kernel.sys_read(fd, 10, verbose=True)
kernel.sys_close(fd, verbose=True)
```

**功能**：
- 系统调用包装器
- 用户态/内核态切换
- 5个系统调用：open, read, write, close, getpid

---

## 🔧 扩展模块详解

### 1. `os_modules.thread_manager` - 线程管理
```python
from os_modules.thread_manager import ThreadManager

mgr = ThreadManager(use_kernel_threads=True)
mgr.create_thread(process_id=1, name="Thread1", priority=5)
mgr.create_mutex("shared_resource")
mgr.run(total_time=20, verbose=True)
```

**功能**：
- 用户级线程
- 内核级线程
- 线程调度
- 互斥锁、信号量

---

### 2. `os_modules.deadlock_manager` - 死锁管理
```python
from os_modules.deadlock_manager import DeadlockManager, Resource, ResourceType

mgr = DeadlockManager(use_bankers=True)
mgr.add_resource(Resource(0, ResourceType.DISK, "Disk1", 1, 1))
success, msg = mgr.request_resource(process_id=1, resource_id=0, instances=1)
has_deadlock, deadlocked = mgr.check_deadlock()
```

**功能**：
- 银行家算法（死锁避免）
- 死锁检测
- 死锁恢复（3种策略）
- 资源分配图

---

### 3. `os_modules.device_manager` - 设备管理
```python
from os_modules.device_manager import DeviceManager, BlockDevice, SSTFScheduler

mgr = DeviceManager()
disk = BlockDevice(device_id=0, device_name="Disk0", device_type=DeviceType.BLOCK_DEVICE)
mgr.register_device(disk, SSTFScheduler())
mgr.submit_io_request(process_id=1, device_id=0, request_type=IORequestType.READ, track=50)
```

**功能**：
- 块设备、字符设备
- 4种I/O调度算法（FCFS、SSTF、SCAN、C-SCAN）
- 设备驱动程序
- 缓冲区管理

---

### 4. `os_modules.interrupt_manager` - 中断管理
```python
from os_modules.interrupt_manager import InterruptManager

mgr = InterruptManager()
mgr.trigger_interrupt(0x20, process_id=1, verbose=True)  # 时钟中断
mgr.process_interrupts(verbose=True)
```

**功能**：
- 中断向量表（IVT）
- 中断控制器
- 中断优先级
- 中断屏蔽
- 中断嵌套

---

## 🚀 使用方法

### 1. 运行模块化操作系统
```bash
python3 main_os.py
```

### 2. 使用核心模块
```python
from os_core import CPU, MemoryManagementUnit, RoundRobinScheduler
from os_core import VirtualFileSystem, Kernel, Process

# 初始化核心组件
cpu = CPU()
mmu = MemoryManagementUnit(num_frames=16)
scheduler = RoundRobinScheduler(time_quantum=3)
vfs = VirtualFileSystem()
kernel = Kernel(cpu, mmu, scheduler, vfs)

# 创建进程
process = Process(pid=1, name="MyProcess", num_pages=8)
mmu.create_page_table(process.pid, process.num_pages)
scheduler.add_process(process)

# 运行
current = scheduler.schedule()
scheduler.tick()
```

### 3. 使用扩展模块
```python
# 线程管理
from os_modules.thread_manager import ThreadManager
mgr = ThreadManager()
mgr.run()

# 死锁管理
from os_modules.deadlock_manager import DeadlockManager
mgr = DeadlockManager()

# 设备管理
from os_modules.device_manager import DeviceManager
mgr = DeviceManager()

# 中断管理
from os_modules.interrupt_manager import InterruptManager
mgr = InterruptManager()
```

---

## 💡 模块化设计优势

### ✅ 优点

1. **职责单一** - 每个模块只负责一个功能
2. **易于测试** - 可以单独测试每个模块
3. **易于扩展** - 添加新功能不影响现有代码
4. **代码复用** - 模块可以在不同项目中复用
5. **团队协作** - 不同人可以开发不同模块
6. **易于维护** - 修改一个模块不影响其他模块

### 📊 对比

| 特性 | 单文件版本 | 模块化版本 |
|------|-----------|-----------|
| 文件大小 | 28KB | 6个小文件 |
| 可维护性 | ❌ 难 | ✅ 易 |
| 可测试性 | ❌ 难 | ✅ 易 |
| 可扩展性 | ❌ 难 | ✅ 易 |
| 代码复用 | ❌ 难 | ✅ 易 |
| 团队协作 | ❌ 难 | ✅ 易 |

---

## 📝 开发指南

### 添加新的核心模块

1. 在 `os_core/` 目录创建新模块文件
2. 在 `os_core/__init__.py` 中导出
3. 在 `main_os.py` 中集成

### 添加新的扩展模块

1. 在 `os_modules/` 目录创建新模块文件
2. 在 `os_modules/__init__.py` 中导出
3. 可选：在 `main_os.py` 中集成

### 模块开发规范

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块名称
Module Name

功能描述
"""

# 导入标准库
import time
from typing import Dict, List

# 导入其他核心模块
from os_core.cpu import CPU

# 定义类和函数
class MyModule:
    """模块类"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def my_function(self):
        """功能函数"""
        pass
```

---

## 🎓 学习路径

### 初级 - 理解模块结构
1. 阅读 `main_os.py` 了解整体架构
2. 查看各个核心模块的接口
3. 运行演示程序

### 中级 - 使用模块
1. 导入核心模块创建自己的程序
2. 使用扩展模块添加功能
3. 修改示例程序

### 高级 - 扩展模块
1. 添加新的核心模块
2. 添加新的扩展模块
3. 优化现有模块

---

## 📦 文件说明

| 文件 | 大小 | 说明 |
|------|------|------|
| `main_os.py` | 主程序 | 集成所有模块的完整操作系统 |
| `os_core/cpu.py` | ~2KB | CPU管理模块 |
| `os_core/memory.py` | ~8KB | 内存管理模块 |
| `os_core/process.py` | ~1KB | 进程管理模块 |
| `os_core/scheduler.py` | ~2KB | 调度器模块 |
| `os_core/filesystem.py` | ~2KB | 文件系统模块 |
| `os_core/syscall.py` | ~3KB | 系统调用模块 |
| `complete_os.py` | 28KB | 原完整版本（保留参考）|

---

## 🏆 总结

**模块化操作系统**实现了：

✅ **核心功能**（6个模块）
- CPU管理
- 内存管理
- 进程管理
- 进程调度
- 文件系统
- 系统调用

✅ **扩展功能**（4个模块）
- 线程管理
- 死锁管理
- 设备管理
- 中断管理

✅ **设计优势**
- 模块化、可扩展、易维护
- 职责单一、高内聚低耦合
- 适合教学和实际开发

---

**这是一个完整的、模块化的、教学级操作系统！** 🎉

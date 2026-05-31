# 教学级操作系统实现

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OS](https://img.shields.io/badge/OS-Educational-orange.svg)]()

一个完整的、模块化的、教学级操作系统实现，涵盖操作系统的所有核心功能模块。

[English](README_EN.md) | 简体中文

## 📚 项目简介

本项目使用Python实现了一个功能完整的教学级操作系统，包含：

- ✅ **进程管理与调度** - 时间片轮转调度算法
- ✅ **内存管理** - 分页存储管理、LRU页面置换
- ✅ **线程管理** - 用户级线程、内核级线程
- ✅ **文件系统** - 虚拟文件系统
- ✅ **设备管理** - 4种I/O调度算法
- ✅ **死锁管理** - 银行家算法、死锁检测与恢复
- ✅ **中断管理** - 中断向量表、中断控制器
- ✅ **系统调用** - 用户态/内核态切换

## 🎯 特性

### 核心功能
- **模块化设计** - 清晰的模块划分，易于理解和扩展
- **完整实现** - 涵盖操作系统的所有核心模块
- **可视化输出** - 详细的运行日志，便于学习
- **教学友好** - 适合操作系统课程教学和实验

### 技术亮点
- 分页存储管理（4KB页面）
- LRU页面置换算法
- 时间片轮转调度
- 银行家算法（死锁避免）
- 4种磁盘调度算法（FCFS、SSTF、SCAN、C-SCAN）
- 用户态/内核态切换
- 中断优先级管理

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 无需额外依赖库

### 安装

```bash
git clone https://github.com/yourusername/educational-os.git
cd educational-os/代码实现
```

### 运行

```bash
# 运行模块化操作系统
python3 main_os.py

# 运行线程管理演示
python3 os_modules/thread_manager.py

# 运行死锁管理演示
python3 os_modules/deadlock_manager.py

# 运行设备管理演示
python3 os_modules/device_manager.py

# 运行中断管理演示
python3 os_modules/interrupt_manager.py

# 运行交互式操作系统
python3 interactive_os.py
```

## 📁 项目结构

```
代码实现/
├── os_core/                    # 核心模块
│   ├── cpu.py                 # CPU管理
│   ├── memory.py              # 内存管理
│   ├── process.py             # 进程管理
│   ├── scheduler.py           # 进程调度
│   ├── filesystem.py          # 文件系统
│   └── syscall.py             # 系统调用
│
├── os_modules/                 # 扩展模块
│   ├── thread_manager.py      # 线程管理
│   ├── deadlock_manager.py    # 死锁管理
│   ├── device_manager.py      # 设备管理
│   └── interrupt_manager.py   # 中断管理
│
├── main_os.py                  # 主程序
├── interactive_os.py           # 交互式界面
└── README_模块化设计.md        # 详细文档
```

## 💡 使用示例

### 创建和运行进程

```python
from os_core import CPU, MemoryManagementUnit, RoundRobinScheduler
from os_core import VirtualFileSystem, Kernel, Process

# 初始化操作系统组件
cpu = CPU()
mmu = MemoryManagementUnit(num_frames=16)
scheduler = RoundRobinScheduler(time_quantum=3)
vfs = VirtualFileSystem()
kernel = Kernel(cpu, mmu, scheduler, vfs)

# 创建进程
process = Process(pid=1, name="MyProcess", num_pages=8)
mmu.create_page_table(process.pid, process.num_pages)
scheduler.add_process(process)

# 调度运行
current = scheduler.schedule()
scheduler.tick()
```

### 使用线程管理

```python
from os_modules.thread_manager import ThreadManager

mgr = ThreadManager(use_kernel_threads=True)
mgr.create_thread(1, "Thread1", priority=5)
mgr.create_mutex("shared_resource")
mgr.run(total_time=20, verbose=True)
```

### 使用死锁管理

```python
from os_modules.deadlock_manager import DeadlockManager, Resource, ResourceType

mgr = DeadlockManager(use_bankers=True)
mgr.add_resource(Resource(0, ResourceType.DISK, "Disk1", 1, 1))
success, msg = mgr.request_resource(process_id=1, resource_id=0, instances=1)
```

## 📊 运行效果

```
模块化操作系统启动
时间片大小: 3 时间单位
页面大小: 4KB
物理页框数: 16
物理内存: 64KB

【调度统计】
总时钟周期:     30
上下文切换:     5
系统调用:       5

【内存统计】
总访问次数:     11
页面命中:       3
缺页次数:       8
命中率:         27.27%
```

## 🎓 教学价值

### 适用课程
- 操作系统原理
- 计算机系统结构
- 系统编程

### 学习目标
1. 理解操作系统核心概念
2. 掌握关键算法实现
3. 体验系统设计过程

## 📖 文档

- [模块化设计文档](代码实现/README_模块化设计.md)
- [完整功能说明](代码实现/README_完整操作系统.md)
- [API文档](docs/API.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- **Your Name** - *Initial work*

## 🙏 致谢

- 感谢所有为操作系统教育做出贡献的人
- 参考教材：《操作系统概念》、《现代操作系统》

## 📧 联系方式

- 项目主页: https://github.com/yourusername/educational-os
- 问题反馈: https://github.com/yourusername/educational-os/issues

## ⭐ Star History

如果这个项目对你有帮助，请给一个Star！

---

**注意**: 这是一个教学项目，用于学习操作系统原理，不适用于生产环境。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备管理模块
Device Management Module

实现：
1. 设备分类（块设备、字符设备）
2. 设备驱动程序
3. I/O调度算法（FCFS、SSTF、SCAN、C-SCAN）
4. 缓冲区管理
5. 设备分配与回收
6. 中断处理
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import heapq


# ============================================================================
# 设备类型和状态
# ============================================================================

class DeviceType(Enum):
    """设备类型"""
    BLOCK_DEVICE = "块设备"      # 磁盘、U盘等
    CHARACTER_DEVICE = "字符设备"  # 键盘、鼠标、打印机等
    NETWORK_DEVICE = "网络设备"    # 网卡等


class DeviceState(Enum):
    """设备状态"""
    IDLE = "空闲"
    BUSY = "忙碌"
    ERROR = "错误"
    OFFLINE = "离线"


class IORequestType(Enum):
    """I/O请求类型"""
    READ = "读"
    WRITE = "写"


# ============================================================================
# I/O请求
# ============================================================================

@dataclass
class IORequest:
    """I/O请求"""
    request_id: int
    process_id: int
    device_id: int
    request_type: IORequestType

    # 块设备专用
    track: int = 0        # 磁道号
    sector: int = 0       # 扇区号
    block_count: int = 1  # 块数

    # 字符设备专用
    data: bytes = b""     # 数据

    # 时间信息
    arrival_time: float = 0.0
    start_time: float = 0.0
    finish_time: float = 0.0

    def __str__(self):
        return f"IORequest(id={self.request_id}, pid={self.process_id}, type={self.request_type.value}, track={self.track})"

    def __lt__(self, other):
        """用于优先队列排序"""
        return self.track < other.track


# ============================================================================
# 设备基类
# ============================================================================

@dataclass
class Device:
    """设备基类"""
    device_id: int
    device_name: str
    device_type: DeviceType
    state: DeviceState = DeviceState.IDLE

    # 设备特性
    transfer_rate: int = 1000  # 传输速率（KB/s）

    # 统计信息
    total_requests: int = 0
    completed_requests: int = 0
    total_wait_time: float = 0.0
    total_service_time: float = 0.0

    def __str__(self):
        return f"{self.device_name}({self.device_type.value}): {self.state.value}"


# ============================================================================
# 块设备（磁盘）
# ============================================================================

@dataclass
class BlockDevice(Device):
    """块设备（如磁盘）"""
    # 磁盘参数
    num_tracks: int = 200      # 磁道数
    num_sectors: int = 64      # 每磁道扇区数
    sector_size: int = 512     # 扇区大小（字节）

    # 磁头位置
    current_track: int = 0     # 当前磁道

    # 寻道时间参数
    seek_time_per_track: float = 0.001  # 每磁道寻道时间（秒）

    def seek(self, target_track: int) -> float:
        """
        寻道操作

        Returns:
            寻道时间（秒）
        """
        distance = abs(target_track - self.current_track)
        seek_time = distance * self.seek_time_per_track
        self.current_track = target_track
        return seek_time

    def calculate_service_time(self, request: IORequest) -> float:
        """计算服务时间"""
        # 寻道时间
        seek_time = abs(request.track - self.current_track) * self.seek_time_per_track

        # 旋转延迟（平均半圈）
        rotation_time = 0.005  # 5ms

        # 传输时间
        transfer_time = (request.block_count * self.sector_size) / (self.transfer_rate * 1024)

        return seek_time + rotation_time + transfer_time


# ============================================================================
# 字符设备
# ============================================================================

@dataclass
class CharacterDevice(Device):
    """字符设备（如打印机、键盘）"""
    # 字符设备参数
    buffer_size: int = 1024    # 缓冲区大小
    current_buffer: bytes = b""  # 当前缓冲区

    def write_char(self, data: bytes) -> float:
        """写字符"""
        self.current_buffer += data
        # 模拟传输时间
        return len(data) / (self.transfer_rate * 1024)

    def read_char(self, count: int) -> Tuple[bytes, float]:
        """读字符"""
        data = self.current_buffer[:count]
        self.current_buffer = self.current_buffer[count:]
        # 模拟传输时间
        transfer_time = len(data) / (self.transfer_rate * 1024)
        return data, transfer_time


# ============================================================================
# I/O调度算法
# ============================================================================

class IOScheduler:
    """I/O调度器基类"""

    def __init__(self, name: str):
        self.name = name
        self.request_queue: List[IORequest] = []

    def add_request(self, request: IORequest):
        """添加I/O请求"""
        self.request_queue.append(request)

    def get_next_request(self, current_track: int) -> Optional[IORequest]:
        """获取下一个请求（由子类实现）"""
        raise NotImplementedError


class FCFSScheduler(IOScheduler):
    """先来先服务（FCFS）调度"""

    def __init__(self):
        super().__init__("FCFS")

    def get_next_request(self, current_track: int) -> Optional[IORequest]:
        """按到达顺序服务"""
        if self.request_queue:
            return self.request_queue.pop(0)
        return None


class SSTFScheduler(IOScheduler):
    """最短寻道时间优先（SSTF）调度"""

    def __init__(self):
        super().__init__("SSTF")

    def get_next_request(self, current_track: int) -> Optional[IORequest]:
        """选择距离当前磁道最近的请求"""
        if not self.request_queue:
            return None

        # 找到距离最近的请求
        min_distance = float('inf')
        selected_idx = 0

        for i, req in enumerate(self.request_queue):
            distance = abs(req.track - current_track)
            if distance < min_distance:
                min_distance = distance
                selected_idx = i

        return self.request_queue.pop(selected_idx)


class SCANScheduler(IOScheduler):
    """扫描（SCAN/电梯）调度"""

    def __init__(self, max_track: int = 200):
        super().__init__("SCAN")
        self.max_track = max_track
        self.direction = 1  # 1=向外，-1=向内

    def get_next_request(self, current_track: int) -> Optional[IORequest]:
        """电梯算法：沿一个方向扫描"""
        if not self.request_queue:
            return None

        # 按磁道号排序
        self.request_queue.sort(key=lambda r: r.track)

        # 找到当前方向上最近的请求
        if self.direction == 1:  # 向外
            for i, req in enumerate(self.request_queue):
                if req.track >= current_track:
                    return self.request_queue.pop(i)
            # 到达边界，改变方向
            self.direction = -1
            return self.request_queue.pop(-1) if self.request_queue else None
        else:  # 向内
            for i in range(len(self.request_queue) - 1, -1, -1):
                req = self.request_queue[i]
                if req.track <= current_track:
                    return self.request_queue.pop(i)
            # 到达边界，改变方向
            self.direction = 1
            return self.request_queue.pop(0) if self.request_queue else None


class CSCANScheduler(IOScheduler):
    """循环扫描（C-SCAN）调度"""

    def __init__(self, max_track: int = 200):
        super().__init__("C-SCAN")
        self.max_track = max_track

    def get_next_request(self, current_track: int) -> Optional[IORequest]:
        """单向扫描，到达末端后返回起点"""
        if not self.request_queue:
            return None

        # 按磁道号排序
        self.request_queue.sort(key=lambda r: r.track)

        # 找到当前位置之后的第一个请求
        for i, req in enumerate(self.request_queue):
            if req.track >= current_track:
                return self.request_queue.pop(i)

        # 没有找到，返回最小的（循环到起点）
        return self.request_queue.pop(0) if self.request_queue else None


# ============================================================================
# 缓冲区管理
# ============================================================================

@dataclass
class Buffer:
    """缓冲区"""
    buffer_id: int
    size: int
    data: bytes = b""
    is_full: bool = False
    is_dirty: bool = False  # 是否被修改过

    def write(self, data: bytes) -> bool:
        """写入缓冲区"""
        if len(data) <= self.size:
            self.data = data
            self.is_full = True
            self.is_dirty = True
            return True
        return False

    def read(self) -> bytes:
        """读取缓冲区"""
        return self.data

    def clear(self):
        """清空缓冲区"""
        self.data = b""
        self.is_full = False
        self.is_dirty = False


class BufferPool:
    """缓冲池"""

    def __init__(self, num_buffers: int = 4, buffer_size: int = 4096):
        """
        初始化缓冲池

        Args:
            num_buffers: 缓冲区数量
            buffer_size: 每个缓冲区大小
        """
        self.buffers: List[Buffer] = []
        for i in range(num_buffers):
            self.buffers.append(Buffer(buffer_id=i, size=buffer_size))

        self.free_list: deque = deque(range(num_buffers))  # 空闲缓冲区列表

    def allocate_buffer(self) -> Optional[Buffer]:
        """分配缓冲区"""
        if self.free_list:
            buffer_id = self.free_list.popleft()
            return self.buffers[buffer_id]
        return None

    def release_buffer(self, buffer: Buffer):
        """释放缓冲区"""
        buffer.clear()
        self.free_list.append(buffer.buffer_id)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_buffers': len(self.buffers),
            'free_buffers': len(self.free_list),
            'used_buffers': len(self.buffers) - len(self.free_list)
        }


# ============================================================================
# 设备驱动程序
# ============================================================================

class DeviceDriver:
    """设备驱动程序"""

    def __init__(self, device: Device, scheduler: IOScheduler):
        """
        初始化设备驱动

        Args:
            device: 设备对象
            scheduler: I/O调度器
        """
        self.device = device
        self.scheduler = scheduler
        self.current_request: Optional[IORequest] = None

        # 统计信息
        self.total_seek_distance = 0
        self.total_requests = 0

    def submit_request(self, request: IORequest, verbose: bool = False):
        """提交I/O请求"""
        request.arrival_time = time.time()
        self.scheduler.add_request(request)
        self.device.total_requests += 1

        if verbose:
            print(f"    [Driver] 提交请求: {request}")

    def process_requests(self, verbose: bool = False) -> bool:
        """处理I/O请求"""
        if self.device.state == DeviceState.BUSY:
            return False

        # 获取下一个请求
        if isinstance(self.device, BlockDevice):
            next_request = self.scheduler.get_next_request(self.device.current_track)
        else:
            next_request = self.scheduler.get_next_request(0)

        if not next_request:
            return False

        # 处理请求
        self.current_request = next_request
        self.device.state = DeviceState.BUSY
        next_request.start_time = time.time()

        if verbose:
            print(f"    [Driver] 处理请求: {next_request}")

        # 执行I/O操作
        if isinstance(self.device, BlockDevice):
            service_time = self.device.calculate_service_time(next_request)
            seek_distance = abs(next_request.track - self.device.current_track)
            self.total_seek_distance += seek_distance
            self.device.seek(next_request.track)

            if verbose:
                print(f"    [Driver] 寻道: {self.device.current_track} -> {next_request.track} (距离={seek_distance})")
        else:
            if next_request.request_type == IORequestType.WRITE:
                service_time = self.device.write_char(next_request.data)
            else:
                _, service_time = self.device.read_char(len(next_request.data))

        # 完成请求
        next_request.finish_time = time.time()
        wait_time = next_request.start_time - next_request.arrival_time

        self.device.total_wait_time += wait_time
        self.device.total_service_time += service_time
        self.device.completed_requests += 1
        self.total_requests += 1

        self.device.state = DeviceState.IDLE
        self.current_request = None

        if verbose:
            print(f"    [Driver] 请求完成，等待时间={wait_time:.4f}s, 服务时间={service_time:.4f}s")

        return True


# ============================================================================
# 设备管理器
# ============================================================================

class DeviceManager:
    """设备管理器"""

    def __init__(self):
        """初始化设备管理器"""
        self.devices: Dict[int, Device] = {}
        self.drivers: Dict[int, DeviceDriver] = {}
        self.buffer_pool = BufferPool(num_buffers=4, buffer_size=4096)
        self.next_device_id = 1
        self.next_request_id = 1

        print("\n" + "=" * 70)
        print("设备管理系统初始化")
        print("=" * 70)

    def register_device(self, device: Device, scheduler: IOScheduler,
                       verbose: bool = False) -> int:
        """
        注册设备

        Args:
            device: 设备对象
            scheduler: I/O调度器

        Returns:
            设备ID
        """
        device_id = self.next_device_id
        self.next_device_id += 1

        device.device_id = device_id
        self.devices[device_id] = device

        # 创建设备驱动
        driver = DeviceDriver(device, scheduler)
        self.drivers[device_id] = driver

        if verbose:
            print(f"  [DevMgr] 注册设备: {device}")

        return device_id

    def submit_io_request(self, process_id: int, device_id: int,
                         request_type: IORequestType, track: int = 0,
                         data: bytes = b"", verbose: bool = False) -> int:
        """
        提交I/O请求

        Returns:
            请求ID
        """
        request_id = self.next_request_id
        self.next_request_id += 1

        request = IORequest(
            request_id=request_id,
            process_id=process_id,
            device_id=device_id,
            request_type=request_type,
            track=track,
            data=data
        )

        if device_id in self.drivers:
            self.drivers[device_id].submit_request(request, verbose)

        return request_id

    def process_all_requests(self, verbose: bool = False):
        """处理所有设备的I/O请求"""
        for device_id, driver in self.drivers.items():
            driver.process_requests(verbose)

    def show_device_status(self):
        """显示设备状态"""
        print("\n" + "=" * 70)
        print("设备状态")
        print("=" * 70)

        for device_id, device in self.devices.items():
            print(f"\n设备 #{device_id}: {device}")
            print(f"  总请求数:     {device.total_requests}")
            print(f"  已完成:       {device.completed_requests}")

            if device.completed_requests > 0:
                avg_wait = device.total_wait_time / device.completed_requests
                avg_service = device.total_service_time / device.completed_requests
                print(f"  平均等待时间: {avg_wait:.4f}s")
                print(f"  平均服务时间: {avg_service:.4f}s")

            if isinstance(device, BlockDevice):
                driver = self.drivers[device_id]
                if driver.total_requests > 0:
                    avg_seek = driver.total_seek_distance / driver.total_requests
                    print(f"  平均寻道距离: {avg_seek:.2f} 磁道")
                print(f"  当前磁道:     {device.current_track}")

        # 缓冲池状态
        buffer_stats = self.buffer_pool.get_statistics()
        print(f"\n缓冲池状态:")
        print(f"  总缓冲区:     {buffer_stats['total_buffers']}")
        print(f"  空闲缓冲区:   {buffer_stats['free_buffers']}")
        print(f"  使用中:       {buffer_stats['used_buffers']}")

        print("=" * 70)


# ============================================================================
# 演示程序
# ============================================================================

def demo_disk_scheduling():
    """演示磁盘调度算法"""
    print("\n" + "=" * 70)
    print("磁盘调度算法演示")
    print("=" * 70)

    # 测试不同的调度算法
    algorithms = [
        ("FCFS", FCFSScheduler()),
        ("SSTF", SSTFScheduler()),
        ("SCAN", SCANScheduler(max_track=200)),
        ("C-SCAN", CSCANScheduler(max_track=200))
    ]

    # 请求序列（磁道号）
    request_tracks = [98, 183, 37, 122, 14, 124, 65, 67]
    initial_track = 53

    for algo_name, scheduler in algorithms:
        print(f"\n{'='*70}")
        print(f"算法: {algo_name}")
        print(f"{'='*70}")

        # 创建磁盘设备
        disk = BlockDevice(
            device_id=1,
            device_name=f"Disk_{algo_name}",
            device_type=DeviceType.BLOCK_DEVICE,
            num_tracks=200,
            current_track=initial_track
        )

        # 创建设备管理器
        mgr = DeviceManager()
        device_id = mgr.register_device(disk, scheduler, verbose=False)

        # 提交请求
        print(f"\n初始磁道: {initial_track}")
        print(f"请求序列: {request_tracks}")
        print(f"\n处理顺序:")

        for i, track in enumerate(request_tracks):
            mgr.submit_io_request(
                process_id=1,
                device_id=device_id,
                request_type=IORequestType.READ,
                track=track,
                verbose=False
            )

        # 处理所有请求
        current_track = initial_track
        total_seek = 0

        while True:
            old_track = disk.current_track
            processed = mgr.drivers[device_id].process_requests(verbose=False)
            if not processed:
                break

            new_track = disk.current_track
            seek_distance = abs(new_track - old_track)
            total_seek += seek_distance
            print(f"  {old_track} -> {new_track} (移动 {seek_distance} 磁道)")

        print(f"\n总寻道距离: {total_seek} 磁道")
        print(f"平均寻道距离: {total_seek / len(request_tracks):.2f} 磁道")


def demo_device_management():
    """演示设备管理"""
    print("\n" + "=" * 70)
    print("设备管理演示")
    print("=" * 70)

    # 创建设备管理器
    mgr = DeviceManager()

    # 注册磁盘设备
    disk = BlockDevice(
        device_id=0,
        device_name="Disk0",
        device_type=DeviceType.BLOCK_DEVICE,
        num_tracks=200,
        current_track=100
    )
    disk_id = mgr.register_device(disk, SSTFScheduler(), verbose=True)

    # 注册打印机设备
    printer = CharacterDevice(
        device_id=0,
        device_name="Printer0",
        device_type=DeviceType.CHARACTER_DEVICE,
        transfer_rate=100  # 100 KB/s
    )
    printer_id = mgr.register_device(printer, FCFSScheduler(), verbose=True)

    print("\n" + "=" * 70)
    print("提交I/O请求")
    print("=" * 70)

    # 提交磁盘请求
    for track in [50, 150, 75, 125, 90]:
        mgr.submit_io_request(1, disk_id, IORequestType.READ, track=track, verbose=True)

    # 提交打印机请求
    mgr.submit_io_request(2, printer_id, IORequestType.WRITE, data=b"Hello, World!", verbose=True)

    print("\n" + "=" * 70)
    print("处理I/O请求")
    print("=" * 70)

    # 处理所有请求
    for i in range(10):
        print(f"\n--- 处理轮次 {i + 1} ---")
        mgr.process_all_requests(verbose=True)

    # 显示设备状态
    mgr.show_device_status()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("设备管理系统演示")
    print("=" * 70)

    # 1. 磁盘调度算法对比
    demo_disk_scheduling()

    # 2. 设备管理
    demo_device_management()


if __name__ == "__main__":
    main()

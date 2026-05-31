#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存管理模块
Memory Management Module
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict


# 内存管理常量
PAGE_SIZE = 4096  # 页面大小：4KB
PHYSICAL_MEMORY_SIZE = 64 * 1024  # 物理内存：64KB
NUM_PHYSICAL_FRAMES = PHYSICAL_MEMORY_SIZE // PAGE_SIZE  # 16个页框
VIRTUAL_MEMORY_SIZE = 256 * 1024  # 虚拟内存：256KB


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

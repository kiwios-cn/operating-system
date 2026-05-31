#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
死锁检测与处理模块
Deadlock Detection and Handling Module

实现：
1. 资源分配图
2. 银行家算法（死锁避免）
3. 死锁检测算法
4. 死锁恢复策略
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import copy


# ============================================================================
# 资源类型
# ============================================================================

class ResourceType(Enum):
    """资源类型"""
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    PRINTER = "PRINTER"
    FILE = "FILE"


@dataclass
class Resource:
    """资源"""
    resource_id: int
    resource_type: ResourceType
    name: str
    total_instances: int  # 总实例数
    available_instances: int  # 可用实例数

    def __str__(self):
        return f"{self.name}({self.resource_type.value}): {self.available_instances}/{self.total_instances}"


# ============================================================================
# 资源分配图
# ============================================================================

@dataclass
class ResourceAllocation:
    """资源分配记录"""
    process_id: int
    resource_id: int
    instances: int  # 分配的实例数


@dataclass
class ResourceRequest:
    """资源请求记录"""
    process_id: int
    resource_id: int
    instances: int  # 请求的实例数


class ResourceAllocationGraph:
    """资源分配图"""

    def __init__(self):
        self.resources: Dict[int, Resource] = {}
        self.allocations: List[ResourceAllocation] = []  # 已分配
        self.requests: List[ResourceRequest] = []  # 等待中的请求

    def add_resource(self, resource: Resource):
        """添加资源"""
        self.resources[resource.resource_id] = resource

    def allocate(self, process_id: int, resource_id: int, instances: int) -> bool:
        """分配资源"""
        resource = self.resources.get(resource_id)
        if not resource or resource.available_instances < instances:
            return False

        # 分配资源
        resource.available_instances -= instances
        self.allocations.append(ResourceAllocation(process_id, resource_id, instances))
        return True

    def release(self, process_id: int, resource_id: int, instances: int) -> bool:
        """释放资源"""
        resource = self.resources.get(resource_id)
        if not resource:
            return False

        # 查找分配记录
        for alloc in self.allocations:
            if alloc.process_id == process_id and alloc.resource_id == resource_id:
                if alloc.instances >= instances:
                    alloc.instances -= instances
                    resource.available_instances += instances

                    # 如果完全释放，移除记录
                    if alloc.instances == 0:
                        self.allocations.remove(alloc)
                    return True
        return False

    def request(self, process_id: int, resource_id: int, instances: int):
        """请求资源（加入等待队列）"""
        self.requests.append(ResourceRequest(process_id, resource_id, instances))

    def get_allocated(self, process_id: int, resource_id: int) -> int:
        """获取进程已分配的资源数"""
        for alloc in self.allocations:
            if alloc.process_id == process_id and alloc.resource_id == resource_id:
                return alloc.instances
        return 0

    def get_requested(self, process_id: int, resource_id: int) -> int:
        """获取进程请求的资源数"""
        for req in self.requests:
            if req.process_id == process_id and req.resource_id == resource_id:
                return req.instances
        return 0


# ============================================================================
# 银行家算法（死锁避免）
# ============================================================================

class BankersAlgorithm:
    """银行家算法 - 死锁避免"""

    def __init__(self, num_processes: int, num_resources: int):
        """
        初始化银行家算法

        Args:
            num_processes: 进程数
            num_resources: 资源类型数
        """
        self.num_processes = num_processes
        self.num_resources = num_resources

        # 可用资源向量
        self.available: List[int] = [0] * num_resources

        # 最大需求矩阵
        self.max_demand: List[List[int]] = [[0] * num_resources for _ in range(num_processes)]

        # 已分配矩阵
        self.allocation: List[List[int]] = [[0] * num_resources for _ in range(num_processes)]

        # 需求矩阵 (Need = Max - Allocation)
        self.need: List[List[int]] = [[0] * num_resources for _ in range(num_processes)]

    def set_available(self, available: List[int]):
        """设置可用资源"""
        self.available = available.copy()

    def set_max_demand(self, process_id: int, max_demand: List[int]):
        """设置进程的最大需求"""
        self.max_demand[process_id] = max_demand.copy()
        self._update_need()

    def set_allocation(self, process_id: int, allocation: List[int]):
        """设置进程的已分配资源"""
        self.allocation[process_id] = allocation.copy()
        self._update_need()

    def _update_need(self):
        """更新需求矩阵"""
        for i in range(self.num_processes):
            for j in range(self.num_resources):
                self.need[i][j] = self.max_demand[i][j] - self.allocation[i][j]

    def is_safe_state(self) -> Tuple[bool, List[int]]:
        """
        检查系统是否处于安全状态

        Returns:
            (是否安全, 安全序列)
        """
        # 工作向量（可用资源的副本）
        work = self.available.copy()

        # 完成标记
        finish = [False] * self.num_processes

        # 安全序列
        safe_sequence = []

        # 查找可以完成的进程
        while len(safe_sequence) < self.num_processes:
            found = False

            for i in range(self.num_processes):
                if finish[i]:
                    continue

                # 检查进程i的需求是否可以满足
                can_allocate = all(self.need[i][j] <= work[j] for j in range(self.num_resources))

                if can_allocate:
                    # 模拟分配资源并完成进程
                    for j in range(self.num_resources):
                        work[j] += self.allocation[i][j]

                    finish[i] = True
                    safe_sequence.append(i)
                    found = True
                    break

            if not found:
                # 无法找到可完成的进程，系统不安全
                return False, []

        return True, safe_sequence

    def request_resources(self, process_id: int, request: List[int]) -> Tuple[bool, str]:
        """
        请求资源（使用银行家算法检查）

        Args:
            process_id: 进程ID
            request: 请求的资源向量

        Returns:
            (是否批准, 原因)
        """
        # 1. 检查请求是否超过需求
        for j in range(self.num_resources):
            if request[j] > self.need[process_id][j]:
                return False, f"请求超过最大需求 (资源{j}: 请求{request[j]} > 需求{self.need[process_id][j]})"

        # 2. 检查请求是否超过可用资源
        for j in range(self.num_resources):
            if request[j] > self.available[j]:
                return False, f"请求超过可用资源 (资源{j}: 请求{request[j]} > 可用{self.available[j]})"

        # 3. 试探性分配
        old_available = self.available.copy()
        old_allocation = [row.copy() for row in self.allocation]
        old_need = [row.copy() for row in self.need]

        for j in range(self.num_resources):
            self.available[j] -= request[j]
            self.allocation[process_id][j] += request[j]
            self.need[process_id][j] -= request[j]

        # 4. 检查安全性
        is_safe, safe_seq = self.is_safe_state()

        if is_safe:
            return True, f"批准请求，安全序列: {safe_seq}"
        else:
            # 恢复状态
            self.available = old_available
            self.allocation = old_allocation
            self.need = old_need
            return False, "拒绝请求：会导致不安全状态"


# ============================================================================
# 死锁检测算法
# ============================================================================

class DeadlockDetector:
    """死锁检测器"""

    def __init__(self, rag: ResourceAllocationGraph):
        """
        初始化死锁检测器

        Args:
            rag: 资源分配图
        """
        self.rag = rag

    def detect_deadlock(self) -> Tuple[bool, List[int]]:
        """
        检测死锁

        Returns:
            (是否存在死锁, 死锁进程列表)
        """
        # 获取所有进程ID
        process_ids = set()
        for alloc in self.rag.allocations:
            process_ids.add(alloc.process_id)
        for req in self.rag.requests:
            process_ids.add(req.process_id)

        if not process_ids:
            return False, []

        # 工作向量（可用资源）
        work = {}
        for rid, resource in self.rag.resources.items():
            work[rid] = resource.available_instances

        # 完成标记
        finish = {pid: False for pid in process_ids}

        # 标记没有请求的进程为已完成
        for pid in process_ids:
            has_request = any(req.process_id == pid for req in self.rag.requests)
            if not has_request:
                finish[pid] = True

        # 查找可以完成的进程
        changed = True
        while changed:
            changed = False

            for pid in process_ids:
                if finish[pid]:
                    continue

                # 检查进程的所有请求是否可以满足
                can_satisfy = True
                for req in self.rag.requests:
                    if req.process_id == pid:
                        if work.get(req.resource_id, 0) < req.instances:
                            can_satisfy = False
                            break

                if can_satisfy:
                    # 释放该进程持有的所有资源
                    for alloc in self.rag.allocations:
                        if alloc.process_id == pid:
                            work[alloc.resource_id] = work.get(alloc.resource_id, 0) + alloc.instances

                    finish[pid] = True
                    changed = True

        # 未完成的进程即为死锁进程
        deadlocked = [pid for pid in process_ids if not finish[pid]]

        return len(deadlocked) > 0, deadlocked


# ============================================================================
# 死锁恢复策略
# ============================================================================

class DeadlockRecoveryStrategy(Enum):
    """死锁恢复策略"""
    TERMINATE_ALL = "终止所有死锁进程"
    TERMINATE_ONE = "逐个终止进程"
    RESOURCE_PREEMPTION = "资源抢占"


class DeadlockRecovery:
    """死锁恢复"""

    def __init__(self, rag: ResourceAllocationGraph):
        self.rag = rag

    def recover(self, deadlocked_processes: List[int],
                strategy: DeadlockRecoveryStrategy = DeadlockRecoveryStrategy.TERMINATE_ONE) -> List[int]:
        """
        恢复死锁

        Args:
            deadlocked_processes: 死锁进程列表
            strategy: 恢复策略

        Returns:
            被终止的进程列表
        """
        if strategy == DeadlockRecoveryStrategy.TERMINATE_ALL:
            return self._terminate_all(deadlocked_processes)
        elif strategy == DeadlockRecoveryStrategy.TERMINATE_ONE:
            return self._terminate_one_by_one(deadlocked_processes)
        elif strategy == DeadlockRecoveryStrategy.RESOURCE_PREEMPTION:
            return self._resource_preemption(deadlocked_processes)
        return []

    def _terminate_all(self, processes: List[int]) -> List[int]:
        """终止所有死锁进程"""
        for pid in processes:
            self._terminate_process(pid)
        return processes

    def _terminate_one_by_one(self, processes: List[int]) -> List[int]:
        """逐个终止进程直到解除死锁"""
        terminated = []
        detector = DeadlockDetector(self.rag)

        for pid in processes:
            self._terminate_process(pid)
            terminated.append(pid)

            # 检查死锁是否解除
            has_deadlock, _ = detector.detect_deadlock()
            if not has_deadlock:
                break

        return terminated

    def _resource_preemption(self, processes: List[int]) -> List[int]:
        """资源抢占（选择代价最小的进程）"""
        # 简化实现：选择持有资源最少的进程
        if not processes:
            return []

        min_resources = float('inf')
        victim = processes[0]

        for pid in processes:
            resource_count = sum(alloc.instances for alloc in self.rag.allocations
                               if alloc.process_id == pid)
            if resource_count < min_resources:
                min_resources = resource_count
                victim = pid

        self._terminate_process(victim)
        return [victim]

    def _terminate_process(self, process_id: int):
        """终止进程并释放其所有资源"""
        # 释放所有已分配的资源
        allocations_to_remove = []
        for alloc in self.rag.allocations:
            if alloc.process_id == process_id:
                resource = self.rag.resources[alloc.resource_id]
                resource.available_instances += alloc.instances
                allocations_to_remove.append(alloc)

        for alloc in allocations_to_remove:
            self.rag.allocations.remove(alloc)

        # 移除所有请求
        requests_to_remove = []
        for req in self.rag.requests:
            if req.process_id == process_id:
                requests_to_remove.append(req)

        for req in requests_to_remove:
            self.rag.requests.remove(req)


# ============================================================================
# 死锁管理器
# ============================================================================

class DeadlockManager:
    """死锁管理器 - 集成检测、避免和恢复"""

    def __init__(self, use_bankers: bool = True):
        """
        初始化死锁管理器

        Args:
            use_bankers: 是否使用银行家算法避免死锁
        """
        self.rag = ResourceAllocationGraph()
        self.use_bankers = use_bankers
        self.bankers: Optional[BankersAlgorithm] = None
        self.detector = DeadlockDetector(self.rag)
        self.recovery = DeadlockRecovery(self.rag)

        # 统计信息
        self.deadlock_detected_count = 0
        self.deadlock_avoided_count = 0
        self.processes_terminated = 0

    def add_resource(self, resource: Resource):
        """添加资源"""
        self.rag.add_resource(resource)

    def initialize_bankers(self, num_processes: int, num_resources: int,
                          available: List[int]):
        """初始化银行家算法"""
        self.bankers = BankersAlgorithm(num_processes, num_resources)
        self.bankers.set_available(available)

    def request_resource(self, process_id: int, resource_id: int,
                        instances: int) -> Tuple[bool, str]:
        """
        请求资源

        Returns:
            (是否成功, 消息)
        """
        # 如果使用银行家算法，先检查安全性
        if self.use_bankers and self.bankers:
            # 构造请求向量
            request = [0] * self.bankers.num_resources
            request[resource_id] = instances

            approved, reason = self.bankers.request_resources(process_id, request)

            if not approved:
                self.deadlock_avoided_count += 1
                return False, f"银行家算法拒绝: {reason}"

        # 尝试分配资源
        success = self.rag.allocate(process_id, resource_id, instances)

        if success:
            return True, "资源分配成功"
        else:
            # 资源不足，加入等待队列
            self.rag.request(process_id, resource_id, instances)
            return False, "资源不足，加入等待队列"

    def release_resource(self, process_id: int, resource_id: int, instances: int) -> bool:
        """释放资源"""
        return self.rag.release(process_id, resource_id, instances)

    def check_deadlock(self) -> Tuple[bool, List[int]]:
        """检查死锁"""
        has_deadlock, deadlocked = self.detector.detect_deadlock()

        if has_deadlock:
            self.deadlock_detected_count += 1

        return has_deadlock, deadlocked

    def recover_deadlock(self, deadlocked_processes: List[int],
                        strategy: DeadlockRecoveryStrategy = DeadlockRecoveryStrategy.TERMINATE_ONE) -> List[int]:
        """恢复死锁"""
        terminated = self.recovery.recover(deadlocked_processes, strategy)
        self.processes_terminated += len(terminated)
        return terminated

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'deadlock_detected': self.deadlock_detected_count,
            'deadlock_avoided': self.deadlock_avoided_count,
            'processes_terminated': self.processes_terminated
        }


# ============================================================================
# 演示程序
# ============================================================================

def demo_bankers_algorithm():
    """演示银行家算法"""
    print("\n" + "=" * 70)
    print("银行家算法演示 - 死锁避免")
    print("=" * 70)

    # 3个进程，3种资源
    bankers = BankersAlgorithm(num_processes=3, num_resources=3)

    # 设置可用资源 [A, B, C]
    bankers.set_available([3, 3, 2])

    # 设置最大需求
    bankers.set_max_demand(0, [7, 5, 3])  # P0
    bankers.set_max_demand(1, [3, 2, 2])  # P1
    bankers.set_max_demand(2, [9, 0, 2])  # P2

    # 设置已分配
    bankers.set_allocation(0, [0, 1, 0])  # P0
    bankers.set_allocation(1, [2, 0, 0])  # P1
    bankers.set_allocation(2, [3, 0, 2])  # P2

    print("\n当前状态:")
    print(f"可用资源: {bankers.available}")
    print(f"已分配矩阵: {bankers.allocation}")
    print(f"需求矩阵: {bankers.need}")

    # 检查安全性
    is_safe, safe_seq = bankers.is_safe_state()
    print(f"\n系统状态: {'安全' if is_safe else '不安全'}")
    if is_safe:
        print(f"安全序列: {safe_seq}")

    # 测试资源请求
    print("\n" + "-" * 70)
    print("P1 请求资源 [1, 0, 2]")
    approved, reason = bankers.request_resources(1, [1, 0, 2])
    print(f"结果: {'批准' if approved else '拒绝'}")
    print(f"原因: {reason}")


def demo_deadlock_detection():
    """演示死锁检测"""
    print("\n" + "=" * 70)
    print("死锁检测演示")
    print("=" * 70)

    # 创建资源分配图
    rag = ResourceAllocationGraph()

    # 添加资源
    rag.add_resource(Resource(0, ResourceType.DISK, "Disk1", 1, 0))
    rag.add_resource(Resource(1, ResourceType.PRINTER, "Printer1", 1, 0))

    # 模拟死锁场景
    # P0持有Disk1，请求Printer1
    rag.allocate(0, 0, 1)
    rag.request(0, 1, 1)

    # P1持有Printer1，请求Disk1
    rag.allocate(1, 1, 1)
    rag.request(1, 0, 1)

    print("\n资源分配情况:")
    print("P0: 持有Disk1, 请求Printer1")
    print("P1: 持有Printer1, 请求Disk1")

    # 检测死锁
    detector = DeadlockDetector(rag)
    has_deadlock, deadlocked = detector.detect_deadlock()

    print(f"\n死锁检测结果: {'存在死锁' if has_deadlock else '无死锁'}")
    if has_deadlock:
        print(f"死锁进程: {deadlocked}")

        # 恢复死锁
        recovery = DeadlockRecovery(rag)
        terminated = recovery.recover(deadlocked, DeadlockRecoveryStrategy.TERMINATE_ONE)
        print(f"\n恢复策略: 逐个终止")
        print(f"被终止的进程: {terminated}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("死锁检测与处理演示")
    print("=" * 70)

    # 演示银行家算法
    demo_bankers_algorithm()

    # 演示死锁检测
    demo_deadlock_detection()


if __name__ == "__main__":
    main()

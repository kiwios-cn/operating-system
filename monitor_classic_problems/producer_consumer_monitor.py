"""
生产者-消费者问题的管程实现

使用管程（Monitor）机制：
- threading.Condition 实现管程
- 自动互斥访问
- 条件变量实现同步

对比信号量实现：
- 更简洁的代码
- 自动的互斥控制
- 更清晰的逻辑
"""

import threading
import time
import random
from typing import List


class ProducerConsumerMonitor:
    """生产者-消费者问题的管程实现"""

    def __init__(self, buffer_size: int = 5):
        """
        初始化管程

        Args:
            buffer_size: 缓冲区大小
        """
        self.buffer_size = buffer_size
        self.buffer: List[int] = []

        # 管程的核心：条件变量（自带互斥锁）
        self.condition = threading.Condition()

        # 统计信息
        self.produced_count = 0
        self.consumed_count = 0

    def produce(self, producer_id: int, item: int):
        """
        生产者操作（管程方法）

        Args:
            producer_id: 生产者编号
            item: 要生产的产品
        """
        with self.condition:  # 进入管程（自动获取锁）
            # 等待条件：缓冲区不满
            while len(self.buffer) >= self.buffer_size:
                print(f"生产者 {producer_id} 等待（缓冲区满）")
                self.condition.wait()  # 释放锁并等待

            # 临界区：生产产品
            self.buffer.append(item)
            self.produced_count += 1
            print(f"生产者 {producer_id} 生产了产品 {item}, 缓冲区: {self.buffer}")

            # 通知消费者（缓冲区有产品了）
            self.condition.notify()
        # 离开管程（自动释放锁）

    def consume(self, consumer_id: int) -> int:
        """
        消费者操作（管程方法）

        Args:
            consumer_id: 消费者编号

        Returns:
            消费的产品
        """
        with self.condition:  # 进入管程
            # 等待条件：缓冲区不空
            while len(self.buffer) == 0:
                print(f"消费者 {consumer_id} 等待（缓冲区空）")
                self.condition.wait()

            # 临界区：消费产品
            item = self.buffer.pop(0)
            self.consumed_count += 1
            print(f"消费者 {consumer_id} 消费了产品 {item}, 缓冲区: {self.buffer}")

            # 通知生产者（缓冲区有空位了）
            self.condition.notify()

            return item
        # 离开管程

    def producer_thread(self, producer_id: int, items_to_produce: int):
        """
        生产者线程

        Args:
            producer_id: 生产者编号
            items_to_produce: 要生产的产品数量
        """
        for i in range(items_to_produce):
            item = random.randint(1, 100)
            time.sleep(random.uniform(0.01, 0.1))  # 模拟生产时间
            self.produce(producer_id, item)

    def consumer_thread(self, consumer_id: int, items_to_consume: int):
        """
        消费者线程

        Args:
            consumer_id: 消费者编号
            items_to_consume: 要消费的产品数量
        """
        for i in range(items_to_consume):
            self.consume(consumer_id)
            time.sleep(random.uniform(0.01, 0.1))  # 模拟消费时间

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.condition:
            return {
                'produced': self.produced_count,
                'consumed': self.consumed_count,
                'buffer_size': len(self.buffer)
            }


def main():
    """主函数：演示管程实现的生产者-消费者问题"""
    print("=" * 60)
    print("生产者-消费者问题演示（管程实现）")
    print("=" * 60)

    # 创建管程
    monitor = ProducerConsumerMonitor(buffer_size=5)

    # 配置参数
    num_producers = 3
    num_consumers = 2
    items_per_producer = 5
    items_per_consumer = 7

    threads = []

    # 创建生产者线程
    for i in range(num_producers):
        t = threading.Thread(
            target=monitor.producer_thread,
            args=(i, items_per_producer),
            name=f"Producer-{i}"
        )
        threads.append(t)

    # 创建消费者线程
    for i in range(num_consumers):
        t = threading.Thread(
            target=monitor.consumer_thread,
            args=(i, items_per_consumer),
            name=f"Consumer-{i}"
        )
        threads.append(t)

    # 启动所有线程
    print(f"\n启动 {num_producers} 个生产者和 {num_consumers} 个消费者...")
    print(f"缓冲区大小: {monitor.buffer_size}")
    print("使用管程机制：自动互斥，条件变量同步\n")

    for t in threads:
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 输出统计信息
    stats = monitor.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总共生产: {stats['produced']} 个产品")
    print(f"总共消费: {stats['consumed']} 个产品")
    print(f"缓冲区剩余: {stats['buffer_size']} 个产品")
    print("=" * 60)

    # 对比说明
    print("\n" + "=" * 60)
    print("管程 vs 信号量对比：")
    print("=" * 60)
    print("信号量实现：")
    print("  - 需要3个信号量：empty, full, mutex")
    print("  - 手动P/V操作，容易出错")
    print("  - PV顺序必须正确")
    print("\n管程实现：")
    print("  - 只需1个条件变量")
    print("  - 自动互斥（with语句）")
    print("  - 逻辑更清晰，代码更简洁")
    print("=" * 60)


if __name__ == "__main__":
    main()

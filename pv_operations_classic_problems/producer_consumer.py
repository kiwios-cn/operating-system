"""
生产者-消费者问题的Python实现

问题描述：
- 多个生产者向有界缓冲区生产产品
- 多个消费者从缓冲区消费产品
- 缓冲区大小有限，需要同步和互斥控制

使用信号量：
- empty: 空槽位数量
- full: 满槽位数量（已有产品数）
- mutex: 互斥访问缓冲区
"""

import threading
import time
import random
from typing import List


class ProducerConsumer:
    """生产者-消费者问题实现"""

    def __init__(self, buffer_size: int = 5):
        """
        初始化生产者-消费者系统

        Args:
            buffer_size: 缓冲区大小
        """
        self.buffer_size = buffer_size
        self.buffer: List[int] = []

        # 信号量定义
        self.empty = threading.Semaphore(buffer_size)  # 空槽位数
        self.full = threading.Semaphore(0)              # 满槽位数
        self.mutex = threading.Semaphore(1)             # 互斥锁

        # 统计信息
        self.produced_count = 0
        self.consumed_count = 0
        self.lock = threading.Lock()  # 保护统计信息

    def producer(self, producer_id: int, items_to_produce: int):
        """
        生产者进程

        Args:
            producer_id: 生产者编号
            items_to_produce: 要生产的产品数量
        """
        for i in range(items_to_produce):
            item = random.randint(1, 100)  # 生产产品
            time.sleep(random.uniform(0.01, 0.1))  # 模拟生产时间

            # P(empty) - 申请空槽位
            self.empty.acquire()

            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：将产品放入缓冲区
            self.buffer.append(item)
            with self.lock:
                self.produced_count += 1
            print(f"生产者 {producer_id} 生产了产品 {item}, 缓冲区: {self.buffer}")

            # V(mutex) - 离开临界区
            self.mutex.release()

            # V(full) - 增加满槽位数
            self.full.release()

    def consumer(self, consumer_id: int, items_to_consume: int):
        """
        消费者进程

        Args:
            consumer_id: 消费者编号
            items_to_consume: 要消费的产品数量
        """
        for i in range(items_to_consume):
            # P(full) - 申请满槽位
            self.full.acquire()

            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：从缓冲区取出产品
            item = self.buffer.pop(0)
            with self.lock:
                self.consumed_count += 1
            print(f"消费者 {consumer_id} 消费了产品 {item}, 缓冲区: {self.buffer}")

            # V(mutex) - 离开临界区
            self.mutex.release()

            # V(empty) - 增加空槽位数
            self.empty.release()

            time.sleep(random.uniform(0.01, 0.1))  # 模拟消费时间

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'produced': self.produced_count,
                'consumed': self.consumed_count,
                'buffer_size': len(self.buffer)
            }


def main():
    """主函数：演示生产者-消费者问题"""
    print("=" * 60)
    print("生产者-消费者问题演示")
    print("=" * 60)

    # 创建生产者-消费者系统
    pc = ProducerConsumer(buffer_size=5)

    # 配置参数
    num_producers = 3
    num_consumers = 2
    items_per_producer = 5
    items_per_consumer = 7  # 总共生产15个，消费14个

    threads = []

    # 创建生产者线程
    for i in range(num_producers):
        t = threading.Thread(
            target=pc.producer,
            args=(i, items_per_producer),
            name=f"Producer-{i}"
        )
        threads.append(t)

    # 创建消费者线程
    for i in range(num_consumers):
        t = threading.Thread(
            target=pc.consumer,
            args=(i, items_per_consumer),
            name=f"Consumer-{i}"
        )
        threads.append(t)

    # 启动所有线程
    print(f"\n启动 {num_producers} 个生产者和 {num_consumers} 个消费者...")
    print(f"缓冲区大小: {pc.buffer_size}\n")

    for t in threads:
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 输出统计信息
    stats = pc.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总共生产: {stats['produced']} 个产品")
    print(f"总共消费: {stats['consumed']} 个产品")
    print(f"缓冲区剩余: {stats['buffer_size']} 个产品")
    print("=" * 60)


if __name__ == "__main__":
    main()

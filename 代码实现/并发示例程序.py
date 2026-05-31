#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作系统并发性示例程序
演示经典的并发问题及其解决方案
"""

import threading
import time
import random
from queue import Queue

# ============================================================================
# 示例1：生产者-消费者问题（单缓冲区）
# ============================================================================

class SingleBufferProducerConsumer:
    """单缓冲区生产者-消费者问题"""

    def __init__(self):
        self.buffer = None  # 单个缓冲区
        self.mutex = threading.Semaphore(1)   # 互斥信号量，初值1
        self.empty = threading.Semaphore(1)   # 空缓冲区信号量，初值1
        self.full = threading.Semaphore(0)    # 满缓冲区信号量，初值0
        self.produced_count = 0
        self.consumed_count = 0

    def producer(self, producer_id):
        """生产者进程"""
        for i in range(3):
            time.sleep(random.uniform(0.1, 0.5))  # 模拟生产时间
            item = f"产品{producer_id}-{i}"

            # P(empty) - 等待空缓冲区
            self.empty.acquire()
            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：放入产品
            self.buffer = item
            self.produced_count += 1
            print(f"[生产者{producer_id}] 生产了 {item}，总生产数：{self.produced_count}")

            # V(mutex) - 离开临界区
            self.mutex.release()
            # V(full) - 增加满缓冲区数
            self.full.release()

    def consumer(self, consumer_id):
        """消费者进程"""
        for i in range(3):
            # P(full) - 等待满缓冲区
            self.full.acquire()
            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：取出产品
            item = self.buffer
            self.buffer = None
            self.consumed_count += 1
            print(f"[消费者{consumer_id}] 消费了 {item}，总消费数：{self.consumed_count}")

            # V(mutex) - 离开临界区
            self.mutex.release()
            # V(empty) - 增加空缓冲区数
            self.empty.release()

            time.sleep(random.uniform(0.1, 0.5))  # 模拟消费时间

    def run(self):
        """运行示例"""
        print("\n" + "="*60)
        print("示例1：生产者-消费者问题（单缓冲区）")
        print("="*60)

        # 创建1个生产者和1个消费者
        producer_thread = threading.Thread(target=self.producer, args=(1,))
        consumer_thread = threading.Thread(target=self.consumer, args=(1,))

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        print(f"\n✓ 单缓冲区示例完成：生产{self.produced_count}个，消费{self.consumed_count}个")


# ============================================================================
# 示例2：生产者-消费者问题（多缓冲区）
# ============================================================================

class MultiBufferProducerConsumer:
    """多缓冲区生产者-消费者问题"""

    def __init__(self, buffer_size=5):
        self.buffer = []  # 缓冲区列表
        self.buffer_size = buffer_size
        self.mutex = threading.Semaphore(1)           # 互斥信号量
        self.empty = threading.Semaphore(buffer_size) # 空缓冲区数，初值n
        self.full = threading.Semaphore(0)            # 满缓冲区数，初值0
        self.produced_count = 0
        self.consumed_count = 0

    def producer(self, producer_id):
        """生产者进程"""
        for i in range(5):
            time.sleep(random.uniform(0.05, 0.2))
            item = f"P{producer_id}-{i}"

            # P(empty) - 等待空缓冲区
            self.empty.acquire()
            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：放入产品
            self.buffer.append(item)
            self.produced_count += 1
            print(f"[生产者{producer_id}] 生产 {item}，缓冲区：{len(self.buffer)}/{self.buffer_size}")

            # V(mutex) - 离开临界区
            self.mutex.release()
            # V(full) - 增加满缓冲区数
            self.full.release()

    def consumer(self, consumer_id):
        """消费者进程"""
        for i in range(5):
            # P(full) - 等待满缓冲区
            self.full.acquire()
            # P(mutex) - 进入临界区
            self.mutex.acquire()

            # 临界区：取出产品
            item = self.buffer.pop(0)
            self.consumed_count += 1
            print(f"[消费者{consumer_id}] 消费 {item}，缓冲区：{len(self.buffer)}/{self.buffer_size}")

            # V(mutex) - 离开临界区
            self.mutex.release()
            # V(empty) - 增加空缓冲区数
            self.empty.release()

            time.sleep(random.uniform(0.05, 0.2))

    def run(self):
        """运行示例"""
        print("\n" + "="*60)
        print("示例2：生产者-消费者问题（多缓冲区，缓冲区大小=5）")
        print("="*60)

        # 创建2个生产者和2个消费者
        threads = []
        for i in range(2):
            threads.append(threading.Thread(target=self.producer, args=(i+1,)))
            threads.append(threading.Thread(target=self.consumer, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        print(f"\n✓ 多缓冲区示例完成：生产{self.produced_count}个，消费{self.consumed_count}个")


# ============================================================================
# 示例3：读者-写者问题（读者优先）
# ============================================================================

class ReaderWriterProblem:
    """读者-写者问题（读者优先策略）"""

    def __init__(self):
        self.data = "初始数据"
        self.readcount = 0  # 读者计数器
        self.wmutex = threading.Semaphore(1)  # 写互斥信号量
        self.rmutex = threading.Semaphore(1)  # 读者计数器互斥信号量
        self.read_count = 0
        self.write_count = 0

    def reader(self, reader_id):
        """读者进程"""
        for i in range(3):
            time.sleep(random.uniform(0.1, 0.3))

            # P(rmutex) - 保护readcount
            self.rmutex.acquire()
            self.readcount += 1
            if self.readcount == 1:
                # 第一个读者锁定写操作
                self.wmutex.acquire()
            self.rmutex.release()

            # 读数据（临界区）
            self.read_count += 1
            print(f"[读者{reader_id}] 正在读取数据：'{self.data}'，当前读者数：{self.readcount}")
            time.sleep(random.uniform(0.05, 0.15))  # 模拟读取时间

            # P(rmutex) - 保护readcount
            self.rmutex.acquire()
            self.readcount -= 1
            if self.readcount == 0:
                # 最后一个读者释放写锁
                self.wmutex.release()
            self.rmutex.release()

    def writer(self, writer_id):
        """写者进程"""
        for i in range(2):
            time.sleep(random.uniform(0.2, 0.4))

            # P(wmutex) - 独占访问
            self.wmutex.acquire()

            # 写数据（临界区）
            new_data = f"写者{writer_id}的数据-{i}"
            self.data = new_data
            self.write_count += 1
            print(f"[写者{writer_id}] 正在写入数据：'{new_data}'")
            time.sleep(random.uniform(0.1, 0.2))  # 模拟写入时间

            # V(wmutex) - 释放独占
            self.wmutex.release()

    def run(self):
        """运行示例"""
        print("\n" + "="*60)
        print("示例3：读者-写者问题（读者优先策略）")
        print("="*60)

        # 创建3个读者和2个写者
        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=self.reader, args=(i+1,)))
        for i in range(2):
            threads.append(threading.Thread(target=self.writer, args=(i+1,)))

        # 随机启动顺序
        random.shuffle(threads)
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        print(f"\n✓ 读者-写者示例完成：读取{self.read_count}次，写入{self.write_count}次")
        print(f"最终数据：'{self.data}'")


# ============================================================================
# 示例4：哲学家就餐问题（避免死锁）
# ============================================================================

class DiningPhilosophers:
    """哲学家就餐问题（使用资源编号法避免死锁）"""

    def __init__(self, num_philosophers=5):
        self.num_philosophers = num_philosophers
        # 每根筷子用一个信号量表示
        self.chopsticks = [threading.Semaphore(1) for _ in range(num_philosophers)]
        self.eat_count = [0] * num_philosophers

    def philosopher(self, philosopher_id):
        """哲学家进程"""
        for i in range(3):
            # 思考
            print(f"[哲学家{philosopher_id}] 正在思考...")
            time.sleep(random.uniform(0.1, 0.3))

            # 拿筷子（资源编号法：先拿编号小的，再拿编号大的）
            left = philosopher_id
            right = (philosopher_id + 1) % self.num_philosophers

            # 关键：按编号顺序获取资源，避免循环等待
            first = min(left, right)
            second = max(left, right)

            print(f"[哲学家{philosopher_id}] 尝试拿起筷子{first}和{second}...")
            self.chopsticks[first].acquire()
            self.chopsticks[second].acquire()

            # 进餐
            self.eat_count[philosopher_id] += 1
            print(f"[哲学家{philosopher_id}] 正在进餐（第{self.eat_count[philosopher_id]}次）")
            time.sleep(random.uniform(0.1, 0.2))

            # 放下筷子
            self.chopsticks[first].release()
            self.chopsticks[second].release()
            print(f"[哲学家{philosopher_id}] 放下筷子{first}和{second}")

    def run(self):
        """运行示例"""
        print("\n" + "="*60)
        print("示例4：哲学家就餐问题（使用资源编号法避免死锁）")
        print("="*60)

        # 创建5个哲学家线程
        threads = []
        for i in range(self.num_philosophers):
            threads.append(threading.Thread(target=self.philosopher, args=(i,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        print(f"\n✓ 哲学家就餐示例完成")
        for i in range(self.num_philosophers):
            print(f"  哲学家{i}进餐{self.eat_count[i]}次")


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数：运行所有并发示例"""
    print("\n" + "="*60)
    print("操作系统并发性示例程序")
    print("演示经典并发问题及其解决方案")
    print("="*60)

    # 示例1：单缓冲区生产者-消费者
    example1 = SingleBufferProducerConsumer()
    example1.run()

    time.sleep(0.5)

    # 示例2：多缓冲区生产者-消费者
    example2 = MultiBufferProducerConsumer(buffer_size=5)
    example2.run()

    time.sleep(0.5)

    # 示例3：读者-写者问题
    example3 = ReaderWriterProblem()
    example3.run()

    time.sleep(0.5)

    # 示例4：哲学家就餐问题
    example4 = DiningPhilosophers(num_philosophers=5)
    example4.run()

    print("\n" + "="*60)
    print("✓ 所有并发示例运行完成！")
    print("="*60)
    print("\n关键要点：")
    print("1. 生产者-消费者：P操作顺序（先资源后互斥），V操作顺序（先互斥后资源）")
    print("2. 读者-写者：多个读者可同时读，写者独占访问")
    print("3. 哲学家就餐：使用资源编号法避免循环等待，防止死锁")
    print("4. 信号量物理意义：S>0表示可用资源数，S<0表示等待进程数")


if __name__ == "__main__":
    main()

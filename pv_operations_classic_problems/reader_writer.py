"""
读者-写者问题的Python实现

问题描述：
- 多个读者可以同时读取共享数据
- 写者必须独占访问（写时不能有其他读者或写者）
- 实现了读者优先和写者优先两种策略

使用信号量：
- write: 写互斥信号量
- mutex: 保护读者计数器
- read: 读互斥信号量（写者优先时使用）
"""

import threading
import time
import random
from typing import List


class ReaderWriterReadFirst:
    """读者-写者问题实现（读者优先策略）"""

    def __init__(self):
        """初始化读者-写者系统（读者优先）"""
        self.shared_data = 0  # 共享数据
        self.reader_count = 0  # 当前读者数量

        # 信号量定义
        self.write = threading.Semaphore(1)  # 写互斥
        self.mutex = threading.Semaphore(1)  # 保护reader_count

        # 统计信息
        self.read_operations = 0
        self.write_operations = 0
        self.lock = threading.Lock()

    def reader(self, reader_id: int, read_times: int):
        """
        读者进程

        Args:
            reader_id: 读者编号
            read_times: 读取次数
        """
        for i in range(read_times):
            time.sleep(random.uniform(0.01, 0.05))

            # P(mutex) - 保护reader_count
            self.mutex.acquire()
            self.reader_count += 1
            if self.reader_count == 1:  # 第一个读者
                self.write.acquire()  # P(write) - 阻止写者
            self.mutex.release()  # V(mutex)

            # 临界区：读取数据
            data = self.shared_data
            with self.lock:
                self.read_operations += 1
            print(f"读者 {reader_id} 读取数据: {data}, 当前读者数: {self.reader_count}")

            time.sleep(random.uniform(0.01, 0.03))  # 模拟读取时间

            # P(mutex)
            self.mutex.acquire()
            self.reader_count -= 1
            if self.reader_count == 0:  # 最后一个读者
                self.write.release()  # V(write) - 允许写者
            self.mutex.release()  # V(mutex)

    def writer(self, writer_id: int, write_times: int):
        """
        写者进程

        Args:
            writer_id: 写者编号
            write_times: 写入次数
        """
        for i in range(write_times):
            time.sleep(random.uniform(0.05, 0.1))

            # P(write) - 申请写权限
            self.write.acquire()

            # 临界区：写入数据
            self.shared_data += 1
            with self.lock:
                self.write_operations += 1
            print(f"写者 {writer_id} 写入数据: {self.shared_data}")

            time.sleep(random.uniform(0.02, 0.05))  # 模拟写入时间

            # V(write) - 释放写权限
            self.write.release()

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'read_operations': self.read_operations,
                'write_operations': self.write_operations,
                'final_data': self.shared_data
            }


class ReaderWriterWriteFirst:
    """读者-写者问题实现（写者优先策略）"""

    def __init__(self):
        """初始化读者-写者系统（写者优先）"""
        self.shared_data = 0
        self.reader_count = 0
        self.writer_count = 0

        # 信号量定义
        self.read = threading.Semaphore(1)   # 读互斥
        self.write = threading.Semaphore(1)  # 写互斥
        self.mutex1 = threading.Semaphore(1) # 保护reader_count
        self.mutex2 = threading.Semaphore(1) # 保护writer_count

        # 统计信息
        self.read_operations = 0
        self.write_operations = 0
        self.lock = threading.Lock()

    def reader(self, reader_id: int, read_times: int):
        """
        读者进程（写者优先）

        Args:
            reader_id: 读者编号
            read_times: 读取次数
        """
        for i in range(read_times):
            time.sleep(random.uniform(0.01, 0.05))

            # P(read) - 如果有写者等待，阻塞
            self.read.acquire()

            # P(mutex1)
            self.mutex1.acquire()
            self.reader_count += 1
            if self.reader_count == 1:
                self.write.acquire()  # P(write)
            self.mutex1.release()  # V(mutex1)

            self.read.release()  # V(read)

            # 临界区：读取数据
            data = self.shared_data
            with self.lock:
                self.read_operations += 1
            print(f"读者 {reader_id} 读取数据: {data}, 当前读者数: {self.reader_count}")

            time.sleep(random.uniform(0.01, 0.03))

            # P(mutex1)
            self.mutex1.acquire()
            self.reader_count -= 1
            if self.reader_count == 0:
                self.write.release()  # V(write)
            self.mutex1.release()  # V(mutex1)

    def writer(self, writer_id: int, write_times: int):
        """
        写者进程（写者优先）

        Args:
            writer_id: 写者编号
            write_times: 写入次数
        """
        for i in range(write_times):
            time.sleep(random.uniform(0.05, 0.1))

            # P(mutex2)
            self.mutex2.acquire()
            self.writer_count += 1
            if self.writer_count == 1:
                self.read.acquire()  # P(read) - 阻止新读者
            self.mutex2.release()  # V(mutex2)

            # P(write)
            self.write.acquire()

            # 临界区：写入数据
            self.shared_data += 1
            with self.lock:
                self.write_operations += 1
            print(f"写者 {writer_id} 写入数据: {self.shared_data}, 等待写者数: {self.writer_count}")

            time.sleep(random.uniform(0.02, 0.05))

            # V(write)
            self.write.release()

            # P(mutex2)
            self.mutex2.acquire()
            self.writer_count -= 1
            if self.writer_count == 0:
                self.read.release()  # V(read) - 允许读者
            self.mutex2.release()  # V(mutex2)

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'read_operations': self.read_operations,
                'write_operations': self.write_operations,
                'final_data': self.shared_data
            }


def demo_read_first():
    """演示读者优先策略"""
    print("=" * 60)
    print("读者-写者问题演示（读者优先策略）")
    print("=" * 60)

    rw = ReaderWriterReadFirst()

    num_readers = 4
    num_writers = 2
    reads_per_reader = 3
    writes_per_writer = 3

    threads = []

    # 创建读者线程
    for i in range(num_readers):
        t = threading.Thread(
            target=rw.reader,
            args=(i, reads_per_reader),
            name=f"Reader-{i}"
        )
        threads.append(t)

    # 创建写者线程
    for i in range(num_writers):
        t = threading.Thread(
            target=rw.writer,
            args=(i, writes_per_writer),
            name=f"Writer-{i}"
        )
        threads.append(t)

    print(f"\n启动 {num_readers} 个读者和 {num_writers} 个写者...")
    print("策略: 读者优先（可能导致写者饥饿）\n")

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = rw.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总读取次数: {stats['read_operations']}")
    print(f"总写入次数: {stats['write_operations']}")
    print(f"最终数据值: {stats['final_data']}")
    print("=" * 60)


def demo_write_first():
    """演示写者优先策略"""
    print("\n\n" + "=" * 60)
    print("读者-写者问题演示（写者优先策略）")
    print("=" * 60)

    rw = ReaderWriterWriteFirst()

    num_readers = 4
    num_writers = 2
    reads_per_reader = 3
    writes_per_writer = 3

    threads = []

    # 创建读者线程
    for i in range(num_readers):
        t = threading.Thread(
            target=rw.reader,
            args=(i, reads_per_reader),
            name=f"Reader-{i}"
        )
        threads.append(t)

    # 创建写者线程
    for i in range(num_writers):
        t = threading.Thread(
            target=rw.writer,
            args=(i, writes_per_writer),
            name=f"Writer-{i}"
        )
        threads.append(t)

    print(f"\n启动 {num_readers} 个读者和 {num_writers} 个写者...")
    print("策略: 写者优先（可能导致读者饥饿）\n")

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = rw.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总读取次数: {stats['read_operations']}")
    print(f"总写入次数: {stats['write_operations']}")
    print(f"最终数据值: {stats['final_data']}")
    print("=" * 60)


def main():
    """主函数：演示两种策略"""
    demo_read_first()
    time.sleep(1)
    demo_write_first()


if __name__ == "__main__":
    main()

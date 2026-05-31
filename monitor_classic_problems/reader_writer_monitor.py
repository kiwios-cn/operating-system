"""
读者-写者问题的管程实现

使用管程（Monitor）机制：
- threading.Condition 实现管程
- 自动互斥访问
- 条件变量实现读写同步

实现了两种策略：
1. 读者优先
2. 写者优先
"""

import threading
import time
import random


class ReaderWriterMonitorReadFirst:
    """读者-写者问题的管程实现（读者优先策略）"""

    def __init__(self):
        """初始化管程"""
        self.shared_data = 0
        self.readers = 0  # 当前读者数量
        self.writers = 0  # 当前写者数量（0或1）

        # 管程的条件变量
        self.condition = threading.Condition()

        # 统计信息
        self.read_operations = 0
        self.write_operations = 0

    def start_read(self, reader_id: int):
        """
        开始读操作

        Args:
            reader_id: 读者编号
        """
        with self.condition:  # 进入管程
            # 等待条件：没有写者
            while self.writers > 0:
                self.condition.wait()

            self.readers += 1
            print(f"读者 {reader_id} 开始读取，当前读者数: {self.readers}")

    def end_read(self, reader_id: int, data: int):
        """
        结束读操作

        Args:
            reader_id: 读者编号
            data: 读取的数据
        """
        with self.condition:
            self.readers -= 1
            self.read_operations += 1
            print(f"读者 {reader_id} 读取数据: {data}，当前读者数: {self.readers}")

            # 如果是最后一个读者，通知写者
            if self.readers == 0:
                self.condition.notify_all()

    def start_write(self, writer_id: int):
        """
        开始写操作

        Args:
            writer_id: 写者编号
        """
        with self.condition:
            # 等待条件：没有读者也没有写者
            while self.readers > 0 or self.writers > 0:
                self.condition.wait()

            self.writers = 1
            print(f"写者 {writer_id} 开始写入")

    def end_write(self, writer_id: int):
        """
        结束写操作

        Args:
            writer_id: 写者编号
        """
        with self.condition:
            self.shared_data += 1
            self.write_operations += 1
            print(f"写者 {writer_id} 写入数据: {self.shared_data}")

            self.writers = 0

            # 通知所有等待的读者和写者
            self.condition.notify_all()

    def reader_thread(self, reader_id: int, read_times: int):
        """读者线程"""
        for i in range(read_times):
            time.sleep(random.uniform(0.01, 0.05))

            self.start_read(reader_id)

            # 读取数据（在管程外，允许多个读者并发）
            data = self.shared_data
            time.sleep(random.uniform(0.01, 0.03))

            self.end_read(reader_id, data)

    def writer_thread(self, writer_id: int, write_times: int):
        """写者线程"""
        for i in range(write_times):
            time.sleep(random.uniform(0.05, 0.1))

            self.start_write(writer_id)

            # 写入数据（在管程内，独占访问）
            time.sleep(random.uniform(0.02, 0.05))

            self.end_write(writer_id)

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.condition:
            return {
                'read_operations': self.read_operations,
                'write_operations': self.write_operations,
                'final_data': self.shared_data
            }


class ReaderWriterMonitorWriteFirst:
    """读者-写者问题的管程实现（写者优先策略）"""

    def __init__(self):
        """初始化管程"""
        self.shared_data = 0
        self.readers = 0
        self.writers = 0
        self.waiting_writers = 0  # 等待的写者数量

        self.condition = threading.Condition()

        # 统计信息
        self.read_operations = 0
        self.write_operations = 0

    def start_read(self, reader_id: int):
        """开始读操作（写者优先）"""
        with self.condition:
            # 等待条件：没有写者且没有等待的写者
            while self.writers > 0 or self.waiting_writers > 0:
                self.condition.wait()

            self.readers += 1
            print(f"读者 {reader_id} 开始读取，当前读者数: {self.readers}")

    def end_read(self, reader_id: int, data: int):
        """结束读操作"""
        with self.condition:
            self.readers -= 1
            self.read_operations += 1
            print(f"读者 {reader_id} 读取数据: {data}，当前读者数: {self.readers}")

            if self.readers == 0:
                self.condition.notify_all()

    def start_write(self, writer_id: int):
        """开始写操作（写者优先）"""
        with self.condition:
            self.waiting_writers += 1

            # 等待条件：没有读者也没有写者
            while self.readers > 0 or self.writers > 0:
                self.condition.wait()

            self.waiting_writers -= 1
            self.writers = 1
            print(f"写者 {writer_id} 开始写入，等待写者数: {self.waiting_writers}")

    def end_write(self, writer_id: int):
        """结束写操作"""
        with self.condition:
            self.shared_data += 1
            self.write_operations += 1
            print(f"写者 {writer_id} 写入数据: {self.shared_data}")

            self.writers = 0
            self.condition.notify_all()

    def reader_thread(self, reader_id: int, read_times: int):
        """读者线程"""
        for i in range(read_times):
            time.sleep(random.uniform(0.01, 0.05))
            self.start_read(reader_id)
            data = self.shared_data
            time.sleep(random.uniform(0.01, 0.03))
            self.end_read(reader_id, data)

    def writer_thread(self, writer_id: int, write_times: int):
        """写者线程"""
        for i in range(write_times):
            time.sleep(random.uniform(0.05, 0.1))
            self.start_write(writer_id)
            time.sleep(random.uniform(0.02, 0.05))
            self.end_write(writer_id)

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.condition:
            return {
                'read_operations': self.read_operations,
                'write_operations': self.write_operations,
                'final_data': self.shared_data
            }


def demo_read_first():
    """演示读者优先策略"""
    print("=" * 60)
    print("读者-写者问题演示（管程实现 - 读者优先）")
    print("=" * 60)

    monitor = ReaderWriterMonitorReadFirst()

    num_readers = 4
    num_writers = 2
    reads_per_reader = 3
    writes_per_writer = 3

    threads = []

    for i in range(num_readers):
        t = threading.Thread(
            target=monitor.reader_thread,
            args=(i, reads_per_reader),
            name=f"Reader-{i}"
        )
        threads.append(t)

    for i in range(num_writers):
        t = threading.Thread(
            target=monitor.writer_thread,
            args=(i, writes_per_writer),
            name=f"Writer-{i}"
        )
        threads.append(t)

    print(f"\n启动 {num_readers} 个读者和 {num_writers} 个写者...")
    print("策略: 读者优先（可能导致写者饥饿）")
    print("使用管程：自动互斥，条件变量同步\n")

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = monitor.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总读取次数: {stats['read_operations']}")
    print(f"总写入次数: {stats['write_operations']}")
    print(f"最终数据值: {stats['final_data']}")
    print("=" * 60)


def demo_write_first():
    """演示写者优先策略"""
    print("\n\n" + "=" * 60)
    print("读者-写者问题演示（管程实现 - 写者优先）")
    print("=" * 60)

    monitor = ReaderWriterMonitorWriteFirst()

    num_readers = 4
    num_writers = 2
    reads_per_reader = 3
    writes_per_writer = 3

    threads = []

    for i in range(num_readers):
        t = threading.Thread(
            target=monitor.reader_thread,
            args=(i, reads_per_reader),
            name=f"Reader-{i}"
        )
        threads.append(t)

    for i in range(num_writers):
        t = threading.Thread(
            target=monitor.writer_thread,
            args=(i, writes_per_writer),
            name=f"Writer-{i}"
        )
        threads.append(t)

    print(f"\n启动 {num_readers} 个读者和 {num_writers} 个写者...")
    print("策略: 写者优先（可能导致读者饥饿）")
    print("使用管程：自动互斥，条件变量同步\n")

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = monitor.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    print(f"总读取次数: {stats['read_operations']}")
    print(f"总写入次数: {stats['write_operations']}")
    print(f"最终数据值: {stats['final_data']}")
    print("=" * 60)


def main():
    """主函数"""
    demo_read_first()
    time.sleep(1)
    demo_write_first()

    # 对比说明
    print("\n\n" + "=" * 60)
    print("管程 vs 信号量对比：")
    print("=" * 60)
    print("信号量实现：")
    print("  - 读者优先：需要2个信号量 + 1个计数器")
    print("  - 写者优先：需要4个信号量 + 2个计数器")
    print("  - 手动管理锁，逻辑复杂")
    print("\n管程实现：")
    print("  - 只需1个条件变量 + 计数器")
    print("  - 自动互斥，逻辑清晰")
    print("  - 代码更简洁易懂")
    print("=" * 60)


if __name__ == "__main__":
    main()

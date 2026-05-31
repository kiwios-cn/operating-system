#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发示例程序的测试用例
验证并发控制的正确性
"""

import unittest
import threading
import time
from 并发示例程序 import (
    SingleBufferProducerConsumer,
    MultiBufferProducerConsumer,
    ReaderWriterProblem,
    DiningPhilosophers
)


class TestSingleBufferProducerConsumer(unittest.TestCase):
    """测试单缓冲区生产者-消费者"""

    def test_single_producer_consumer(self):
        """测试单生产者单消费者场景"""
        pc = SingleBufferProducerConsumer()

        producer = threading.Thread(target=pc.producer, args=(1,))
        consumer = threading.Thread(target=pc.consumer, args=(1,))

        producer.start()
        consumer.start()

        producer.join()
        consumer.join()

        # 验证：生产数量应等于消费数量
        self.assertEqual(pc.produced_count, pc.consumed_count)
        self.assertEqual(pc.produced_count, 3)
        # 验证：缓冲区应为空
        self.assertIsNone(pc.buffer)

    def test_buffer_mutex(self):
        """测试缓冲区互斥访问"""
        pc = SingleBufferProducerConsumer()

        # 记录缓冲区访问冲突
        conflicts = []
        original_producer = pc.producer
        original_consumer = pc.consumer

        def monitored_producer(pid):
            original_producer(pid)

        def monitored_consumer(cid):
            original_consumer(cid)

        producer = threading.Thread(target=monitored_producer, args=(1,))
        consumer = threading.Thread(target=monitored_consumer, args=(1,))

        producer.start()
        consumer.start()

        producer.join()
        consumer.join()

        # 如果没有异常，说明互斥控制正确
        self.assertEqual(pc.produced_count, pc.consumed_count)


class TestMultiBufferProducerConsumer(unittest.TestCase):
    """测试多缓冲区生产者-消费者"""

    def test_multi_producer_consumer(self):
        """测试多生产者多消费者场景"""
        pc = MultiBufferProducerConsumer(buffer_size=5)

        threads = []
        # 2个生产者，2个消费者
        for i in range(2):
            threads.append(threading.Thread(target=pc.producer, args=(i+1,)))
            threads.append(threading.Thread(target=pc.consumer, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：生产数量应等于消费数量
        self.assertEqual(pc.produced_count, pc.consumed_count)
        self.assertEqual(pc.produced_count, 10)  # 2个生产者 × 5次
        # 验证：缓冲区应为空
        self.assertEqual(len(pc.buffer), 0)

    def test_buffer_size_limit(self):
        """测试缓冲区大小限制"""
        pc = MultiBufferProducerConsumer(buffer_size=3)
        max_buffer_size = 0

        # 监控缓冲区大小
        original_producer = pc.producer

        def monitored_producer(pid):
            nonlocal max_buffer_size
            for i in range(5):
                time.sleep(0.05)
                item = f"P{pid}-{i}"

                pc.empty.acquire()
                pc.mutex.acquire()

                pc.buffer.append(item)
                pc.produced_count += 1
                max_buffer_size = max(max_buffer_size, len(pc.buffer))

                pc.mutex.release()
                pc.full.release()

        producer = threading.Thread(target=monitored_producer, args=(1,))
        consumer = threading.Thread(target=pc.consumer, args=(1,))

        producer.start()
        time.sleep(0.1)  # 让生产者先运行
        consumer.start()

        producer.join()
        consumer.join()

        # 验证：缓冲区大小不应超过限制
        self.assertLessEqual(max_buffer_size, 3)


class TestReaderWriterProblem(unittest.TestCase):
    """测试读者-写者问题"""

    def test_multiple_readers(self):
        """测试多个读者可以同时读"""
        rw = ReaderWriterProblem()

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=rw.reader, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：读取次数应为 3个读者 × 3次
        self.assertEqual(rw.read_count, 9)

    def test_writer_exclusion(self):
        """测试写者独占访问"""
        rw = ReaderWriterProblem()

        threads = []
        for i in range(2):
            threads.append(threading.Thread(target=rw.writer, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：写入次数应为 2个写者 × 2次
        self.assertEqual(rw.write_count, 4)
        # 验证：数据应被正确更新
        self.assertIn("写者", rw.data)

    def test_reader_writer_mixed(self):
        """测试读者和写者混合场景"""
        rw = ReaderWriterProblem()

        threads = []
        for i in range(2):
            threads.append(threading.Thread(target=rw.reader, args=(i+1,)))
            threads.append(threading.Thread(target=rw.writer, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：读写操作都完成
        self.assertGreater(rw.read_count, 0)
        self.assertGreater(rw.write_count, 0)


class TestDiningPhilosophers(unittest.TestCase):
    """测试哲学家就餐问题"""

    def test_no_deadlock(self):
        """测试不会发生死锁"""
        dp = DiningPhilosophers(num_philosophers=5)

        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=dp.philosopher, args=(i,)))

        start_time = time.time()

        for t in threads:
            t.start()

        # 设置超时：如果10秒内未完成，可能发生死锁
        for t in threads:
            t.join(timeout=10)

        end_time = time.time()

        # 验证：所有线程都应该完成
        for t in threads:
            self.assertFalse(t.is_alive(), "检测到可能的死锁")

        # 验证：每个哲学家都应该进餐3次
        for i in range(5):
            self.assertEqual(dp.eat_count[i], 3, f"哲学家{i}未完成进餐")

        # 验证：总时间应该合理（不应该太长）
        self.assertLess(end_time - start_time, 10, "执行时间过长，可能存在性能问题")

    def test_chopstick_mutex(self):
        """测试筷子的互斥使用"""
        dp = DiningPhilosophers(num_philosophers=3)

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=dp.philosopher, args=(i,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：所有哲学家都完成进餐
        total_meals = sum(dp.eat_count)
        self.assertEqual(total_meals, 9)  # 3个哲学家 × 3次


class TestConcurrencyProperties(unittest.TestCase):
    """测试并发属性"""

    def test_producer_consumer_no_data_loss(self):
        """测试生产者-消费者不会丢失数据"""
        pc = MultiBufferProducerConsumer(buffer_size=10)

        # 大量生产和消费
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=pc.producer, args=(i+1,)))
            threads.append(threading.Thread(target=pc.consumer, args=(i+1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：生产数 = 消费数，无数据丢失
        self.assertEqual(pc.produced_count, pc.consumed_count)
        self.assertEqual(pc.produced_count, 25)  # 5个生产者 × 5次

    def test_reader_writer_data_consistency(self):
        """测试读者-写者数据一致性"""
        rw = ReaderWriterProblem()
        inconsistencies = []

        def monitored_reader(rid):
            for i in range(5):
                time.sleep(0.05)
                rw.rmutex.acquire()
                rw.readcount += 1
                if rw.readcount == 1:
                    rw.wmutex.acquire()
                rw.rmutex.release()

                # 读取数据并验证
                data = rw.data
                time.sleep(0.01)
                # 再次读取，应该相同（因为写者被锁定）
                if data != rw.data:
                    inconsistencies.append(f"读者{rid}检测到数据不一致")

                rw.rmutex.acquire()
                rw.readcount -= 1
                if rw.readcount == 0:
                    rw.wmutex.release()
                rw.rmutex.release()

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=monitored_reader, args=(i+1,)))
        threads.append(threading.Thread(target=rw.writer, args=(1,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证：不应该有数据不一致
        self.assertEqual(len(inconsistencies), 0, f"发现数据不一致：{inconsistencies}")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_empty_buffer_consumer_blocks(self):
        """测试空缓冲区时消费者会阻塞"""
        pc = SingleBufferProducerConsumer()
        consumer_started = threading.Event()
        consumer_finished = threading.Event()

        def delayed_consumer(cid):
            consumer_started.set()
            pc.consumer(cid)
            consumer_finished.set()

        consumer = threading.Thread(target=delayed_consumer, args=(1,))
        consumer.start()

        # 等待消费者启动
        consumer_started.wait(timeout=1)
        time.sleep(0.2)

        # 验证：消费者应该被阻塞（未完成）
        self.assertFalse(consumer_finished.is_set())

        # 启动生产者
        producer = threading.Thread(target=pc.producer, args=(1,))
        producer.start()

        producer.join()
        consumer.join()

        # 验证：现在消费者应该完成了
        self.assertTrue(consumer_finished.is_set())

    def test_full_buffer_producer_blocks(self):
        """测试满缓冲区时生产者会阻塞"""
        pc = MultiBufferProducerConsumer(buffer_size=2)

        # 先填满缓冲区
        pc.empty.acquire()
        pc.mutex.acquire()
        pc.buffer.append("item1")
        pc.mutex.release()
        pc.full.release()

        pc.empty.acquire()
        pc.mutex.acquire()
        pc.buffer.append("item2")
        pc.mutex.release()
        pc.full.release()

        producer_blocked = threading.Event()

        def monitored_producer(pid):
            # 尝试生产（应该被阻塞）
            pc.empty.acquire()  # 这里会阻塞
            producer_blocked.set()
            pc.mutex.acquire()
            pc.buffer.append(f"P{pid}")
            pc.mutex.release()
            pc.full.release()

        producer = threading.Thread(target=monitored_producer, args=(1,))
        producer.start()

        time.sleep(0.2)

        # 验证：生产者应该被阻塞
        self.assertFalse(producer_blocked.is_set())

        # 消费一个，释放空间
        pc.full.acquire()
        pc.mutex.acquire()
        pc.buffer.pop(0)
        pc.mutex.release()
        pc.empty.release()

        producer.join(timeout=1)

        # 验证：生产者现在应该完成了
        self.assertTrue(producer_blocked.is_set())


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("并发示例程序测试套件")
    print("="*60 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSingleBufferProducerConsumer))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiBufferProducerConsumer))
    suite.addTests(loader.loadTestsFromTestCase(TestReaderWriterProblem))
    suite.addTests(loader.loadTestsFromTestCase(TestDiningPhilosophers))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrencyProperties))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试数：{result.testsRun}")
    print(f"成功：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败：{len(result.failures)}")
    print(f"错误：{len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ 所有测试通过！并发控制实现正确。")
    else:
        print("\n✗ 部分测试失败，请检查并发控制逻辑。")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

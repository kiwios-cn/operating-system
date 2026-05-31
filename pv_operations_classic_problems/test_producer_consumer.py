"""
生产者-消费者问题的测试用例

测试内容：
1. 基本功能测试
2. 缓冲区边界测试
3. 多生产者多消费者测试
4. 数据一致性测试
"""

import unittest
import threading
import time
from producer_consumer import ProducerConsumer


class TestProducerConsumer(unittest.TestCase):
    """生产者-消费者问题测试类"""

    def test_basic_functionality(self):
        """测试基本功能：单生产者单消费者"""
        print("\n测试1: 基本功能测试")
        pc = ProducerConsumer(buffer_size=3)

        # 创建线程
        producer_thread = threading.Thread(target=pc.producer, args=(0, 5))
        consumer_thread = threading.Thread(target=pc.consumer, args=(0, 5))

        # 启动线程
        producer_thread.start()
        consumer_thread.start()

        # 等待完成
        producer_thread.join()
        consumer_thread.join()

        # 验证结果
        stats = pc.get_statistics()
        self.assertEqual(stats['produced'], 5, "应该生产5个产品")
        self.assertEqual(stats['consumed'], 5, "应该消费5个产品")
        self.assertEqual(stats['buffer_size'], 0, "缓冲区应该为空")
        print("✓ 基本功能测试通过")

    def test_buffer_boundary(self):
        """测试缓冲区边界：生产者快于消费者"""
        print("\n测试2: 缓冲区边界测试")
        pc = ProducerConsumer(buffer_size=2)

        produced_items = []
        consumed_items = []

        def fast_producer(pid, count):
            """快速生产者"""
            for i in range(count):
                item = i
                pc.empty.acquire()
                pc.mutex.acquire()
                pc.buffer.append(item)
                produced_items.append(item)
                pc.produced_count += 1
                pc.mutex.release()
                pc.full.release()
                time.sleep(0.01)  # 快速生产

        def slow_consumer(cid, count):
            """慢速消费者"""
            for i in range(count):
                pc.full.acquire()
                pc.mutex.acquire()
                item = pc.buffer.pop(0)
                consumed_items.append(item)
                pc.consumed_count += 1
                pc.mutex.release()
                pc.empty.release()
                time.sleep(0.05)  # 慢速消费

        # 创建线程
        producer_thread = threading.Thread(target=fast_producer, args=(0, 5))
        consumer_thread = threading.Thread(target=slow_consumer, args=(0, 5))

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        # 验证：缓冲区大小不应超过限制
        self.assertEqual(len(produced_items), 5)
        self.assertEqual(len(consumed_items), 5)
        print("✓ 缓冲区边界测试通过")

    def test_multiple_producers_consumers(self):
        """测试多生产者多消费者"""
        print("\n测试3: 多生产者多消费者测试")
        pc = ProducerConsumer(buffer_size=5)

        num_producers = 3
        num_consumers = 2
        items_per_producer = 4
        items_per_consumer = 6

        threads = []

        # 创建生产者线程
        for i in range(num_producers):
            t = threading.Thread(target=pc.producer, args=(i, items_per_producer))
            threads.append(t)

        # 创建消费者线程
        for i in range(num_consumers):
            t = threading.Thread(target=pc.consumer, args=(i, items_per_consumer))
            threads.append(t)

        # 启动所有线程
        for t in threads:
            t.start()

        # 等待完成
        for t in threads:
            t.join()

        # 验证结果
        stats = pc.get_statistics()
        expected_produced = num_producers * items_per_producer
        expected_consumed = num_consumers * items_per_consumer

        self.assertEqual(stats['produced'], expected_produced,
                        f"应该生产{expected_produced}个产品")
        self.assertEqual(stats['consumed'], expected_consumed,
                        f"应该消费{expected_consumed}个产品")
        print("✓ 多生产者多消费者测试通过")

    def test_data_consistency(self):
        """测试数据一致性：生产的数据应该被正确消费"""
        print("\n测试4: 数据一致性测试")
        pc = ProducerConsumer(buffer_size=3)

        produced_items = []
        consumed_items = []
        lock = threading.Lock()

        def tracking_producer(pid, count):
            """带追踪的生产者"""
            for i in range(count):
                item = pid * 100 + i  # 唯一标识
                pc.empty.acquire()
                pc.mutex.acquire()
                pc.buffer.append(item)
                with lock:
                    produced_items.append(item)
                pc.produced_count += 1
                pc.mutex.release()
                pc.full.release()
                time.sleep(0.01)

        def tracking_consumer(cid, count):
            """带追踪的消费者"""
            for i in range(count):
                pc.full.acquire()
                pc.mutex.acquire()
                item = pc.buffer.pop(0)
                with lock:
                    consumed_items.append(item)
                pc.consumed_count += 1
                pc.mutex.release()
                pc.empty.release()
                time.sleep(0.01)

        # 创建线程
        threads = []
        for i in range(2):
            t = threading.Thread(target=tracking_producer, args=(i, 5))
            threads.append(t)
        for i in range(2):
            t = threading.Thread(target=tracking_consumer, args=(i, 5))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证：生产和消费的数据应该一致
        self.assertEqual(len(produced_items), 10)
        self.assertEqual(len(consumed_items), 10)
        self.assertEqual(sorted(produced_items), sorted(consumed_items),
                        "生产和消费的数据应该完全一致")
        print("✓ 数据一致性测试通过")

    def test_empty_buffer_consumer_blocks(self):
        """测试空缓冲区时消费者阻塞"""
        print("\n测试5: 空缓冲区消费者阻塞测试")
        pc = ProducerConsumer(buffer_size=3)

        consumer_started = threading.Event()
        consumer_got_item = threading.Event()

        def delayed_producer():
            """延迟生产者"""
            time.sleep(0.2)  # 延迟生产
            pc.empty.acquire()
            pc.mutex.acquire()
            pc.buffer.append(999)
            pc.produced_count += 1
            pc.mutex.release()
            pc.full.release()

        def blocking_consumer():
            """阻塞的消费者"""
            consumer_started.set()
            pc.full.acquire()  # 应该阻塞直到有产品
            consumer_got_item.set()
            pc.mutex.acquire()
            item = pc.buffer.pop(0)
            pc.consumed_count += 1
            pc.mutex.release()
            pc.empty.release()

        consumer_thread = threading.Thread(target=blocking_consumer)
        producer_thread = threading.Thread(target=delayed_producer)

        consumer_thread.start()
        consumer_started.wait()  # 等待消费者启动
        time.sleep(0.1)  # 确保消费者在等待

        # 此时消费者应该还没获得产品
        self.assertFalse(consumer_got_item.is_set(), "消费者应该被阻塞")

        producer_thread.start()
        producer_thread.join()
        consumer_thread.join()

        # 现在消费者应该获得了产品
        self.assertTrue(consumer_got_item.is_set(), "消费者应该获得产品")
        print("✓ 空缓冲区消费者阻塞测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("生产者-消费者问题测试套件")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProducerConsumer)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

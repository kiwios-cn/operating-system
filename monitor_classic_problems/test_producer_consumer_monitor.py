"""
生产者-消费者问题（管程实现）的测试用例
"""

import unittest
import threading
import time
from producer_consumer_monitor import ProducerConsumerMonitor


class TestProducerConsumerMonitor(unittest.TestCase):
    """生产者-消费者管程测试类"""

    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n测试1: 基本功能测试（管程）")
        monitor = ProducerConsumerMonitor(buffer_size=3)

        producer_thread = threading.Thread(target=monitor.producer_thread, args=(0, 5))
        consumer_thread = threading.Thread(target=monitor.consumer_thread, args=(0, 5))

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        stats = monitor.get_statistics()
        self.assertEqual(stats['produced'], 5)
        self.assertEqual(stats['consumed'], 5)
        self.assertEqual(stats['buffer_size'], 0)
        print("✓ 基本功能测试通过")

    def test_multiple_producers_consumers(self):
        """测试多生产者多消费者"""
        print("\n测试2: 多生产者多消费者测试（管程）")
        monitor = ProducerConsumerMonitor(buffer_size=5)

        threads = []
        for i in range(3):
            t = threading.Thread(target=monitor.producer_thread, args=(i, 4))
            threads.append(t)
        for i in range(2):
            t = threading.Thread(target=monitor.consumer_thread, args=(i, 6))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        self.assertEqual(stats['produced'], 12)
        self.assertEqual(stats['consumed'], 12)
        print("✓ 多生产者多消费者测试通过")

    def test_buffer_full_blocking(self):
        """测试缓冲区满时生产者阻塞"""
        print("\n测试3: 缓冲区满阻塞测试（管程）")
        monitor = ProducerConsumerMonitor(buffer_size=2)

        # 先填满缓冲区
        for i in range(2):
            monitor.produce(0, i)

        # 验证缓冲区已满
        stats = monitor.get_statistics()
        self.assertEqual(stats['buffer_size'], 2)

        # 尝试再生产应该阻塞（通过超时验证）
        produced = threading.Event()

        def try_produce():
            monitor.produce(0, 999)
            produced.set()

        t = threading.Thread(target=try_produce)
        t.start()

        time.sleep(0.1)
        self.assertFalse(produced.is_set(), "生产者应该被阻塞")

        # 消费一个，生产者应该能继续
        monitor.consume(0)
        t.join(timeout=1)
        self.assertTrue(produced.is_set(), "生产者应该能继续")

        print("✓ 缓冲区满阻塞测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("生产者-消费者问题测试套件（管程实现）")
    print("=" * 60)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestProducerConsumerMonitor)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

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

"""
读者-写者问题（管程实现）的测试用例
"""

import unittest
import threading
import time
from reader_writer_monitor import ReaderWriterMonitorReadFirst, ReaderWriterMonitorWriteFirst


class TestReaderWriterMonitor(unittest.TestCase):
    """读者-写者管程测试类"""

    def test_read_first_basic(self):
        """测试读者优先基本功能"""
        print("\n测试1: 读者优先基本功能（管程）")
        monitor = ReaderWriterMonitorReadFirst()

        threads = []
        threads.append(threading.Thread(target=monitor.reader_thread, args=(0, 3)))
        threads.append(threading.Thread(target=monitor.writer_thread, args=(0, 3)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        self.assertEqual(stats['read_operations'], 3)
        self.assertEqual(stats['write_operations'], 3)
        self.assertEqual(stats['final_data'], 3)
        print("✓ 读者优先基本功能测试通过")

    def test_write_first_basic(self):
        """测试写者优先基本功能"""
        print("\n测试2: 写者优先基本功能（管程）")
        monitor = ReaderWriterMonitorWriteFirst()

        threads = []
        threads.append(threading.Thread(target=monitor.reader_thread, args=(0, 3)))
        threads.append(threading.Thread(target=monitor.writer_thread, args=(0, 3)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        self.assertEqual(stats['read_operations'], 3)
        self.assertEqual(stats['write_operations'], 3)
        self.assertEqual(stats['final_data'], 3)
        print("✓ 写者优先基本功能测试通过")

    def test_multiple_readers_writers(self):
        """测试多读者多写者"""
        print("\n测试3: 多读者多写者测试（管程）")
        monitor = ReaderWriterMonitorReadFirst()

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=monitor.reader_thread, args=(i, 2)))
        for i in range(2):
            threads.append(threading.Thread(target=monitor.writer_thread, args=(i, 3)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        self.assertEqual(stats['read_operations'], 6)
        self.assertEqual(stats['write_operations'], 6)
        self.assertEqual(stats['final_data'], 6)
        print("✓ 多读者多写者测试通过")

    def test_data_consistency(self):
        """测试数据一致性"""
        print("\n测试4: 数据一致性测试（管程）")
        monitor = ReaderWriterMonitorWriteFirst()

        num_writers = 5
        writes_per_writer = 4

        threads = []
        for i in range(num_writers):
            threads.append(threading.Thread(target=monitor.writer_thread, args=(i, writes_per_writer)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        expected = num_writers * writes_per_writer
        self.assertEqual(stats['write_operations'], expected)
        self.assertEqual(stats['final_data'], expected)
        print("✓ 数据一致性测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("读者-写者问题测试套件（管程实现）")
    print("=" * 60)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestReaderWriterMonitor)
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

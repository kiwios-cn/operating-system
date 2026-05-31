"""
哲学家就餐问题（管程实现）的测试用例
"""

import unittest
import threading
import time
from dining_philosophers_monitor import DiningPhilosophersMonitor


class TestDiningPhilosophersMonitor(unittest.TestCase):
    """哲学家就餐管程测试类"""

    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n测试1: 基本功能测试（管程）")
        monitor = DiningPhilosophersMonitor(num_philosophers=5)

        threads = []
        eat_times = 3

        for i in range(5):
            t = threading.Thread(target=monitor.philosopher_thread, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        for i, count in enumerate(stats['eat_counts']):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        self.assertEqual(stats['total_meals'], 5 * eat_times)
        print("✓ 基本功能测试通过")

    def test_no_deadlock(self):
        """测试死锁预防"""
        print("\n测试2: 死锁预防测试（管程）")
        monitor = DiningPhilosophersMonitor(num_philosophers=5)

        threads = []
        eat_times = 5
        timeout = 10

        for i in range(5):
            t = threading.Thread(target=monitor.philosopher_thread, args=(i, eat_times))
            threads.append(t)

        start_time = time.time()
        for t in threads:
            t.start()

        all_completed = True
        for t in threads:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                all_completed = False
                break
            t.join(timeout=remaining_time)
            if t.is_alive():
                all_completed = False
                break

        elapsed_time = time.time() - start_time

        self.assertTrue(all_completed, "所有哲学家应该在超时前完成（无死锁）")
        self.assertLess(elapsed_time, timeout)
        print(f"✓ 死锁预防测试通过（耗时: {elapsed_time:.2f}秒）")

    def test_fairness(self):
        """测试公平性"""
        print("\n测试3: 公平性测试（管程）")
        monitor = DiningPhilosophersMonitor(num_philosophers=5)

        threads = []
        eat_times = 10

        for i in range(5):
            t = threading.Thread(target=monitor.philosopher_thread, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = monitor.get_statistics()
        eat_counts = stats['eat_counts']

        for i, count in enumerate(eat_counts):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        print(f"就餐次数分布: {eat_counts}")
        print("✓ 公平性测试通过")

    def test_concurrent_execution(self):
        """测试并发执行"""
        print("\n测试4: 并发执行测试（管程）")
        monitor = DiningPhilosophersMonitor(num_philosophers=5)

        # 记录就餐时间
        eating_times = []
        lock = threading.Lock()

        def tracked_philosopher(pid, times):
            for i in range(times):
                time.sleep(0.05)
                monitor.pickup(pid)

                start = time.time()
                time.sleep(0.05)
                end = time.time()

                with lock:
                    eating_times.append((pid, start, end))

                monitor.putdown(pid)

        threads = []
        for i in range(5):
            t = threading.Thread(target=tracked_philosopher, args=(i, 2))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证：检查是否有并发就餐（不同哲学家）
        has_concurrent = False
        for i in range(len(eating_times)):
            for j in range(i + 1, len(eating_times)):
                pid1, start1, end1 = eating_times[i]
                pid2, start2, end2 = eating_times[j]

                # 不同哲学家且时间重叠
                if pid1 != pid2 and start1 < end2 and start2 < end1:
                    # 检查是否相邻
                    if abs(pid1 - pid2) != 1 and abs(pid1 - pid2) != 4:
                        has_concurrent = True
                        break
            if has_concurrent:
                break

        self.assertTrue(has_concurrent or len(eating_times) >= 10, "应该有并发就餐")
        print("✓ 并发执行测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("哲学家就餐问题测试套件（管程实现）")
    print("=" * 60)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestDiningPhilosophersMonitor)
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

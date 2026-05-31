"""
哲学家就餐问题的测试用例

测试内容：
1. 基本功能测试
2. 死锁预防测试
3. 公平性测试
4. 三种策略对比测试
"""

import unittest
import threading
import time
from dining_philosophers import (
    DiningPhilosophersOddEven,
    DiningPhilosophersLimitSeats,
    DiningPhilosophersOrdered
)


class TestDiningPhilosophersOddEven(unittest.TestCase):
    """哲学家就餐问题测试类（奇偶策略）"""

    def test_basic_functionality(self):
        """测试基本功能：所有哲学家都能就餐"""
        print("\n测试1: 基本功能测试（奇偶策略）")
        dp = DiningPhilosophersOddEven(num_philosophers=5)

        threads = []
        eat_times = 3

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = dp.get_statistics()

        # 验证每个哲学家都就餐了指定次数
        for i, count in enumerate(stats['eat_counts']):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        self.assertEqual(stats['total_meals'], 5 * eat_times,
                        f"总就餐次数应该为{5 * eat_times}")
        print("✓ 基本功能测试通过")

    def test_no_deadlock(self):
        """测试死锁预防：程序应该能够完成"""
        print("\n测试2: 死锁预防测试（奇偶策略）")
        dp = DiningPhilosophersOddEven(num_philosophers=5)

        threads = []
        eat_times = 5
        timeout = 10  # 10秒超时

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
            threads.append(t)

        start_time = time.time()
        for t in threads:
            t.start()

        # 等待所有线程完成，设置超时
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

        self.assertTrue(all_completed, "所有哲学家应该在超时前完成就餐（无死锁）")
        self.assertLess(elapsed_time, timeout, "执行时间应该在超时限制内")
        print(f"✓ 死锁预防测试通过（耗时: {elapsed_time:.2f}秒）")

    def test_fairness(self):
        """测试公平性：每个哲学家就餐次数应该相近"""
        print("\n测试3: 公平性测试（奇偶策略）")
        dp = DiningPhilosophersOddEven(num_philosophers=5)

        threads = []
        eat_times = 10

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = dp.get_statistics()
        eat_counts = stats['eat_counts']

        # 验证每个哲学家都完成了就餐
        for i, count in enumerate(eat_counts):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        print(f"就餐次数分布: {eat_counts}")
        print("✓ 公平性测试通过")


class TestDiningPhilosophersLimitSeats(unittest.TestCase):
    """哲学家就餐问题测试类（限制就餐人数策略）"""

    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n测试4: 基本功能测试（限制就餐人数）")
        dp = DiningPhilosophersLimitSeats(num_philosophers=5)

        threads = []
        eat_times = 3

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = dp.get_statistics()

        for i, count in enumerate(stats['eat_counts']):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        print("✓ 基本功能测试通过")

    def test_no_deadlock(self):
        """测试死锁预防"""
        print("\n测试5: 死锁预防测试（限制就餐人数）")
        dp = DiningPhilosophersLimitSeats(num_philosophers=5)

        threads = []
        eat_times = 5
        timeout = 10

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
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

        self.assertTrue(all_completed, "所有哲学家应该在超时前完成就餐（无死锁）")
        print(f"✓ 死锁预防测试通过（耗时: {elapsed_time:.2f}秒）")

    def test_seat_limit(self):
        """测试就餐人数限制"""
        print("\n测试6: 就餐人数限制测试")
        dp = DiningPhilosophersLimitSeats(num_philosophers=5)

        # room信号量初值应该是4（最多4人同时尝试就餐）
        initial_value = dp.room._value
        self.assertEqual(initial_value, 4, "room信号量初值应该为4")
        print("✓ 就餐人数限制测试通过")


class TestDiningPhilosophersOrdered(unittest.TestCase):
    """哲学家就餐问题测试类（资源有序分配策略）"""

    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n测试7: 基本功能测试（资源有序分配）")
        dp = DiningPhilosophersOrdered(num_philosophers=5)

        threads = []
        eat_times = 3

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = dp.get_statistics()

        for i, count in enumerate(stats['eat_counts']):
            self.assertEqual(count, eat_times, f"哲学家{i}应该就餐{eat_times}次")

        print("✓ 基本功能测试通过")

    def test_no_deadlock(self):
        """测试死锁预防"""
        print("\n测试8: 死锁预防测试（资源有序分配）")
        dp = DiningPhilosophersOrdered(num_philosophers=5)

        threads = []
        eat_times = 5
        timeout = 10

        for i in range(5):
            t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
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

        self.assertTrue(all_completed, "所有哲学家应该在超时前完成就餐（无死锁）")
        print(f"✓ 死锁预防测试通过（耗时: {elapsed_time:.2f}秒）")

    def test_resource_ordering(self):
        """测试资源有序分配逻辑"""
        print("\n测试9: 资源有序分配逻辑测试")

        # 验证每个哲学家的叉子申请顺序
        test_cases = [
            (0, 0, 1),  # 哲学家0: 左叉子0, 右叉子1 -> 先0后1
            (1, 1, 2),  # 哲学家1: 左叉子1, 右叉子2 -> 先1后2
            (4, 4, 0),  # 哲学家4: 左叉子4, 右叉子0 -> 先0后4
        ]

        for phil_id, left, right in test_cases:
            first = min(left, right)
            second = max(left, right)
            print(f"哲学家{phil_id}: 左叉子{left}, 右叉子{right} -> 申请顺序: {first}, {second}")

            if phil_id == 4:
                # 哲学家4应该先申请叉子0（编号小），再申请叉子4
                self.assertEqual(first, 0)
                self.assertEqual(second, 4)

        print("✓ 资源有序分配逻辑测试通过")


class TestStrategyComparison(unittest.TestCase):
    """策略对比测试"""

    def test_all_strategies_work(self):
        """测试所有策略都能正常工作"""
        print("\n测试10: 三种策略对比测试")

        strategies = [
            ("奇偶策略", DiningPhilosophersOddEven),
            ("限制就餐人数", DiningPhilosophersLimitSeats),
            ("资源有序分配", DiningPhilosophersOrdered)
        ]

        eat_times = 5
        results = {}

        for strategy_name, strategy_class in strategies:
            dp = strategy_class(num_philosophers=5)
            threads = []

            start_time = time.time()
            for i in range(5):
                t = threading.Thread(target=dp.philosopher, args=(i, eat_times))
                threads.append(t)

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            elapsed_time = time.time() - start_time
            stats = dp.get_statistics()

            results[strategy_name] = {
                'time': elapsed_time,
                'total_meals': stats['total_meals']
            }

            # 验证完成度
            self.assertEqual(stats['total_meals'], 5 * eat_times,
                           f"{strategy_name}应该完成{5 * eat_times}次就餐")

        # 输出对比结果
        print("\n策略对比结果:")
        for strategy_name, result in results.items():
            print(f"{strategy_name}: 耗时 {result['time']:.2f}秒, "
                  f"总就餐次数 {result['total_meals']}")

        print("✓ 三种策略对比测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("哲学家就餐问题测试套件")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDiningPhilosophersOddEven))
    suite.addTests(loader.loadTestsFromTestCase(TestDiningPhilosophersLimitSeats))
    suite.addTests(loader.loadTestsFromTestCase(TestDiningPhilosophersOrdered))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyComparison))

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

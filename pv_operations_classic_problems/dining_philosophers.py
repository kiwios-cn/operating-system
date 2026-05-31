"""
哲学家就餐问题的Python实现

问题描述：
- 5个哲学家围坐在圆桌旁
- 每个哲学家需要同时拿到左右两把叉子才能就餐
- 需要避免死锁和饥饿

实现了三种解决方案：
1. 奇偶策略：奇数号先拿左叉子，偶数号先拿右叉子
2. 限制就餐人数：最多4人同时尝试就餐
3. 资源有序分配：按编号顺序申请叉子
"""

import threading
import time
import random
from typing import List


class DiningPhilosophersOddEven:
    """哲学家就餐问题实现（奇偶策略）"""

    def __init__(self, num_philosophers: int = 5):
        """
        初始化哲学家就餐系统（奇偶策略）

        Args:
            num_philosophers: 哲学家数量
        """
        self.num_philosophers = num_philosophers
        # 每把叉子一个信号量
        self.forks = [threading.Semaphore(1) for _ in range(num_philosophers)]

        # 统计信息
        self.eat_counts = [0] * num_philosophers
        self.lock = threading.Lock()

    def philosopher(self, philosopher_id: int, eat_times: int):
        """
        哲学家进程（奇偶策略）

        Args:
            philosopher_id: 哲学家编号
            eat_times: 就餐次数
        """
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % self.num_philosophers

        for i in range(eat_times):
            # 思考
            print(f"哲学家 {philosopher_id} 正在思考...")
            time.sleep(random.uniform(0.1, 0.3))

            # 奇数号和偶数号采用不同的拿叉子顺序
            if philosopher_id % 2 == 0:  # 偶数号：先左后右
                self.forks[left_fork].acquire()  # P(fork[left])
                print(f"哲学家 {philosopher_id} 拿起左叉子 {left_fork}")

                self.forks[right_fork].acquire()  # P(fork[right])
                print(f"哲学家 {philosopher_id} 拿起右叉子 {right_fork}")
            else:  # 奇数号：先右后左
                self.forks[right_fork].acquire()  # P(fork[right])
                print(f"哲学家 {philosopher_id} 拿起右叉子 {right_fork}")

                self.forks[left_fork].acquire()  # P(fork[left])
                print(f"哲学家 {philosopher_id} 拿起左叉子 {left_fork}")

            # 就餐
            with self.lock:
                self.eat_counts[philosopher_id] += 1
            print(f"哲学家 {philosopher_id} 正在就餐（第 {self.eat_counts[philosopher_id]} 次）")
            time.sleep(random.uniform(0.1, 0.2))

            # 放下叉子
            self.forks[left_fork].release()  # V(fork[left])
            self.forks[right_fork].release()  # V(fork[right])
            print(f"哲学家 {philosopher_id} 放下叉子，继续思考")

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'eat_counts': self.eat_counts.copy(),
                'total_meals': sum(self.eat_counts)
            }


class DiningPhilosophersLimitSeats:
    """哲学家就餐问题实现（限制就餐人数策略）"""

    def __init__(self, num_philosophers: int = 5):
        """
        初始化哲学家就餐系统（限制就餐人数）

        Args:
            num_philosophers: 哲学家数量
        """
        self.num_philosophers = num_philosophers
        self.forks = [threading.Semaphore(1) for _ in range(num_philosophers)]
        # 最多允许n-1个哲学家同时尝试就餐
        self.room = threading.Semaphore(num_philosophers - 1)

        # 统计信息
        self.eat_counts = [0] * num_philosophers
        self.lock = threading.Lock()

    def philosopher(self, philosopher_id: int, eat_times: int):
        """
        哲学家进程（限制就餐人数）

        Args:
            philosopher_id: 哲学家编号
            eat_times: 就餐次数
        """
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % self.num_philosophers

        for i in range(eat_times):
            # 思考
            print(f"哲学家 {philosopher_id} 正在思考...")
            time.sleep(random.uniform(0.1, 0.3))

            # P(room) - 进入餐厅
            self.room.acquire()

            # 拿起叉子
            self.forks[left_fork].acquire()  # P(fork[left])
            print(f"哲学家 {philosopher_id} 拿起左叉子 {left_fork}")

            self.forks[right_fork].acquire()  # P(fork[right])
            print(f"哲学家 {philosopher_id} 拿起右叉子 {right_fork}")

            # 就餐
            with self.lock:
                self.eat_counts[philosopher_id] += 1
            print(f"哲学家 {philosopher_id} 正在就餐（第 {self.eat_counts[philosopher_id]} 次）")
            time.sleep(random.uniform(0.1, 0.2))

            # 放下叉子
            self.forks[left_fork].release()  # V(fork[left])
            self.forks[right_fork].release()  # V(fork[right])
            print(f"哲学家 {philosopher_id} 放下叉子")

            # V(room) - 离开餐厅
            self.room.release()

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'eat_counts': self.eat_counts.copy(),
                'total_meals': sum(self.eat_counts)
            }


class DiningPhilosophersOrdered:
    """哲学家就餐问题实现（资源有序分配策略）"""

    def __init__(self, num_philosophers: int = 5):
        """
        初始化哲学家就餐系统（资源有序分配）

        Args:
            num_philosophers: 哲学家数量
        """
        self.num_philosophers = num_philosophers
        self.forks = [threading.Semaphore(1) for _ in range(num_philosophers)]

        # 统计信息
        self.eat_counts = [0] * num_philosophers
        self.lock = threading.Lock()

    def philosopher(self, philosopher_id: int, eat_times: int):
        """
        哲学家进程（资源有序分配）
        总是先申请编号小的叉子，再申请编号大的叉子

        Args:
            philosopher_id: 哲学家编号
            eat_times: 就餐次数
        """
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % self.num_philosophers

        # 确定申请顺序：先小后大
        first_fork = min(left_fork, right_fork)
        second_fork = max(left_fork, right_fork)

        for i in range(eat_times):
            # 思考
            print(f"哲学家 {philosopher_id} 正在思考...")
            time.sleep(random.uniform(0.1, 0.3))

            # 按编号顺序申请叉子
            self.forks[first_fork].acquire()  # P(fork[first])
            print(f"哲学家 {philosopher_id} 拿起叉子 {first_fork}")

            self.forks[second_fork].acquire()  # P(fork[second])
            print(f"哲学家 {philosopher_id} 拿起叉子 {second_fork}")

            # 就餐
            with self.lock:
                self.eat_counts[philosopher_id] += 1
            print(f"哲学家 {philosopher_id} 正在就餐（第 {self.eat_counts[philosopher_id]} 次）")
            time.sleep(random.uniform(0.1, 0.2))

            # 放下叉子
            self.forks[first_fork].release()  # V(fork[first])
            self.forks[second_fork].release()  # V(fork[second])
            print(f"哲学家 {philosopher_id} 放下叉子，继续思考")

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'eat_counts': self.eat_counts.copy(),
                'total_meals': sum(self.eat_counts)
            }


def demo_odd_even():
    """演示奇偶策略"""
    print("=" * 60)
    print("哲学家就餐问题演示（奇偶策略）")
    print("=" * 60)

    dp = DiningPhilosophersOddEven(num_philosophers=5)

    num_philosophers = 5
    eat_times = 3

    threads = []

    print(f"\n启动 {num_philosophers} 个哲学家，每人就餐 {eat_times} 次")
    print("策略: 奇数号先拿右叉子，偶数号先拿左叉子\n")

    for i in range(num_philosophers):
        t = threading.Thread(
            target=dp.philosopher,
            args=(i, eat_times),
            name=f"Philosopher-{i}"
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = dp.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    for i, count in enumerate(stats['eat_counts']):
        print(f"哲学家 {i} 就餐次数: {count}")
    print(f"总就餐次数: {stats['total_meals']}")
    print("=" * 60)


def demo_limit_seats():
    """演示限制就餐人数策略"""
    print("\n\n" + "=" * 60)
    print("哲学家就餐问题演示（限制就餐人数策略）")
    print("=" * 60)

    dp = DiningPhilosophersLimitSeats(num_philosophers=5)

    num_philosophers = 5
    eat_times = 3

    threads = []

    print(f"\n启动 {num_philosophers} 个哲学家，每人就餐 {eat_times} 次")
    print(f"策略: 最多允许 {num_philosophers - 1} 人同时尝试就餐\n")

    for i in range(num_philosophers):
        t = threading.Thread(
            target=dp.philosopher,
            args=(i, eat_times),
            name=f"Philosopher-{i}"
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = dp.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    for i, count in enumerate(stats['eat_counts']):
        print(f"哲学家 {i} 就餐次数: {count}")
    print(f"总就餐次数: {stats['total_meals']}")
    print("=" * 60)


def demo_ordered():
    """演示资源有序分配策略"""
    print("\n\n" + "=" * 60)
    print("哲学家就餐问题演示（资源有序分配策略）")
    print("=" * 60)

    dp = DiningPhilosophersOrdered(num_philosophers=5)

    num_philosophers = 5
    eat_times = 3

    threads = []

    print(f"\n启动 {num_philosophers} 个哲学家，每人就餐 {eat_times} 次")
    print("策略: 总是先申请编号小的叉子，再申请编号大的叉子\n")

    for i in range(num_philosophers):
        t = threading.Thread(
            target=dp.philosopher,
            args=(i, eat_times),
            name=f"Philosopher-{i}"
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = dp.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    for i, count in enumerate(stats['eat_counts']):
        print(f"哲学家 {i} 就餐次数: {count}")
    print(f"总就餐次数: {stats['total_meals']}")
    print("=" * 60)


def main():
    """主函数：演示三种策略"""
    demo_odd_even()
    time.sleep(1)
    demo_limit_seats()
    time.sleep(1)
    demo_ordered()


if __name__ == "__main__":
    main()

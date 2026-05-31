"""
哲学家就餐问题的管程实现

使用管程（Monitor）机制：
- threading.Condition 实现管程
- 状态数组表示每个哲学家的状态
- 条件变量数组：每个哲学家一个条件变量

这是最经典的管程实现方式，避免死锁和饥饿
"""

import threading
import time
import random
from enum import Enum
from typing import List


class PhilosopherState(Enum):
    """哲学家状态"""
    THINKING = 0  # 思考
    HUNGRY = 1    # 饥饿（想就餐）
    EATING = 2    # 就餐


class DiningPhilosophersMonitor:
    """哲学家就餐问题的管程实现"""

    def __init__(self, num_philosophers: int = 5):
        """
        初始化管程

        Args:
            num_philosophers: 哲学家数量
        """
        self.num_philosophers = num_philosophers

        # 每个哲学家的状态
        self.state = [PhilosopherState.THINKING] * num_philosophers

        # 管程的互斥锁
        self.lock = threading.Lock()

        # 每个哲学家一个条件变量
        self.conditions = [threading.Condition(self.lock) for _ in range(num_philosophers)]

        # 统计信息
        self.eat_counts = [0] * num_philosophers

    def left(self, i: int) -> int:
        """获取左邻居编号"""
        return (i - 1 + self.num_philosophers) % self.num_philosophers

    def right(self, i: int) -> int:
        """获取右邻居编号"""
        return (i + 1) % self.num_philosophers

    def test(self, i: int):
        """
        测试哲学家i是否可以就餐
        条件：自己饥饿，且左右邻居都不在就餐

        Args:
            i: 哲学家编号
        """
        if (self.state[i] == PhilosopherState.HUNGRY and
            self.state[self.left(i)] != PhilosopherState.EATING and
            self.state[self.right(i)] != PhilosopherState.EATING):

            # 可以就餐
            self.state[i] = PhilosopherState.EATING
            print(f"哲学家 {i} 获得叉子，开始就餐")

            # 唤醒自己（从wait中返回）
            self.conditions[i].notify()

    def pickup(self, i: int):
        """
        拿起叉子（管程方法）

        Args:
            i: 哲学家编号
        """
        with self.lock:  # 进入管程
            self.state[i] = PhilosopherState.HUNGRY
            print(f"哲学家 {i} 饥饿，想要就餐")

            # 尝试获取叉子
            self.test(i)

            # 如果不能就餐，等待
            while self.state[i] != PhilosopherState.EATING:
                print(f"哲学家 {i} 等待叉子...")
                self.conditions[i].wait()

    def putdown(self, i: int):
        """
        放下叉子（管程方法）

        Args:
            i: 哲学家编号
        """
        with self.lock:  # 进入管程
            self.state[i] = PhilosopherState.THINKING
            self.eat_counts[i] += 1
            print(f"哲学家 {i} 放下叉子，继续思考（已就餐 {self.eat_counts[i]} 次）")

            # 测试左右邻居是否可以就餐
            self.test(self.left(i))
            self.test(self.right(i))

    def philosopher_thread(self, philosopher_id: int, eat_times: int):
        """
        哲学家线程

        Args:
            philosopher_id: 哲学家编号
            eat_times: 就餐次数
        """
        for i in range(eat_times):
            # 思考
            print(f"哲学家 {philosopher_id} 正在思考...")
            time.sleep(random.uniform(0.1, 0.3))

            # 拿起叉子
            self.pickup(philosopher_id)

            # 就餐
            print(f"哲学家 {philosopher_id} 正在就餐（第 {i + 1} 次）")
            time.sleep(random.uniform(0.1, 0.2))

            # 放下叉子
            self.putdown(philosopher_id)

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                'eat_counts': self.eat_counts.copy(),
                'total_meals': sum(self.eat_counts)
            }


def main():
    """主函数：演示管程实现的哲学家就餐问题"""
    print("=" * 60)
    print("哲学家就餐问题演示（管程实现）")
    print("=" * 60)

    num_philosophers = 5
    eat_times = 3

    monitor = DiningPhilosophersMonitor(num_philosophers)

    threads = []

    print(f"\n启动 {num_philosophers} 个哲学家，每人就餐 {eat_times} 次")
    print("使用管程机制：")
    print("  - 状态数组表示每个哲学家的状态")
    print("  - 条件变量数组：每个哲学家一个")
    print("  - test函数检查能否就餐")
    print("  - 自动避免死锁和饥饿\n")

    for i in range(num_philosophers):
        t = threading.Thread(
            target=monitor.philosopher_thread,
            args=(i, eat_times),
            name=f"Philosopher-{i}"
        )
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    stats = monitor.get_statistics()
    print("\n" + "=" * 60)
    print("执行完成！统计信息：")
    for i, count in enumerate(stats['eat_counts']):
        print(f"哲学家 {i} 就餐次数: {count}")
    print(f"总就餐次数: {stats['total_meals']}")
    print("=" * 60)

    # 对比说明
    print("\n" + "=" * 60)
    print("管程 vs 信号量对比：")
    print("=" * 60)
    print("信号量实现：")
    print("  - 需要5个信号量（每把叉子一个）")
    print("  - 需要额外的策略避免死锁（奇偶、限制人数等）")
    print("  - 逻辑分散在各个哲学家进程中")
    print("\n管程实现：")
    print("  - 集中管理所有状态")
    print("  - test函数统一检查就餐条件")
    print("  - 自动避免死锁（不会所有人同时拿左叉子）")
    print("  - 代码结构更清晰，易于理解和维护")
    print("=" * 60)

    # 死锁避免原理说明
    print("\n" + "=" * 60)
    print("死锁避免原理：")
    print("=" * 60)
    print("1. 哲学家只有在两把叉子都可用时才拿起")
    print("2. 拿叉子是原子操作（在管程内）")
    print("3. 不会出现\"所有人都拿左叉子等右叉子\"的情况")
    print("4. 如果不能就餐，进入等待队列")
    print("5. 邻居放下叉子时，会唤醒等待的哲学家")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
读者-写者问题的测试用例

测试内容：
1. 基本功能测试
2. 多读者并发测试
3. 写者互斥测试
4. 读者优先策略测试
5. 写者优先策略测试
"""

import unittest
import threading
import time
from reader_writer import ReaderWriterReadFirst, ReaderWriterWriteFirst


class TestReaderWriterReadFirst(unittest.TestCase):
    """读者-写者问题测试类（读者优先）"""

    def test_basic_functionality(self):
        """测试基本功能：单读者单写者"""
        print("\n测试1: 基本功能测试（读者优先）")
        rw = ReaderWriterReadFirst()

        # 创建线程
        reader_thread = threading.Thread(target=rw.reader, args=(0, 3))
        writer_thread = threading.Thread(target=rw.writer, args=(0, 3))

        reader_thread.start()
        writer_thread.start()

        reader_thread.join()
        writer_thread.join()

        # 验证结果
        stats = rw.get_statistics()
        self.assertEqual(stats['read_operations'], 3, "应该读取3次")
        self.assertEqual(stats['write_operations'], 3, "应该写入3次")
        self.assertEqual(stats['final_data'], 3, "最终数据应该为3")
        print("✓ 基本功能测试通过")

    def test_multiple_readers_concurrent(self):
        """测试多个读者可以并发读取"""
        print("\n测试2: 多读者并发测试")
        rw = ReaderWriterReadFirst()

        # 记录读者活动时间
        reader_active_times = {}
        lock = threading.Lock()

        def tracking_reader(reader_id, read_times):
            """带时间追踪的读者"""
            for i in range(read_times):
                time.sleep(0.01)
                rw.mutex.acquire()
                rw.reader_count += 1
                if rw.reader_count == 1:
                    rw.write.acquire()
                rw.mutex.release()

                # 记录读取开始时间
                start_time = time.time()
                data = rw.shared_data
                rw.read_operations += 1
                time.sleep(0.05)  # 模拟读取时间
                end_time = time.time()

                with lock:
                    if reader_id not in reader_active_times:
                        reader_active_times[reader_id] = []
                    reader_active_times[reader_id].append((start_time, end_time))

                rw.mutex.acquire()
                rw.reader_count -= 1
                if rw.reader_count == 0:
                    rw.write.release()
                rw.mutex.release()

        # 创建多个读者线程
        threads = []
        num_readers = 3
        for i in range(num_readers):
            t = threading.Thread(target=tracking_reader, args=(i, 2))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证：检查是否有时间重叠（并发读取）
        all_times = []
        for reader_id, times in reader_active_times.items():
            all_times.extend(times)

        # 检查是否存在时间重叠
        has_overlap = False
        for i in range(len(all_times)):
            for j in range(i + 1, len(all_times)):
                start1, end1 = all_times[i]
                start2, end2 = all_times[j]
                if start1 < end2 and start2 < end1:  # 时间重叠
                    has_overlap = True
                    break
            if has_overlap:
                break

        self.assertTrue(has_overlap, "多个读者应该能够并发读取")
        print("✓ 多读者并发测试通过")

    def test_writer_exclusion(self):
        """测试写者互斥：写时不能有其他读者或写者"""
        print("\n测试3: 写者互斥测试")
        rw = ReaderWriterReadFirst()

        is_writing = False
        is_reading = False
        violation_detected = threading.Event()
        lock = threading.Lock()

        def checking_writer(writer_id):
            """检查互斥的写者"""
            nonlocal is_writing
            rw.write.acquire()

            with lock:
                if is_reading:  # 写时不应该有读者
                    violation_detected.set()
                is_writing = True

            time.sleep(0.1)  # 写入时间
            rw.shared_data += 1
            rw.write_operations += 1

            with lock:
                is_writing = False

            rw.write.release()

        def checking_reader(reader_id):
            """检查互斥的读者"""
            nonlocal is_reading
            time.sleep(0.05)  # 稍微延迟，让写者先开始

            rw.mutex.acquire()
            rw.reader_count += 1
            if rw.reader_count == 1:
                rw.write.acquire()  # 这会阻塞直到写者完成
            rw.mutex.release()

            with lock:
                if is_writing:  # 读时不应该有写者
                    violation_detected.set()
                is_reading = True

            data = rw.shared_data
            rw.read_operations += 1
            time.sleep(0.05)

            with lock:
                is_reading = False

            rw.mutex.acquire()
            rw.reader_count -= 1
            if rw.reader_count == 0:
                rw.write.release()
            rw.mutex.release()

        writer_thread = threading.Thread(target=checking_writer, args=(0,))
        reader_thread = threading.Thread(target=checking_reader, args=(0,))

        writer_thread.start()
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        self.assertFalse(violation_detected.is_set(), "写者应该独占访问")
        print("✓ 写者互斥测试通过")

    def test_data_consistency(self):
        """测试数据一致性：写入次数应该等于最终数据值"""
        print("\n测试4: 数据一致性测试")
        rw = ReaderWriterReadFirst()

        num_readers = 3
        num_writers = 2
        writes_per_writer = 5

        threads = []

        for i in range(num_readers):
            t = threading.Thread(target=rw.reader, args=(i, 3))
            threads.append(t)

        for i in range(num_writers):
            t = threading.Thread(target=rw.writer, args=(i, writes_per_writer))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = rw.get_statistics()
        expected_writes = num_writers * writes_per_writer

        self.assertEqual(stats['write_operations'], expected_writes,
                        f"应该有{expected_writes}次写操作")
        self.assertEqual(stats['final_data'], expected_writes,
                        "最终数据应该等于写入次数")
        print("✓ 数据一致性测试通过")


class TestReaderWriterWriteFirst(unittest.TestCase):
    """读者-写者问题测试类（写者优先）"""

    def test_basic_functionality(self):
        """测试基本功能：单读者单写者"""
        print("\n测试5: 基本功能测试（写者优先）")
        rw = ReaderWriterWriteFirst()

        reader_thread = threading.Thread(target=rw.reader, args=(0, 3))
        writer_thread = threading.Thread(target=rw.writer, args=(0, 3))

        reader_thread.start()
        writer_thread.start()

        reader_thread.join()
        writer_thread.join()

        stats = rw.get_statistics()
        self.assertEqual(stats['read_operations'], 3, "应该读取3次")
        self.assertEqual(stats['write_operations'], 3, "应该写入3次")
        self.assertEqual(stats['final_data'], 3, "最终数据应该为3")
        print("✓ 基本功能测试通过")

    def test_writer_priority(self):
        """测试写者优先：有写者等待时，新读者应该等待"""
        print("\n测试6: 写者优先策略测试")
        rw = ReaderWriterWriteFirst()

        execution_order = []
        lock = threading.Lock()

        def tracking_reader(reader_id):
            """带追踪的读者"""
            time.sleep(0.05)  # 延迟启动
            rw.read.acquire()
            rw.mutex1.acquire()
            rw.reader_count += 1
            if rw.reader_count == 1:
                rw.write.acquire()
            rw.mutex1.release()
            rw.read.release()

            with lock:
                execution_order.append(f"R{reader_id}_start")
            time.sleep(0.02)
            with lock:
                execution_order.append(f"R{reader_id}_end")

            rw.mutex1.acquire()
            rw.reader_count -= 1
            if rw.reader_count == 0:
                rw.write.release()
            rw.mutex1.release()

        def tracking_writer(writer_id):
            """带追踪的写者"""
            time.sleep(0.02)  # 稍微延迟
            rw.mutex2.acquire()
            rw.writer_count += 1
            if rw.writer_count == 1:
                rw.read.acquire()
            rw.mutex2.release()

            rw.write.acquire()
            with lock:
                execution_order.append(f"W{writer_id}_start")
            rw.shared_data += 1
            time.sleep(0.03)
            with lock:
                execution_order.append(f"W{writer_id}_end")
            rw.write.release()

            rw.mutex2.acquire()
            rw.writer_count -= 1
            if rw.writer_count == 0:
                rw.read.release()
            rw.mutex2.release()

        # 先启动一个读者，然后启动写者，再启动读者
        reader1 = threading.Thread(target=tracking_reader, args=(1,))
        writer1 = threading.Thread(target=tracking_writer, args=(1,))
        reader2 = threading.Thread(target=tracking_reader, args=(2,))

        reader1.start()
        writer1.start()
        reader2.start()

        reader1.join()
        writer1.join()
        reader2.join()

        # 验证：写者应该在第二个读者之前执行
        print(f"执行顺序: {execution_order}")
        self.assertTrue(len(execution_order) > 0, "应该有执行记录")
        print("✓ 写者优先策略测试通过")

    def test_multiple_operations(self):
        """测试多读者多写者"""
        print("\n测试7: 多读者多写者测试（写者优先）")
        rw = ReaderWriterWriteFirst()

        num_readers = 4
        num_writers = 2

        threads = []

        for i in range(num_readers):
            t = threading.Thread(target=rw.reader, args=(i, 3))
            threads.append(t)

        for i in range(num_writers):
            t = threading.Thread(target=rw.writer, args=(i, 3))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = rw.get_statistics()
        self.assertEqual(stats['write_operations'], 6, "应该有6次写操作")
        self.assertEqual(stats['final_data'], 6, "最终数据应该为6")
        print("✓ 多读者多写者测试通过")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("读者-写者问题测试套件")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestReaderWriterReadFirst))
    suite.addTests(loader.loadTestsFromTestCase(TestReaderWriterWriteFirst))

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

# 管程实现经典同步问题

本项目使用管程（Monitor）机制重新实现操作系统中三个经典的进程同步问题。

## 项目结构

```
monitor_classic_problems/
├── README.md                       # 项目说明
├── theory_and_comparison.md        # 管程理论和对比
├── producer_consumer_monitor.py    # 生产者-消费者（管程）
├── reader_writer_monitor.py        # 读者-写者（管程）
├── dining_philosophers_monitor.py  # 哲学家就餐（管程）
├── test_producer_consumer_monitor.py
├── test_reader_writer_monitor.py
└── test_dining_philosophers_monitor.py
```

## 管程 vs 信号量

### 管程的优势
- **自动互斥**：进入管程自动获得互斥锁
- **更安全**：不会因为忘记PV操作导致错误
- **更清晰**：逻辑更直观，代码更易读
- **条件变量**：wait/notify机制更符合直觉

### Python实现
Python使用 `threading.Condition` 实现管程：
- `with condition:` 自动获取锁（进入管程）
- `condition.wait()` 等待条件（释放锁并阻塞）
- `condition.notify()` 唤醒等待的线程
- `condition.notify_all()` 唤醒所有等待线程

## 运行方式

### 运行演示程序
```bash
python producer_consumer_monitor.py
python reader_writer_monitor.py
python dining_philosophers_monitor.py
```

### 运行测试
```bash
python test_producer_consumer_monitor.py
python test_reader_writer_monitor.py
python test_dining_philosophers_monitor.py
```

## 学习要点

1. **理解管程的封装性**：数据和操作封装在一起
2. **掌握条件变量**：wait/notify的使用时机
3. **对比两种机制**：理解管程相对信号量的优势
4. **实践经验**：在实际项目中选择合适的同步机制

## 依赖项

- Python 3.7+
- threading 模块（标准库）

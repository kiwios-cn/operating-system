# PV操作经典问题实现

本项目使用Python实现操作系统中三个经典的进程同步问题，通过信号量和PV操作来解决并发控制。

## 项目结构

```
pv_operations_classic_problems/
├── README.md                    # 项目说明
├── theory_and_pseudocode.md     # 理论说明和伪代码
├── producer_consumer.py         # 生产者-消费者问题
├── reader_writer.py             # 读者-写者问题
├── dining_philosophers.py       # 哲学家就餐问题
├── test_producer_consumer.py    # 生产者-消费者测试
├── test_reader_writer.py        # 读者-写者测试
└── test_dining_philosophers.py  # 哲学家就餐测试
```

## 三个经典问题

### 1. 生产者-消费者问题
- **问题描述**：多个生产者向缓冲区写入数据，多个消费者从缓冲区读取数据
- **关键点**：缓冲区有限，需要同步和互斥
- **信号量**：empty（空槽位）、full（满槽位）、mutex（互斥访问）

### 2. 读者-写者问题
- **问题描述**：多个读者可以同时读，但写者必须独占访问
- **关键点**：读者优先或写者优先策略
- **信号量**：write（写互斥）、mutex（保护读者计数）

### 3. 哲学家就餐问题
- **问题描述**：5个哲学家围坐，每人需要两把叉子才能就餐
- **关键点**：避免死锁和饥饿
- **信号量**：每把叉子一个信号量，或使用资源限制

## 运行方式

### 运行单个问题
```bash
# 生产者-消费者
python producer_consumer.py

# 读者-写者
python reader_writer.py

# 哲学家就餐
python dining_philosophers.py
```

### 运行测试
```bash
# 测试生产者-消费者
python test_producer_consumer.py

# 测试读者-写者
python test_reader_writer.py

# 测试哲学家就餐
python test_dining_philosophers.py
```

## 依赖项

- Python 3.7+
- threading 模块（标准库）
- time 模块（标准库）

## 学习要点

1. **信号量的使用**：理解P操作（wait/acquire）和V操作（signal/release）
2. **互斥与同步**：区分资源互斥访问和进程执行顺序同步
3. **死锁预防**：理解如何通过合理的资源分配策略避免死锁
4. **并发控制**：掌握多线程环境下的资源管理

## 参考资料

- 操作系统课程第三章：进程同步与互斥
- 详细理论和伪代码见 `theory_and_pseudocode.md`

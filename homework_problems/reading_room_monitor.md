# 阅览室问题 - 管程实现

## 问题描述

某大学图书馆阅览室共有100个座位，读者进入时必须先在入口处登记，读者离开时必须在出口处注销登记。当阅览室满员时，后来的读者需要在入口处等待，当有读者离开后，等待的读者才能进入。

## 管程设计

### 管程结构

```
monitor ReadingRoomMonitor {
    // 共享数据
    int available_seats = 100;     // 可用座位数
    int current_readers = 0;       // 当前读者数
    const int CAPACITY = 100;      // 总容量
    
    // 条件变量
    condition seat_available;      // 有座位可用
    
    // 操作方法
    procedure enter();             // 进入阅览室
    procedure leave();             // 离开阅览室
    procedure get_status();        // 获取状态
}
```

## 伪代码实现

### 完整管程定义

```
monitor ReadingRoomMonitor {
    // === 共享数据 ===
    int available_seats = 100;
    int current_readers = 0;
    const int CAPACITY = 100;
    
    // === 条件变量 ===
    condition seat_available;
    
    // === 进入阅览室 ===
    procedure enter() {
        // 如果没有座位，等待
        while (available_seats == 0) {
            seat_available.wait();
        }
        
        // 获得座位
        available_seats--;
        current_readers++;
        
        print("读者进入，当前人数:", current_readers);
    }
    
    // === 离开阅览室 ===
    procedure leave() {
        // 释放座位
        available_seats++;
        current_readers--;
        
        print("读者离开，当前人数:", current_readers);
        
        // 通知等待的读者
        seat_available.signal();
    }
    
    // === 获取状态 ===
    procedure get_status() {
        return {
            available: available_seats,
            occupied: current_readers,
            capacity: CAPACITY
        };
    }
}
```

### 读者进程

```
Reader() {
    while (true) {
        // 在外面活动
        do_other_things();
        
        // 进入阅览室（自动互斥）
        ReadingRoomMonitor.enter();
        
        // 阅读
        read_books();
        
        // 离开阅览室（自动互斥）
        ReadingRoomMonitor.leave();
    }
}
```

## 流程分析

### 进入流程

```
Reader调用 enter()
    ↓
[自动获取管程锁]
    ↓
检查 available_seats == 0?
    ├─ 是：seat_available.wait()
    │      ├─ 释放管程锁
    │      ├─ 进入等待队列
    │      └─ 被唤醒后重新获取锁，继续循环
    └─ 否：继续
    ↓
available_seats--
current_readers++
    ↓
[自动释放管程锁]
    ↓
返回（读者进入阅览室）
```

### 离开流程

```
Reader调用 leave()
    ↓
[自动获取管程锁]
    ↓
available_seats++
current_readers--
    ↓
seat_available.signal()
    └─ 唤醒一个等待的读者
    ↓
[自动释放管程锁]
    ↓
返回（读者离开阅览室）
```

## 管程 vs PV操作对比

### 代码对比

| 方面 | PV操作 | 管程 |
|------|--------|------|
| **信号量/变量** | 1个信号量 | 1个条件变量 + 2个计数器 |
| **互斥控制** | 隐式（P/V原子性） | 自动（管程机制） |
| **代码行数** | ~5行 | ~15行（含统计） |
| **可读性** | 简洁 | 更清晰 |
| **扩展性** | 较难 | 容易 |

### PV操作版本
```
P(seats);
read_books();
V(seats);
```

### 管程版本
```
monitor.enter();
read_books();
monitor.leave();
```

## 正确性验证

### 1. 互斥性
- ✓ 管程自动保证互斥
- ✓ 同一时刻只有一个进程在管程内执行

### 2. 同步性
- ✓ 满员时读者阻塞在 `seat_available.wait()`
- ✓ 有人离开时通过 `seat_available.signal()` 唤醒

### 3. 资源约束
- ✓ `available_seats + current_readers = CAPACITY = 100`
- ✓ 因此 `current_readers ≤ 100`

### 4. 无死锁
- ✓ 只有一个条件变量，不会循环等待
- ✓ wait()会释放锁，不会持锁等待

### 5. 无饥饿
- ✓ signal()按FIFO唤醒等待队列

## 管程的优势

### 1. 封装性
```
// 数据和操作封装在一起
monitor ReadingRoomMonitor {
    private int available_seats;  // 数据隐藏
    public procedure enter();     // 接口暴露
    public procedure leave();
}
```

### 2. 自动互斥
```
// 不需要手动加锁
procedure enter() {
    // 进入时自动获取锁
    available_seats--;
    // 退出时自动释放锁
}
```

### 3. 清晰的条件等待
```
// 条件不满足时等待
while (available_seats == 0) {
    seat_available.wait();  // 语义清晰
}
```

### 4. 易于扩展

#### 添加VIP功能
```
monitor ReadingRoomMonitor {
    int available_seats = 100;
    condition vip_queue;
    condition normal_queue;
    int vip_waiting = 0;
    
    procedure vip_enter() {
        while (available_seats == 0) {
            vip_waiting++;
            vip_queue.wait();
            vip_waiting--;
        }
        available_seats--;
    }
    
    procedure normal_enter() {
        while (available_seats == 0 || vip_waiting > 0) {
            normal_queue.wait();
        }
        available_seats--;
    }
    
    procedure leave() {
        available_seats++;
        if (vip_waiting > 0) {
            vip_queue.signal();
        } else {
            normal_queue.signal();
        }
    }
}
```

#### 添加统计功能
```
monitor ReadingRoomMonitor {
    int total_visits = 0;
    int total_reading_time = 0;
    
    procedure enter() {
        // ... 原有逻辑 ...
        total_visits++;
    }
    
    procedure get_statistics() {
        return {
            total_visits: total_visits,
            avg_time: total_reading_time / total_visits,
            current_readers: current_readers
        };
    }
}
```

## Python实现示例

```python
import threading

class ReadingRoomMonitor:
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.available_seats = capacity
        self.current_readers = 0
        
        # 条件变量（自带锁）
        self.condition = threading.Condition()
    
    def enter(self):
        """进入阅览室"""
        with self.condition:  # 自动获取锁
            # 等待有座位
            while self.available_seats == 0:
                self.condition.wait()
            
            # 获得座位
            self.available_seats -= 1
            self.current_readers += 1
            print(f"读者进入，当前人数: {self.current_readers}")
    
    def leave(self):
        """离开阅览室"""
        with self.condition:  # 自动获取锁
            # 释放座位
            self.available_seats += 1
            self.current_readers -= 1
            print(f"读者离开，当前人数: {self.current_readers}")
            
            # 通知等待的读者
            self.condition.notify()
    
    def get_status(self):
        """获取状态"""
        with self.condition:
            return {
                'available': self.available_seats,
                'occupied': self.current_readers,
                'capacity': self.capacity
            }

# 读者线程
def reader_thread(monitor, reader_id, times):
    for i in range(times):
        time.sleep(random.uniform(0.1, 0.5))
        monitor.enter()
        
        time.sleep(random.uniform(0.2, 0.8))  # 阅读
        
        monitor.leave()
```

## 总结

### 管程实现特点
1. **封装性强**：数据和操作封装在一起
2. **自动互斥**：不需要手动管理锁
3. **语义清晰**：条件等待意图明确
4. **易于扩展**：添加功能不影响原有逻辑

### 适用场景
- 需要复杂状态管理
- 需要多个条件变量
- 需要统计和监控
- 团队协作开发

### 与PV操作对比
- **PV操作**：简洁，适合简单场景
- **管程**：结构化，适合复杂场景

对于阅览室这个简单问题，PV操作更简洁；但如果需要扩展功能（VIP、统计等），管程更有优势。

# 水果盘问题 - 管程实现

## 问题描述

桌上有一个盘子，容量为2（最多能放2个水果）。爸爸专门向盘子中放苹果，妈妈专门向盘子中放橘子，儿子专门等待吃盘子中的橘子，女儿专门等待吃盘子中的苹果。

## 管程设计

### 管程结构

```
monitor FruitPlateMonitor {
    // 共享数据
    int capacity = 2;              // 盘子容量
    int apple_count = 0;           // 盘子中的苹果数
    int orange_count = 0;          // 盘子中的橘子数
    
    // 条件变量
    condition plate_not_full;      // 盘子未满
    condition apple_available;     // 有苹果可取
    condition orange_available;    // 有橘子可取
    
    // 操作方法
    procedure put_apple();         // 放苹果
    procedure put_orange();        // 放橘子
    procedure take_apple();        // 取苹果
    procedure take_orange();       // 取橘子
}
```

## 伪代码实现

### 完整管程定义

```
monitor FruitPlateMonitor {
    // === 共享数据 ===
    const int CAPACITY = 2;
    int apple_count = 0;
    int orange_count = 0;
    
    // === 条件变量 ===
    condition plate_not_full;
    condition apple_available;
    condition orange_available;
    
    // === 辅助函数 ===
    function is_full() {
        return (apple_count + orange_count) >= CAPACITY;
    }
    
    function get_total_count() {
        return apple_count + orange_count;
    }
    
    // === 放苹果（爸爸调用）===
    procedure put_apple() {
        // 等待盘子有空位
        while (is_full()) {
            plate_not_full.wait();
        }
        
        // 放入苹果
        apple_count++;
        print("爸爸放入苹果，盘子:", apple_count, "个苹果,", orange_count, "个橘子");
        
        // 通知女儿有苹果了
        apple_available.signal();
    }
    
    // === 放橘子（妈妈调用）===
    procedure put_orange() {
        // 等待盘子有空位
        while (is_full()) {
            plate_not_full.wait();
        }
        
        // 放入橘子
        orange_count++;
        print("妈妈放入橘子，盘子:", apple_count, "个苹果,", orange_count, "个橘子");
        
        // 通知儿子有橘子了
        orange_available.signal();
    }
    
    // === 取苹果（女儿调用）===
    procedure take_apple() {
        // 等待有苹果
        while (apple_count == 0) {
            apple_available.wait();
        }
        
        // 取出苹果
        apple_count--;
        print("女儿取出苹果，盘子:", apple_count, "个苹果,", orange_count, "个橘子");
        
        // 通知爸爸/妈妈盘子有空位了
        plate_not_full.signal();
    }
    
    // === 取橘子（儿子调用）===
    procedure take_orange() {
        // 等待有橘子
        while (orange_count == 0) {
            orange_available.wait();
        }
        
        // 取出橘子
        orange_count--;
        print("儿子取出橘子，盘子:", apple_count, "个苹果,", orange_count, "个橘子");
        
        // 通知爸爸/妈妈盘子有空位了
        plate_not_full.signal();
    }
    
    // === 获取状态 ===
    procedure get_status() {
        return {
            apples: apple_count,
            oranges: orange_count,
            total: get_total_count(),
            capacity: CAPACITY,
            available: CAPACITY - get_total_count()
        };
    }
}
```

### 进程实现

```
// 爸爸进程
Father() {
    while (true) {
        prepare_apple();
        FruitPlateMonitor.put_apple();
    }
}

// 妈妈进程
Mother() {
    while (true) {
        prepare_orange();
        FruitPlateMonitor.put_orange();
    }
}

// 女儿进程
Daughter() {
    while (true) {
        FruitPlateMonitor.take_apple();
        eat_apple();
    }
}

// 儿子进程
Son() {
    while (true) {
        FruitPlateMonitor.take_orange();
        eat_orange();
    }
}
```

## 流程分析

### 爸爸放苹果流程

```
Father调用 put_apple()
    ↓
[自动获取管程锁]
    ↓
检查 is_full()?
    ├─ 是：plate_not_full.wait()
    │      ├─ 释放管程锁
    │      ├─ 进入等待队列
    │      └─ 被唤醒后重新获取锁，继续循环
    └─ 否：继续
    ↓
apple_count++
    ↓
apple_available.signal()
    └─ 唤醒等待苹果的女儿
    ↓
[自动释放管程锁]
    ↓
返回
```

### 女儿取苹果流程

```
Daughter调用 take_apple()
    ↓
[自动获取管程锁]
    ↓
检查 apple_count == 0?
    ├─ 是：apple_available.wait()
    │      ├─ 释放管程锁
    │      ├─ 进入等待队列
    │      └─ 被唤醒后重新获取锁，继续循环
    └─ 否：继续
    ↓
apple_count--
    ↓
plate_not_full.signal()
    └─ 唤醒等待空位的爸爸/妈妈
    ↓
[自动释放管程锁]
    ↓
返回
```

## 管程 vs PV操作对比

### 代码对比

| 方面 | PV操作 | 管程 |
|------|--------|------|
| **信号量/变量** | 3个信号量 | 3个条件变量 + 2个计数器 |
| **互斥控制** | 隐式（通过empty） | 自动（管程机制） |
| **状态管理** | 分散在信号量中 | 集中在管程内 |
| **可读性** | 需要理解不变式 | 逻辑清晰直观 |
| **扩展性** | 较难 | 容易 |

### PV操作版本
```
P(empty);
put_apple();
V(apple);
```

### 管程版本
```
monitor.put_apple();  // 内部自动处理所有同步
```

## 正确性验证

### 1. 互斥性
- ✓ 管程自动保证互斥
- ✓ 同一时刻只有一个进程在管程内执行

### 2. 同步性
- ✓ 盘子满时生产者阻塞在 `plate_not_full.wait()`
- ✓ 没有苹果时女儿阻塞在 `apple_available.wait()`
- ✓ 没有橘子时儿子阻塞在 `orange_available.wait()`

### 3. 资源约束
- ✓ `apple_count + orange_count ≤ CAPACITY = 2`
- ✓ 通过 `is_full()` 检查保证

### 4. 配对正确性
- ✓ 女儿只能取苹果（调用 `take_apple()`）
- ✓ 儿子只能取橘子（调用 `take_orange()`）

### 5. 无死锁
- ✓ 条件变量的wait()会释放锁
- ✓ 不会持锁等待

### 6. 无饥饿
- ✓ signal()按FIFO唤醒等待队列

## 管程的优势

### 1. 封装性

```
// 所有状态和操作封装在一起
monitor FruitPlateMonitor {
    private int apple_count;      // 数据隐藏
    private int orange_count;
    
    public procedure put_apple(); // 接口暴露
    public procedure take_apple();
    // ...
}
```

### 2. 清晰的条件等待

```
// PV操作：需要理解信号量含义
P(apple);  // 这是在等待苹果吗？还是在申请资源？

// 管程：语义清晰
while (apple_count == 0) {
    apple_available.wait();  // 明确：等待苹果可用
}
```

### 3. 集中的状态管理

```
// 可以随时查询状态
status = monitor.get_status();
print("盘子中有", status.apples, "个苹果,", status.oranges, "个橘子");
```

### 4. 易于扩展

#### 添加第三种水果（香蕉）

```
monitor FruitPlateMonitor {
    int apple_count = 0;
    int orange_count = 0;
    int banana_count = 0;  // 新增
    
    condition banana_available;  // 新增
    
    procedure put_banana() {
        while (is_full()) {
            plate_not_full.wait();
        }
        banana_count++;
        banana_available.signal();
    }
    
    procedure take_banana() {
        while (banana_count == 0) {
            banana_available.wait();
        }
        banana_count--;
        plate_not_full.signal();
    }
    
    function is_full() {
        return (apple_count + orange_count + banana_count) >= CAPACITY;
    }
}
```

#### 添加优先级（VIP可以插队）

```
monitor FruitPlateMonitor {
    int vip_waiting = 0;
    condition vip_queue;
    condition normal_queue;
    
    procedure vip_put_apple() {
        vip_waiting++;
        while (is_full()) {
            vip_queue.wait();
        }
        vip_waiting--;
        apple_count++;
        apple_available.signal();
    }
    
    procedure normal_put_apple() {
        while (is_full() || vip_waiting > 0) {
            normal_queue.wait();
        }
        apple_count++;
        apple_available.signal();
    }
    
    procedure take_apple() {
        while (apple_count == 0) {
            apple_available.wait();
        }
        apple_count--;
        
        // 优先唤醒VIP
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
monitor FruitPlateMonitor {
    // 统计数据
    int total_apples_produced = 0;
    int total_apples_consumed = 0;
    int total_oranges_produced = 0;
    int total_oranges_consumed = 0;
    
    procedure put_apple() {
        while (is_full()) {
            plate_not_full.wait();
        }
        apple_count++;
        total_apples_produced++;  // 统计
        apple_available.signal();
    }
    
    procedure take_apple() {
        while (apple_count == 0) {
            apple_available.wait();
        }
        apple_count--;
        total_apples_consumed++;  // 统计
        plate_not_full.signal();
    }
    
    procedure get_statistics() {
        return {
            apples_produced: total_apples_produced,
            apples_consumed: total_apples_consumed,
            oranges_produced: total_oranges_produced,
            oranges_consumed: total_oranges_consumed,
            current_apples: apple_count,
            current_oranges: orange_count
        };
    }
}
```

## Python实现示例

```python
import threading
import time
import random

class FruitPlateMonitor:
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.apple_count = 0
        self.orange_count = 0
        
        # 条件变量（自带锁）
        self.condition = threading.Condition()
    
    def is_full(self):
        """检查盘子是否满"""
        return (self.apple_count + self.orange_count) >= self.capacity
    
    def put_apple(self):
        """放苹果（爸爸调用）"""
        with self.condition:
            # 等待盘子有空位
            while self.is_full():
                self.condition.wait()
            
            # 放入苹果
            self.apple_count += 1
            print(f"爸爸放入苹果，盘子: {self.apple_count}🍎 {self.orange_count}🍊")
            
            # 通知女儿
            self.condition.notify_all()
    
    def put_orange(self):
        """放橘子（妈妈调用）"""
        with self.condition:
            # 等待盘子有空位
            while self.is_full():
                self.condition.wait()
            
            # 放入橘子
            self.orange_count += 1
            print(f"妈妈放入橘子，盘子: {self.apple_count}🍎 {self.orange_count}🍊")
            
            # 通知儿子
            self.condition.notify_all()
    
    def take_apple(self):
        """取苹果（女儿调用）"""
        with self.condition:
            # 等待有苹果
            while self.apple_count == 0:
                self.condition.wait()
            
            # 取出苹果
            self.apple_count -= 1
            print(f"女儿取出苹果，盘子: {self.apple_count}🍎 {self.orange_count}🍊")
            
            # 通知爸爸/妈妈
            self.condition.notify_all()
    
    def take_orange(self):
        """取橘子（儿子调用）"""
        with self.condition:
            # 等待有橘子
            while self.orange_count == 0:
                self.condition.wait()
            
            # 取出橘子
            self.orange_count -= 1
            print(f"儿子取出橘子，盘子: {self.apple_count}🍎 {self.orange_count}🍊")
            
            # 通知爸爸/妈妈
            self.condition.notify_all()
    
    def get_status(self):
        """获取状态"""
        with self.condition:
            return {
                'apples': self.apple_count,
                'oranges': self.orange_count,
                'total': self.apple_count + self.orange_count,
                'capacity': self.capacity
            }

# 进程线程
def father_thread(monitor, times):
    for i in range(times):
        time.sleep(random.uniform(0.1, 0.5))
        monitor.put_apple()

def mother_thread(monitor, times):
    for i in range(times):
        time.sleep(random.uniform(0.1, 0.5))
        monitor.put_orange()

def daughter_thread(monitor, times):
    for i in range(times):
        time.sleep(random.uniform(0.1, 0.5))
        monitor.take_apple()

def son_thread(monitor, times):
    for i in range(times):
        time.sleep(random.uniform(0.1, 0.5))
        monitor.take_orange()

# 测试
if __name__ == "__main__":
    monitor = FruitPlateMonitor(capacity=2)
    
    threads = [
        threading.Thread(target=father_thread, args=(monitor, 5)),
        threading.Thread(target=mother_thread, args=(monitor, 5)),
        threading.Thread(target=daughter_thread, args=(monitor, 5)),
        threading.Thread(target=son_thread, args=(monitor, 5))
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("\n最终状态:", monitor.get_status())
```

## 关键设计决策

### 为什么使用notify_all()而不是notify()？

```python
# 使用notify()的问题
def put_apple(self):
    with self.condition:
        while self.is_full():
            self.condition.wait()
        self.apple_count += 1
        self.condition.notify()  # 只唤醒一个

# 问题：可能唤醒了妈妈，但妈妈发现盘子满了又睡了
# 而女儿还在等待苹果
```

```python
# 使用notify_all()
def put_apple(self):
    with self.condition:
        while self.is_full():
            self.condition.wait()
        self.apple_count += 1
        self.condition.notify_all()  # 唤醒所有

# 好处：女儿会被唤醒并取走苹果
# 代价：可能唤醒不必要的线程（但它们会再次wait）
```

**优化方案**：使用多个条件变量（如伪代码中的设计）

### 为什么使用while而不是if？

```python
# 错误：使用if
def take_apple(self):
    with self.condition:
        if self.apple_count == 0:  # 错误！
            self.condition.wait()
        self.apple_count -= 1

# 问题：虚假唤醒（spurious wakeup）
# 被唤醒时apple_count可能仍然是0
```

```python
# 正确：使用while
def take_apple(self):
    with self.condition:
        while self.apple_count == 0:  # 正确！
            self.condition.wait()
        self.apple_count -= 1

# 好处：重新检查条件，防止虚假唤醒
```

## 总结

### 管程实现特点
1. **封装性强**：状态和操作封装在一起
2. **语义清晰**：条件等待意图明确
3. **易于扩展**：添加功能不影响原有逻辑
4. **便于调试**：可以随时查询状态

### 与PV操作对比

| 维度 | PV操作 | 管程 |
|------|--------|------|
| 抽象层次 | 低级 | 高级 |
| 代码量 | 少 | 多 |
| 可读性 | 需要理解不变式 | 直观 |
| 可维护性 | 较难 | 容易 |
| 扩展性 | 困难 | 容易 |

### 适用场景
- **PV操作**：简单问题，性能敏感
- **管程**：复杂问题，需要扩展和维护

水果盘问题虽然可以用PV操作简洁实现，但管程版本在扩展性和可维护性上更有优势。

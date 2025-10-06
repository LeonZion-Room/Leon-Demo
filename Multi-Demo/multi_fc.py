#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单易用的Python多线程实现
基于Python原生threading库
"""

import threading
import time
import queue
import inspect
from typing import Callable, Any, List, Optional, Dict, Union
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==================== 简洁接口 ====================

def thread_fc(func: Callable, *args, **kwargs) -> Any:
    """
    超简洁的多线程函数调用接口 - 直接传递函数变量
    
    Args:
        func: 函数变量（可调用对象）
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果
        
    Examples:
        # 使用位置参数
        result = thread_fc(test_simple_calc, 5, 3)
        
        # 使用关键字参数
        result = thread_fc(test_flexible_params, a=1, b=2, c=30)
        
        # 混合使用
        result = thread_fc(test_flexible_params, 1, 2, d=40)
        
        # 使用lambda函数
        result = thread_fc(lambda x, y: x + y, 10, 20)
    """
    # 检查是否为可调用对象
    if not callable(func):
        raise ValueError(f"第一个参数必须是可调用的函数，得到的是: {type(func)}")
    
    # 创建线程执行函数
    result_container = {'result': None, 'error': None}
    
    def thread_wrapper():
        try:
            result_container['result'] = func(*args, **kwargs)
        except Exception as e:
            result_container['error'] = e
    
    # 启动线程并等待完成
    thread = threading.Thread(target=thread_wrapper)
    thread.start()
    thread.join()
    
    # 检查是否有错误
    if result_container['error']:
        raise result_container['error']
    
    return result_container['result']


def thread_fc_async(func: Callable, *args, **kwargs) -> threading.Thread:
    """
    异步版本的多线程函数调用接口 - 直接传递函数变量
    
    Args:
        func: 函数变量（可调用对象）
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Thread对象，可以通过join()等待完成，通过get_result()获取结果
        
    Examples:
        # 使用位置参数
        thread = thread_fc_async(test_simple_calc, 7, 8)
        
        # 使用关键字参数
        thread = thread_fc_async(test_flexible_params, a=1, b=2, c=30)
        
        # 使用lambda函数
        thread = thread_fc_async(lambda x: x * 2, 50)
        
        # 等待完成并获取结果
        thread.join()
        result = thread.get_result()
    """
    # 检查是否为可调用对象
    if not callable(func):
        raise ValueError(f"第一个参数必须是可调用的函数，得到的是: {type(func)}")
    
    # 创建线程执行函数
    result_container = {'result': None, 'error': None}
    
    def thread_wrapper():
        try:
            result_container['result'] = func(*args, **kwargs)
        except Exception as e:
            result_container['error'] = e
    
    # 创建并启动线程
    thread = threading.Thread(target=thread_wrapper)
    
    # 添加result属性和error属性
    def get_result():
        thread.join()  # 确保线程完成
        if result_container['error']:
            raise result_container['error']
        return result_container['result']
    
    thread.result = property(lambda self: get_result())
    thread.get_result = get_result
    thread.start()
    
    return thread


class SimpleMultiThread:
    """简单的多线程执行器类"""
    
    def __init__(self, max_workers: int = 4):
        """
        初始化多线程执行器
        
        Args:
            max_workers: 最大工作线程数，默认为4
        """
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        
    def run_parallel(self, func: Callable, args_list: List[tuple], 
                    timeout: Optional[float] = None) -> List[Any]:
        """
        并行执行函数
        
        Args:
            func: 要执行的函数
            args_list: 参数列表，每个元素是一个tuple，包含函数的参数
            timeout: 超时时间（秒），None表示不设置超时
            
        Returns:
            结果列表
        """
        self.results.clear()
        self.errors.clear()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_args = {
                executor.submit(func, *args): args 
                for args in args_list
            }
            
            # 收集结果
            for future in as_completed(future_to_args, timeout=timeout):
                args = future_to_args[future]
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as exc:
                    error_info = {
                        'args': args,
                        'error': str(exc),
                        'exception': exc
                    }
                    self.errors.append(error_info)
                    
        return self.results
    
    def run_async(self, func: Callable, *args, **kwargs) -> threading.Thread:
        """
        异步执行单个函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Thread对象
        """
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    
    def get_results(self) -> List[Any]:
        """获取执行结果"""
        return self.results.copy()
    
    def get_errors(self) -> List[Dict]:
        """获取执行错误"""
        return self.errors.copy()
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0


class ThreadSafeCounter:
    """线程安全的计数器"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, step: int = 1) -> int:
        """增加计数"""
        with self._lock:
            self._value += step
            return self._value
    
    def decrement(self, step: int = 1) -> int:
        """减少计数"""
        with self._lock:
            self._value -= step
            return self._value
    
    def get_value(self) -> int:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def reset(self, value: int = 0):
        """重置计数器"""
        with self._lock:
            self._value = value


class ThreadSafeQueue:
    """线程安全的队列包装器"""
    
    def __init__(self, maxsize: int = 0):
        self._queue = queue.Queue(maxsize=maxsize)
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """放入元素"""
        self._queue.put(item, block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """获取元素"""
        return self._queue.get(block=block, timeout=timeout)
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()
    
    def size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()


# ==================== 示例代码 ====================

def example_task(task_id: int, duration: float = 1.0) -> str:
    """示例任务函数"""
    print(f"任务 {task_id} 开始执行...")
    time.sleep(duration)
    result = f"任务 {task_id} 完成，耗时 {duration} 秒"
    print(result)
    return result


def test_flexible_params(a, b, c=10, d=20):
    """测试函数：支持位置参数和关键字参数"""
    result = f"a={a}, b={b}, c={c}, d={d}, sum={a+b+c+d}"
    print(f"  执行结果: {result}")
    return result

def test_simple_calc(x, y):
    """简单计算函数"""
    result = x * y + 100
    print(f"  计算结果: {x} * {y} + 100 = {result}")
    return result

def demo_thread_fc():
    """演示thread_fc的简洁用法 - 直接传递函数变量"""
    print("=== thread_fc 简洁接口演示 (函数变量传递) ===")
    
    # 1. 使用位置参数
    print("\n1. 使用位置参数:")
    print("  调用: thread_fc(test_simple_calc, 5, 3)")
    result1 = thread_fc(test_simple_calc, 5, 3)
    print(f"  返回值: {result1}")
    
    # 2. 使用关键字参数
    print("\n2. 使用关键字参数:")
    print("  调用: thread_fc(test_flexible_params, a=1, b=2, c=30)")
    result2 = thread_fc(test_flexible_params, a=1, b=2, c=30)
    print(f"  返回值: {result2}")
    
    # 3. 混合使用位置参数和关键字参数
    print("\n3. 混合使用位置参数和关键字参数:")
    print("  调用: thread_fc(test_flexible_params, 1, 2, d=40)")
    result3 = thread_fc(test_flexible_params, 1, 2, d=40)
    print(f"  返回值: {result3}")
    
    # 4. 使用lambda函数
    print("\n4. 使用lambda函数:")
    print("  调用: thread_fc(lambda x, y: x * y + 100, 6, 7)")
    result4 = thread_fc(lambda x, y: x * y + 100, 6, 7)
    print(f"  返回值: {result4}")
    
    # 5. 使用内置函数
    print("\n5. 使用内置函数:")
    print("  调用: thread_fc(max, [1, 5, 3, 9, 2])")
    result5 = thread_fc(max, [1, 5, 3, 9, 2])
    print(f"  返回值: {result5}")
    
    # 6. 异步调用示例
    print("\n6. 异步调用示例:")
    print("  调用: thread_fc_async(test_simple_calc, 7, 8)")
    thread1 = thread_fc_async(test_simple_calc, 7, 8)
    print("  异步任务已启动，继续执行其他代码...")
    time.sleep(0.5)
    print("  等待异步任务完成...")
    result6 = thread1.get_result()
    print(f"  异步返回值: {result6}")
    
    # 7. 异步lambda函数
    print("\n7. 异步lambda函数:")
    print("  调用: thread_fc_async(lambda x: x ** 2, 12)")
    thread2 = thread_fc_async(lambda x: x ** 2, 12)
    result7 = thread2.get_result()
    print(f"  异步返回值: {result7}")
    
    print("\nthread_fc 函数变量传递演示完成!\n")


def example_calculation(x: int, y: int) -> int:
    """示例计算函数"""
    time.sleep(0.5)  # 模拟计算时间
    result = x * y + x + y
    print(f"计算 {x} * {y} + {x} + {y} = {result}")
    return result


def demo_parallel_execution():
    """演示并行执行"""
    print("=== 并行执行演示 ===")
    
    # 创建多线程执行器
    mt = SimpleMultiThread(max_workers=3)
    
    # 准备任务参数
    task_args = [
        (1, 1.0),
        (2, 1.5),
        (3, 0.8),
        (4, 1.2),
        (5, 0.5)
    ]
    
    start_time = time.time()
    
    # 并行执行任务
    results = mt.run_parallel(example_task, task_args)
    
    end_time = time.time()
    
    print(f"\n所有任务完成，总耗时: {end_time - start_time:.2f} 秒")
    print(f"成功执行 {len(results)} 个任务")
    
    if mt.has_errors():
        print(f"发生 {len(mt.get_errors())} 个错误:")
        for error in mt.get_errors():
            print(f"  参数 {error['args']}: {error['error']}")


def demo_calculation():
    """演示并行计算"""
    print("\n=== 并行计算演示 ===")
    
    mt = SimpleMultiThread(max_workers=4)
    
    # 准备计算参数
    calc_args = [
        (2, 3),
        (4, 5),
        (6, 7),
        (8, 9),
        (10, 11)
    ]
    
    start_time = time.time()
    results = mt.run_parallel(example_calculation, calc_args)
    end_time = time.time()
    
    print(f"\n计算结果: {results}")
    print(f"计算耗时: {end_time - start_time:.2f} 秒")


def demo_async_execution():
    """演示异步执行"""
    print("\n=== 异步执行演示 ===")
    
    mt = SimpleMultiThread()
    
    # 启动异步任务
    threads = []
    for i in range(3):
        thread = mt.run_async(example_task, i+1, 1.0)
        threads.append(thread)
    
    print("异步任务已启动，主线程继续执行其他工作...")
    time.sleep(0.5)
    print("主线程工作完成，等待异步任务...")
    
    # 等待所有异步任务完成
    for thread in threads:
        thread.join()
    
    print("所有异步任务完成")


def demo_thread_safe_utilities():
    """演示线程安全工具"""
    print("\n=== 线程安全工具演示 ===")
    
    # 线程安全计数器
    counter = ThreadSafeCounter()
    
    def increment_counter():
        for _ in range(1000):
            counter.increment()
    
    # 启动多个线程同时增加计数器
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=increment_counter)
        thread.start()
        threads.append(thread)
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print(f"计数器最终值: {counter.get_value()} (期望值: 5000)")
    
    # 线程安全队列
    safe_queue = ThreadSafeQueue()
    
    def producer(queue_obj, items):
        for item in items:
            queue_obj.put(f"数据-{item}")
            time.sleep(0.1)
    
    def consumer(queue_obj, name):
        while True:
            try:
                item = queue_obj.get(timeout=1.0)
                print(f"消费者 {name} 处理: {item}")
            except:
                break
    
    # 启动生产者和消费者
    producer_thread = threading.Thread(target=producer, args=(safe_queue, range(5)))
    consumer_thread1 = threading.Thread(target=consumer, args=(safe_queue, "A"))
    consumer_thread2 = threading.Thread(target=consumer, args=(safe_queue, "B"))
    
    producer_thread.start()
    consumer_thread1.start()
    consumer_thread2.start()
    
    producer_thread.join()
    time.sleep(2)  # 等待消费者处理完成


if __name__ == "__main__":
    print("Python 多线程演示程序")
    print("=" * 50)
    
    # 最简实例
    def fc_test(a,b,c,d):
        return a+b+c+d
    result1 = thread_fc(fc_test, 5, 3, 2,6)
    print(f"  返回值: {result1}")


 

    if 0:
        # 首先演示最简洁的thread_fc接口
        demo_thread_fc()

        # 测试fc_test函数
        result = thread_fc('fc_test',{'a':1,'b':2,'c':3})
        print(f"fc_test(1,2,3) = {result}")

        # 然后演示其他高级功能
        demo_parallel_execution()
        demo_calculation()
        demo_async_execution()
        demo_thread_safe_utilities()
        
        print("\n" + "=" * 50)
        print("演示完成！")
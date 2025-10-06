#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Redis 字符类型的字典存储和读取实现
作者: Python 程序员
功能: 使用 Redis 字符串类型存储和读取 Python 字典
"""

import redis
import json
import logging
from typing import Dict, Any, Optional, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RedisStringDict:
    """
    基于 Redis 字符串类型的字典存储类
    
    特点:
    - 所有字典数据都通过 JSON 序列化为字符串存储在 Redis 中
    - 支持字典的基本操作：存储、读取、删除、更新等
    - 使用 Redis 字符串类型作为存储介质
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 6379, db: int = 0, 
                 decode_responses: bool = True, prefix: str = 'dict:'):
        """
        初始化 Redis 连接
        
        Args:
            host: Redis 服务器地址
            port: Redis 服务器端口
            db: Redis 数据库编号
            decode_responses: 是否自动解码响应为字符串
            prefix: 键名前缀，用于区分不同类型的数据
        """
        self.prefix = prefix
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=decode_responses
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"成功连接到 Redis 服务器 {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"无法连接到 Redis 服务器: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis 连接初始化失败: {e}")
            raise
    
    def _get_full_key(self, key: str) -> str:
        """
        获取完整的 Redis 键名（添加前缀）
        
        Args:
            key: 原始键名
            
        Returns:
            完整的键名
        """
        return f"{self.prefix}{key}"
    
    def _serialize_dict(self, data: Dict[str, Any]) -> str:
        """
        将字典序列化为 JSON 字符串
        
        Args:
            data: 要序列化的字典
            
        Returns:
            JSON 字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            logger.error(f"字典序列化失败: {e}")
            raise ValueError(f"无法序列化字典: {e}")
    
    def _deserialize_dict(self, json_str: str) -> Dict[str, Any]:
        """
        将 JSON 字符串反序列化为字典
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            反序列化后的字典
        """
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"字典反序列化失败: {e}")
            raise ValueError(f"无法反序列化字符串为字典: {e}")
    
    def set_dict(self, key: str, data: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """
        存储字典到 Redis（使用字符串类型）
        
        Args:
            key: 存储键名
            data: 要存储的字典
            ex: 过期时间（秒），None 表示不过期
            
        Returns:
            是否存储成功
        """
        try:
            full_key = self._get_full_key(key)
            json_str = self._serialize_dict(data)
            
            result = self.redis_client.set(full_key, json_str, ex=ex)
            
            if result:
                logger.info(f"成功存储字典到键 '{key}'，数据大小: {len(json_str)} 字符")
                return True
            else:
                logger.warning(f"存储字典到键 '{key}' 失败")
                return False
                
        except Exception as e:
            logger.error(f"存储字典失败: {e}")
            return False
    
    def get_dict(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从 Redis 读取字典（从字符串类型）
        
        Args:
            key: 存储键名
            
        Returns:
            读取到的字典，如果不存在则返回 None
        """
        try:
            full_key = self._get_full_key(key)
            json_str = self.redis_client.get(full_key)
            
            if json_str is None:
                logger.info(f"键 '{key}' 不存在")
                return None
            
            data = self._deserialize_dict(json_str)
            logger.info(f"成功读取键 '{key}' 的字典数据")
            return data
            
        except Exception as e:
            logger.error(f"读取字典失败: {e}")
            return None
    
    def update_dict(self, key: str, updates: Dict[str, Any]) -> bool:
        """
        更新字典中的部分数据
        
        Args:
            key: 存储键名
            updates: 要更新的键值对
            
        Returns:
            是否更新成功
        """
        try:
            # 先读取现有数据
            existing_data = self.get_dict(key)
            if existing_data is None:
                logger.info(f"键 '{key}' 不存在，创建新字典")
                existing_data = {}
            
            # 更新数据
            existing_data.update(updates)
            
            # 保存更新后的数据
            result = self.set_dict(key, existing_data)
            if result:
                logger.info(f"成功更新键 '{key}' 的字典数据")
            return result
            
        except Exception as e:
            logger.error(f"更新字典失败: {e}")
            return False
    
    def delete_dict(self, key: str) -> bool:
        """
        删除字典
        
        Args:
            key: 存储键名
            
        Returns:
            是否删除成功
        """
        try:
            full_key = self._get_full_key(key)
            result = self.redis_client.delete(full_key)
            
            if result > 0:
                logger.info(f"成功删除键 '{key}' 的字典数据")
                return True
            else:
                logger.info(f"键 '{key}' 不存在，无需删除")
                return False
                
        except Exception as e:
            logger.error(f"删除字典失败: {e}")
            return False
    
    def exists_dict(self, key: str) -> bool:
        """
        检查字典是否存在
        
        Args:
            key: 存储键名
            
        Returns:
            字典是否存在
        """
        try:
            full_key = self._get_full_key(key)
            result = self.redis_client.exists(full_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"检查字典存在性失败: {e}")
            return False
    
    def get_dict_keys(self, pattern: str = "*") -> list:
        """
        获取所有匹配模式的字典键名
        
        Args:
            pattern: 匹配模式，默认为所有键
            
        Returns:
            匹配的键名列表（去除前缀）
        """
        try:
            full_pattern = f"{self.prefix}{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            # 去除前缀
            result = [key[len(self.prefix):] for key in keys]
            logger.info(f"找到 {len(result)} 个匹配的字典键")
            return result
            
        except Exception as e:
            logger.error(f"获取字典键列表失败: {e}")
            return []
    
    def get_dict_size(self, key: str) -> int:
        """
        获取字典存储的字符串大小（字节数）
        
        Args:
            key: 存储键名
            
        Returns:
            字符串大小，如果不存在则返回 0
        """
        try:
            full_key = self._get_full_key(key)
            size = self.redis_client.strlen(full_key)
            return size
            
        except Exception as e:
            logger.error(f"获取字典大小失败: {e}")
            return 0
    
    def clear_all_dicts(self) -> int:
        """
        清除所有字典数据
        
        Returns:
            删除的键数量
        """
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                logger.info("没有找到要删除的字典数据")
                return 0
            
            result = self.redis_client.delete(*keys)
            logger.info(f"成功删除 {result} 个字典键")
            return result
            
        except Exception as e:
            logger.error(f"清除所有字典失败: {e}")
            return 0


def main():
    """
    测试函数 - 演示 RedisStringDict 的使用
    """
    print("=" * 60)
    print("Redis 字符串字典存储测试")
    print("=" * 60)
    
    try:
        # 创建 Redis 字典实例
        redis_dict = RedisStringDict()
        
        # 测试数据
        test_data = {
            "name": "张三",
            "age": 25,
            "city": "北京",
            "skills": ["Python", "Redis", "数据库"],
            "profile": {
                "education": "本科",
                "experience": 3
            }
        }
        
        print("\n1. 存储字典数据:")
        print(f"原始数据: {test_data}")
        success = redis_dict.set_dict("user:1001", test_data)
        print(f"存储结果: {'成功' if success else '失败'}")
        
        print("\n2. 读取字典数据:")
        retrieved_data = redis_dict.get_dict("user:1001")
        print(f"读取数据: {retrieved_data}")
        
        print("\n3. 更新字典数据:")
        updates = {"age": 26, "city": "上海", "department": "技术部"}
        success = redis_dict.update_dict("user:1001", updates)
        print(f"更新结果: {'成功' if success else '失败'}")
        
        print("\n4. 读取更新后的数据:")
        updated_data = redis_dict.get_dict("user:1001")
        print(f"更新后数据: {updated_data}")
        
        print("\n5. 检查字典存在性:")
        exists = redis_dict.exists_dict("user:1001")
        print(f"字典是否存在: {exists}")
        
        print("\n6. 获取字典大小:")
        size = redis_dict.get_dict_size("user:1001")
        print(f"字典存储大小: {size} 字节")
        
        print("\n7. 获取所有字典键:")
        keys = redis_dict.get_dict_keys()
        print(f"所有字典键: {keys}")
        
        print("\n8. 删除字典:")
        success = redis_dict.delete_dict("user:1001")
        print(f"删除结果: {'成功' if success else '失败'}")
        
        print("\n9. 验证删除:")
        final_data = redis_dict.get_dict("user:1001")
        print(f"删除后读取: {final_data}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
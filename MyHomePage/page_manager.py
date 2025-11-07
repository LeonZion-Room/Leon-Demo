"""
页面管理模块
实现类似语雀的多页面管理和组织功能
"""

import streamlit as st
import json
import os
from typing import Dict, List, Any
from components import ComponentManager, CardComponent, MarkdownComponent, ColumnComponent


class Page:
    """页面类"""
    def __init__(self, page_id: str, title: str = "新页面", description: str = ""):
        self.page_id = page_id
        self.title = title
        self.description = description
        self.component_manager = ComponentManager()
        self.created_at = None
        self.updated_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """从字典创建页面对象"""
        page = cls(data["page_id"], data["title"], data["description"])
        page.created_at = data.get("created_at")
        page.updated_at = data.get("updated_at")
        return page


class PageManager:
    """页面管理器"""
    def __init__(self):
        self.pages: Dict[str, Page] = {}
        self.current_page_id: str = None
        self.page_counter = 0
        self.load_pages()
    
    def create_page(self, title: str = "新页面", description: str = "") -> Page:
        """创建新页面"""
        self.page_counter += 1
        page_id = f"page_{self.page_counter}"
        page = Page(page_id, title, description)
        self.pages[page_id] = page
        
        # 如果是第一个页面，设为当前页面
        if self.current_page_id is None:
            self.current_page_id = page_id
        
        self.save_pages()
        return page
    
    def delete_page(self, page_id: str) -> bool:
        """删除页面"""
        if page_id in self.pages:
            del self.pages[page_id]
            
            # 如果删除的是当前页面，切换到第一个可用页面
            if self.current_page_id == page_id:
                if self.pages:
                    self.current_page_id = list(self.pages.keys())[0]
                else:
                    self.current_page_id = None
            
            self.save_pages()
            return True
        return False
    
    def get_current_page(self) -> Page:
        """获取当前页面"""
        if self.current_page_id and self.current_page_id in self.pages:
            return self.pages[self.current_page_id]
        
        # 如果没有当前页面，创建一个默认页面
        if not self.pages:
            return self.create_page("首页", "欢迎来到我的博客")
        
        # 设置第一个页面为当前页面
        self.current_page_id = list(self.pages.keys())[0]
        return self.pages[self.current_page_id]
    
    def switch_page(self, page_id: str) -> bool:
        """切换到指定页面"""
        if page_id in self.pages:
            self.current_page_id = page_id
            return True
        return False
    
    def get_page_list(self) -> List[Page]:
        """获取所有页面列表"""
        return list(self.pages.values())
    
    def save_pages(self):
        """保存页面信息到文件"""
        try:
            pages_data = {
                "current_page_id": self.current_page_id,
                "page_counter": self.page_counter,
                "pages": {pid: page.to_dict() for pid, page in self.pages.items()}
            }
            
            with open("pages_data.json", "w", encoding="utf-8") as f:
                json.dump(pages_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"保存页面数据失败: {e}")
    
    def load_pages(self):
        """从文件加载页面信息"""
        try:
            if os.path.exists("pages_data.json"):
                with open("pages_data.json", "r", encoding="utf-8") as f:
                    pages_data = json.load(f)
                
                self.current_page_id = pages_data.get("current_page_id")
                self.page_counter = pages_data.get("page_counter", 0)
                
                for pid, page_data in pages_data.get("pages", {}).items():
                    self.pages[pid] = Page.from_dict(page_data)
        except Exception as e:
            st.error(f"加载页面数据失败: {e}")


class EditMode:
    """编辑模式管理"""
    def __init__(self):
        self.is_edit_mode = False
        self.editing_component_id = None
    
    def toggle_edit_mode(self):
        """切换编辑模式"""
        self.is_edit_mode = not self.is_edit_mode
        if not self.is_edit_mode:
            self.editing_component_id = None
    
    def start_editing_component(self, component_id: str):
        """开始编辑指定组件"""
        self.editing_component_id = component_id
        self.is_edit_mode = True
    
    def stop_editing(self):
        """停止编辑"""
        self.editing_component_id = None
        self.is_edit_mode = False


# 全局实例
if 'page_manager' not in st.session_state:
    st.session_state.page_manager = PageManager()

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = EditMode()
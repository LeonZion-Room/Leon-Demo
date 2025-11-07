"""
个人博客平台核心组件模块
包含卡片单元、Markdown单元、分栏单元等组件
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import requests
from PIL import Image
from io import BytesIO


class ComponentBase:
    """组件基类"""
    def __init__(self, component_id: str):
        self.component_id = component_id
    
    def render(self):
        """渲染组件，子类需要实现此方法"""
        raise NotImplementedError


class CardComponent(ComponentBase):
    """卡片组件"""
    def __init__(self, component_id: str, title: str = "", description: str = "", 
                 image_url: str = "", link_url: str = "", style: str = "default"):
        super().__init__(component_id)
        self.title = title
        self.description = description
        self.image_url = image_url
        self.link_url = link_url
        self.style = style
    
    def render(self, edit_mode=False):
        """渲染卡片组件"""
        # 根据样式设置不同的布局
        if self.style == "vertical":
            self._render_vertical_card(edit_mode)
        elif self.style == "minimal":
            self._render_minimal_card(edit_mode)
        else:
            self._render_default_card(edit_mode)
    
    def _render_default_card(self, edit_mode=False):
        """渲染默认样式卡片"""
        with st.container():
            # 编辑模式下显示编辑按钮
            if edit_mode:
                col_edit, col_main = st.columns([1, 10])
                with col_edit:
                    if st.button("✏️", key=f"edit_{self.component_id}", help="编辑此卡片"):
                        self._show_edit_dialog()
                with col_main:
                    self._render_card_content()
            else:
                self._render_card_content()
    
    def _render_card_content(self):
        """渲染卡片内容"""
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if self.image_url:
                try:
                    # 尝试加载网络图片
                    if self.image_url.startswith(('http://', 'https://')):
                        response = requests.get(self.image_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, use_container_width=True)
                    else:
                        # 本地图片
                        st.image(self.image_url, use_container_width=True)
                except Exception as e:
                    st.error(f"图片加载失败: {e}")
                    st.image("https://via.placeholder.com/300x200?text=No+Image", 
                           use_container_width=True)
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image", 
                       use_container_width=True)
        
        with col2:
            if self.title:
                st.subheader(self.title)
            if self.description:
                st.write(self.description)
            if self.link_url:
                if st.button(f"查看详情", key=f"btn_{self.component_id}"):
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={self.link_url}">', 
                              unsafe_allow_html=True)
                    st.success(f"正在跳转到: {self.link_url}")
    
    def _render_vertical_card(self, edit_mode=False):
        """渲染垂直样式卡片"""
        with st.container():
            if edit_mode:
                col_edit, col_main = st.columns([1, 10])
                with col_edit:
                    if st.button("✏️", key=f"edit_{self.component_id}", help="编辑此卡片"):
                        self._show_edit_dialog()
                with col_main:
                    self._render_vertical_content()
            else:
                self._render_vertical_content()
    
    def _render_vertical_content(self):
        """渲染垂直卡片内容"""
        if self.image_url:
            try:
                if self.image_url.startswith(('http://', 'https://')):
                    response = requests.get(self.image_url)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, use_container_width=True)
                else:
                    st.image(self.image_url, use_container_width=True)
            except Exception as e:
                st.image("https://via.placeholder.com/300x200?text=No+Image", 
                       use_container_width=True)
        
        if self.title:
            st.subheader(self.title)
        if self.description:
            st.write(self.description)
        if self.link_url:
            if st.button(f"查看详情", key=f"btn_{self.component_id}"):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={self.link_url}">', 
                          unsafe_allow_html=True)
                st.success(f"正在跳转到: {self.link_url}")
    
    def _render_minimal_card(self, edit_mode=False):
        """渲染简约样式卡片"""
        with st.container():
            if edit_mode:
                col_edit, col_main = st.columns([1, 10])
                with col_edit:
                    if st.button("✏️", key=f"edit_{self.component_id}", help="编辑此卡片"):
                        self._show_edit_dialog()
                with col_main:
                    self._render_minimal_content()
            else:
                self._render_minimal_content()
    
    def _render_minimal_content(self):
        """渲染简约卡片内容"""
        if self.title:
            st.markdown(f"### {self.title}")
        if self.description:
            st.markdown(self.description)
        if self.link_url:
            st.markdown(f"[查看详情]({self.link_url})")
    
    def _show_edit_dialog(self):
        """显示编辑对话框"""
        with st.expander(f"编辑卡片: {self.title or '未命名'}", expanded=True):
            new_title = st.text_input("标题", value=self.title, key=f"edit_title_{self.component_id}")
            new_description = st.text_area("描述", value=self.description, key=f"edit_desc_{self.component_id}")
            new_image_url = st.text_input("图片URL", value=self.image_url, key=f"edit_img_{self.component_id}")
            new_link_url = st.text_input("链接URL", value=self.link_url, key=f"edit_link_{self.component_id}")
            new_style = st.selectbox("样式", ["default", "vertical", "minimal"], 
                                   index=["default", "vertical", "minimal"].index(self.style),
                                   key=f"edit_style_{self.component_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存", key=f"save_{self.component_id}"):
                    self.title = new_title
                    self.description = new_description
                    self.image_url = new_image_url
                    self.link_url = new_link_url
                    self.style = new_style
                    st.success("保存成功！")
                    st.rerun()
            with col2:
                if st.button("删除", key=f"delete_{self.component_id}"):
                    # 这里需要从组件管理器中删除
                    st.error("删除功能待实现")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "type": "card",
            "component_id": self.component_id,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "link_url": self.link_url,
            "style": self.style
        }


class MarkdownComponent(ComponentBase):
    """Markdown组件"""
    def __init__(self, component_id: str, content: str = ""):
        super().__init__(component_id)
        self.content = content
    
    def render(self, edit_mode=False):
        """渲染Markdown组件"""
        with st.container():
            if edit_mode:
                col_edit, col_main = st.columns([1, 10])
                with col_edit:
                    if st.button("✏️", key=f"edit_{self.component_id}", help="编辑此Markdown"):
                        self._show_edit_dialog()
                with col_main:
                    self._render_content()
            else:
                self._render_content()
    
    def _render_content(self):
        """渲染Markdown内容"""
        if self.content:
            st.markdown(self.content)
        else:
            st.info("请添加Markdown内容")
    
    def _show_edit_dialog(self):
        """显示编辑对话框"""
        with st.expander("编辑Markdown内容", expanded=True):
            new_content = st.text_area(
                "Markdown内容", 
                value=self.content, 
                height=300,
                key=f"edit_content_{self.component_id}",
                help="支持完整的Markdown语法"
            )
            
            # 实时预览
            if new_content:
                st.markdown("**预览效果：**")
                st.markdown(new_content)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存", key=f"save_md_{self.component_id}"):
                    self.content = new_content
                    st.success("保存成功！")
                    st.rerun()
            with col2:
                if st.button("删除", key=f"delete_md_{self.component_id}"):
                    st.error("删除功能待实现")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "type": "markdown",
            "component_id": self.component_id,
            "content": self.content
        }


class ColumnComponent(ComponentBase):
    """分栏组件"""
    def __init__(self, component_id: str, columns: int = 2):
        super().__init__(component_id)
        self.columns = columns
        self.components = [[] for _ in range(columns)]
    
    def add_component(self, component: ComponentBase, column_index: int = 0):
        """向指定列添加组件"""
        if 0 <= column_index < self.columns:
            self.components[column_index].append(component)
    
    def render(self, edit_mode=False):
        """渲染分栏组件"""
        with st.container():
            if edit_mode:
                col_edit, col_main = st.columns([1, 10])
                with col_edit:
                    if st.button("✏️", key=f"edit_{self.component_id}", help="编辑分栏"):
                        self._show_edit_dialog()
                with col_main:
                    self._render_columns(edit_mode)
            else:
                self._render_columns(edit_mode)
    
    def _render_columns(self, edit_mode=False):
        """渲染分栏内容"""
        cols = st.columns(self.columns)
        
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"**第 {i+1} 列**")
                for component in self.components[i]:
                    component.render(edit_mode)
                    st.markdown("---")  # 分隔线
                
                # 编辑模式下显示添加按钮
                if edit_mode:
                    if st.button(f"➕ 添加组件", key=f"add_to_col_{self.component_id}_{i}"):
                        st.info(f"请在左侧选择要添加到第{i+1}列的组件类型")
    
    def _show_edit_dialog(self):
        """显示编辑对话框"""
        with st.expander("编辑分栏设置", expanded=True):
            new_columns = st.slider("列数", min_value=2, max_value=4, value=self.columns, 
                                   key=f"edit_cols_{self.component_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存", key=f"save_col_{self.component_id}"):
                    if new_columns != self.columns:
                        # 调整列数
                        if new_columns > self.columns:
                            # 增加列
                            for _ in range(new_columns - self.columns):
                                self.components.append([])
                        else:
                            # 减少列，需要处理多余的组件
                            for i in range(new_columns, self.columns):
                                if self.components[i]:
                                    # 将多余列的组件移到最后一列
                                    self.components[new_columns-1].extend(self.components[i])
                            self.components = self.components[:new_columns]
                        
                        self.columns = new_columns
                    st.success("保存成功！")
                    st.rerun()
            with col2:
                if st.button("删除", key=f"delete_col_{self.component_id}"):
                    st.error("删除功能待实现")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "type": "column",
            "component_id": self.component_id,
            "columns": self.columns,
            "components": [[comp.to_dict() for comp in col_comps] for col_comps in self.components]
        }


class ComponentManager:
    """组件管理器"""
    def __init__(self):
        self.components: List[ComponentBase] = []
        self.component_counter = 0
    
    def add_card(self, title: str = "", description: str = "", 
                 image_url: str = "", link_url: str = "", style: str = "default") -> CardComponent:
        """添加卡片组件"""
        self.component_counter += 1
        card = CardComponent(f"card_{self.component_counter}", title, description, 
                           image_url, link_url, style)
        self.components.append(card)
        return card
    
    def add_markdown(self, content: str = "") -> MarkdownComponent:
        """添加Markdown组件"""
        self.component_counter += 1
        markdown = MarkdownComponent(f"markdown_{self.component_counter}", content)
        self.components.append(markdown)
        return markdown
    
    def add_column(self, columns: int = 2) -> ColumnComponent:
        """添加分栏组件"""
        self.component_counter += 1
        column = ColumnComponent(f"column_{self.component_counter}", columns)
        self.components.append(column)
        return column
    
    def remove_component(self, component_id: str) -> bool:
        """删除指定组件"""
        for i, component in enumerate(self.components):
            if component.component_id == component_id:
                del self.components[i]
                return True
        return False
    
    def move_component(self, component_id: str, direction: str) -> bool:
        """移动组件位置"""
        for i, component in enumerate(self.components):
            if component.component_id == component_id:
                if direction == "up" and i > 0:
                    self.components[i], self.components[i-1] = self.components[i-1], self.components[i]
                    return True
                elif direction == "down" and i < len(self.components) - 1:
                    self.components[i], self.components[i+1] = self.components[i+1], self.components[i]
                    return True
        return False
    
    def render_all(self, edit_mode: bool = False):
        """渲染所有组件"""
        if not self.components:
            return
        
        for i, component in enumerate(self.components):
            # 编辑模式下显示组件控制按钮
            if edit_mode:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 8])
                
                with col1:
                    if st.button("🔼", key=f"up_{component.component_id}", 
                               help="上移", disabled=(i == 0)):
                        if self.move_component(component.component_id, "up"):
                            st.rerun()
                
                with col2:
                    if st.button("🔽", key=f"down_{component.component_id}", 
                               help="下移", disabled=(i == len(self.components) - 1)):
                        if self.move_component(component.component_id, "down"):
                            st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"del_{component.component_id}", help="删除"):
                        if self.remove_component(component.component_id):
                            st.success("组件已删除")
                            st.rerun()
                
                with col4:
                    st.markdown(f"**{i+1}**")
                
                with col5:
                    component.render(edit_mode)
            else:
                component.render(edit_mode)
            
            st.markdown("---")
    
    def clear_all(self):
        """清空所有组件"""
        self.components.clear()
        self.component_counter = 0
    
    def get_component_count(self) -> int:
        """获取组件数量"""
        return len(self.components)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "component_counter": self.component_counter,
            "components": [comp.to_dict() for comp in self.components]
        }


# 全局组件管理器实例
if 'component_manager' not in st.session_state:
    st.session_state.component_manager = ComponentManager()
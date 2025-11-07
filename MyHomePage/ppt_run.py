"""
个人博客平台主程序 - 语雀风格编辑器
基于Streamlit实现类似语雀/飞书的个人博客平台
"""

import streamlit as st
from components import ComponentManager, CardComponent, MarkdownComponent, ColumnComponent
from page_manager import PageManager, EditMode

# 页面配置
st.set_page_config(
    page_title="个人博客平台 - 语雀风格",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .page-nav {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed;
    }
    
    .edit-mode-banner {
        background: linear-gradient(90deg, #ffeaa7, #fab1a0);
        color: #2d3436;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 0.95rem;
        border-left: 4px solid #e17055;
    }
    
    .page-title {
        color: #2c3e50;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    .page-description {
        color: #7f8c8d;
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .card-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
    }
    
    .card-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .card-container.vertical {
        text-align: center;
        border-left: none;
        border-top: 4px solid #667eea;
    }
    
    .card-container.minimal {
        background: transparent;
        box-shadow: none;
        border: 1px solid #e1e8ed;
        border-left: 4px solid #667eea;
    }
    
    .card-title {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .card-description {
        color: #7f8c8d;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .card-image {
        border-radius: 10px;
        max-width: 100%;
        height: auto;
    }
    
    .component-controls {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        padding: 0.3rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .markdown-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed;
        position: relative;
    }
    
    .column-container {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 2px dashed #dee2e6;
        position: relative;
    }
    
    .stButton > button {
        border-radius: 20px;
        border: none;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .component-edit-btn {
        background: #74b9ff !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.3rem 0.6rem !important;
        font-size: 0.8rem !important;
        margin: 0.2rem !important;
    }
    
    .component-move-btn {
        background: #00b894 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.2rem 0.4rem !important;
        font-size: 0.7rem !important;
        margin: 0.1rem !important;
    }
    
    .component-delete-btn {
        background: #e17055 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.2rem 0.4rem !important;
        font-size: 0.7rem !important;
        margin: 0.1rem !important;
    }
</style>
""", unsafe_allow_html=True)

def render_page_navigation():
    """渲染页面导航"""
    page_manager = st.session_state.page_manager
    
    with st.container():
        st.markdown('<div class="page-nav">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # 页面选择下拉框
            page_list = page_manager.get_page_list()
            if page_list:
                page_options = {f"{page.title} ({page.page_id})": page.page_id for page in page_list}
                current_display = f"{page_manager.get_current_page().title} ({page_manager.get_current_page().page_id})"
                
                selected_page = st.selectbox(
                    "当前页面",
                    options=list(page_options.keys()),
                    index=list(page_options.keys()).index(current_display) if current_display in page_options else 0,
                    key="page_selector"
                )
                
                # 切换页面
                if selected_page and page_options[selected_page] != page_manager.current_page_id:
                    page_manager.switch_page(page_options[selected_page])
                    st.rerun()
        
        with col2:
            if st.button("➕ 新建页面", use_container_width=True):
                st.session_state.show_new_page_dialog = True
                st.rerun()
        
        with col3:
            edit_mode = st.session_state.edit_mode
            if st.button("✏️ 编辑模式" if not edit_mode.is_edit_mode else "👁️ 预览模式", 
                        use_container_width=True):
                edit_mode.toggle_edit_mode()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_new_page_dialog():
    """渲染新建页面对话框"""
    if st.session_state.get('show_new_page_dialog', False):
        with st.expander("📄 新建页面", expanded=True):
            page_title = st.text_input("页面标题", placeholder="输入页面标题")
            page_description = st.text_area("页面描述", placeholder="输入页面描述（可选）")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("创建", use_container_width=True):
                    if page_title:
                        page_manager = st.session_state.page_manager
                        new_page = page_manager.create_page(page_title, page_description)
                        page_manager.switch_page(new_page.page_id)
                        st.session_state.show_new_page_dialog = False
                        st.success(f"页面 '{page_title}' 创建成功！")
                        st.rerun()
                    else:
                        st.error("请输入页面标题")
            
            with col2:
                if st.button("取消", use_container_width=True):
                    st.session_state.show_new_page_dialog = False
                    st.rerun()


def render_sidebar():
    """渲染侧边栏"""
    page_manager = st.session_state.page_manager
    current_page = page_manager.get_current_page()
    manager = current_page.component_manager
    edit_mode = st.session_state.edit_mode
    
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # 页面管理
        st.header("📚 页面管理")
        
        # 当前页面信息
        st.markdown(f"**当前页面：** {current_page.title}")
        if current_page.description:
            st.markdown(f"**描述：** {current_page.description}")
        
        # 页面操作
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ 编辑页面", use_container_width=True):
                st.session_state.show_edit_page_dialog = True
                st.rerun()
        
        with col2:
            if st.button("🗑️ 删除页面", use_container_width=True):
                if len(page_manager.get_page_list()) > 1:
                    page_manager.delete_page(current_page.page_id)
                    st.success("页面已删除")
                    st.rerun()
                else:
                    st.error("至少需要保留一个页面")
        
        st.markdown("---")
        
        # 组件管理
        st.header("🛠️ 组件管理")
        
        # 显示组件统计
        component_count = manager.get_component_count()
        st.markdown(f"**组件数量：** {component_count}")
        
        # 组件类型选择
        component_type = st.selectbox(
            "选择组件类型",
            ["卡片组件", "Markdown组件", "分栏组件"]
        )
        
        st.markdown("---")
        
        # 根据选择的组件类型显示不同的配置界面
        if component_type == "卡片组件":
            st.subheader("🎴 卡片组件配置")
            
            card_title = st.text_input("卡片标题", placeholder="输入卡片标题")
            card_description = st.text_area("卡片描述", placeholder="输入卡片描述")
            card_image_url = st.text_input("图片URL", placeholder="输入图片链接或本地路径")
            card_link_url = st.text_input("跳转链接", placeholder="输入点击后跳转的链接")
            card_style = st.selectbox("卡片样式", ["default", "vertical", "minimal"])
            
            if st.button("➕ 添加卡片", use_container_width=True):
                manager.add_card(card_title, card_description, card_image_url, card_link_url, card_style)
                st.success("卡片添加成功！")
                st.rerun()
        
        elif component_type == "Markdown组件":
            st.subheader("📝 Markdown组件配置")
            
            markdown_content = st.text_area(
                "Markdown内容", 
                placeholder="输入Markdown内容...\n\n例如：\n# 标题\n**粗体文本**\n- 列表项",
                height=200
            )
            
            if st.button("➕ 添加Markdown", use_container_width=True):
                manager.add_markdown(markdown_content)
                st.success("Markdown组件添加成功！")
                st.rerun()
        
        elif component_type == "分栏组件":
            st.subheader("📊 分栏组件配置")
            
            columns_count = st.slider("列数", min_value=2, max_value=4, value=2)
            
            if st.button("➕ 添加分栏", use_container_width=True):
                column_component = manager.add_column(columns_count)
                st.success(f"分栏组件添加成功！({columns_count}列)")
                st.rerun()
        
        st.markdown("---")
        
        # 快速操作
        st.subheader("⚡ 快速操作")
        
        if st.button("🚀 添加示例内容", use_container_width=True):
            # 添加示例内容
            manager.add_card(
                "Python编程指南",
                "学习Python编程的完整指南，从基础语法到高级应用",
                "https://via.placeholder.com/300x200/4CAF50/white?text=Python",
                "https://python.org",
                "default"
            )
            
            manager.add_markdown("""
# 欢迎来到我的博客 🎉

这是一个基于**Streamlit**构建的个人博客平台，具有以下特点：

- 🎴 **卡片组件**：展示项目、文章或任何内容
- 📝 **Markdown支持**：丰富的文本格式化
- 📊 **分栏布局**：灵活的页面布局
- 🎨 **现代化UI**：简洁美观的界面设计

> 开始创建你的第一个组件吧！
            """)
            
            st.success("示例内容添加成功！")
            st.rerun()
        
        if st.button("🗑️ 清空当前页面", use_container_width=True):
            manager.clear_all()
            st.success("当前页面已清空！")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_edit_page_dialog():
    """渲染编辑页面对话框"""
    if st.session_state.get('show_edit_page_dialog', False):
        page_manager = st.session_state.page_manager
        current_page = page_manager.get_current_page()
        
        with st.expander("✏️ 编辑页面信息", expanded=True):
            new_title = st.text_input("页面标题", value=current_page.title)
            new_description = st.text_area("页面描述", value=current_page.description)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存", use_container_width=True):
                    current_page.title = new_title
                    current_page.description = new_description
                    page_manager.save_pages()
                    st.session_state.show_edit_page_dialog = False
                    st.success("页面信息已更新！")
                    st.rerun()
            
            with col2:
                if st.button("取消", use_container_width=True):
                    st.session_state.show_edit_page_dialog = False
                    st.rerun()


def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">📝 个人博客平台 - 语雀风格</h1>', unsafe_allow_html=True)
    
    # 获取管理器实例
    page_manager = st.session_state.page_manager
    edit_mode = st.session_state.edit_mode
    current_page = page_manager.get_current_page()
    manager = current_page.component_manager
    
    # 页面导航
    render_page_navigation()
    
    # 新建页面对话框
    render_new_page_dialog()
    
    # 编辑页面对话框
    render_edit_page_dialog()
    
    # 编辑模式提示
    if edit_mode.is_edit_mode:
        st.markdown(
            '<div class="edit-mode-banner">'
            '✏️ <strong>编辑模式</strong> - 点击组件旁的编辑按钮进行编辑，使用上下箭头调整顺序'
            '</div>',
            unsafe_allow_html=True
        )
    
    # 侧边栏
    render_sidebar()
    
    # 主内容区域
    col1, col2 = st.columns([1, 20])
    
    with col2:
        # 页面标题和描述
        st.markdown(f'<h2 class="page-title">{current_page.title}</h2>', unsafe_allow_html=True)
        if current_page.description:
            st.markdown(f'<p class="page-description">{current_page.description}</p>', unsafe_allow_html=True)
        
        # 页面内容
        if manager.get_component_count() == 0:
            st.info("👈 请在左侧添加组件来构建页面内容")
            st.markdown("""
            ### 🎯 快速开始
            
            1. **选择组件类型**：在左侧选择要添加的组件类型
            2. **配置组件**：填写相应的配置信息
            3. **添加组件**：点击添加按钮将组件加入页面
            4. **编辑模式**：点击右上角的编辑模式按钮进入编辑状态
            5. **页面管理**：可以创建多个页面，每个页面独立管理组件
            
            💡 **提示**：可以点击"添加示例内容"快速体验所有功能！
            """)
        else:
            # 渲染所有组件
            manager.render_all(edit_mode.is_edit_mode)
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 2rem;'>"
        "🚀 基于 Streamlit 构建的个人博客平台 - 语雀风格编辑器 | "
        "💻 支持多页面管理、实时编辑、组件拖拽等功能"
        "</div>", 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
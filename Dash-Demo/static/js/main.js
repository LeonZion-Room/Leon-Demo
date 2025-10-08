// 主要JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化应用
    initializeApp();
});

function initializeApp() {
    // 添加页面加载动画
    addPageAnimations();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化模态框
    initializeModals();
    
    // 添加平滑滚动
    addSmoothScrolling();
    
    // 初始化表单验证
    initializeFormValidation();
}

// 页面动画
function addPageAnimations() {
    const animatedElements = document.querySelectorAll('.fade-in-up');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化模态框
function initializeModals() {
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            document.body.style.overflow = 'hidden';
        });
        
        modal.addEventListener('hide.bs.modal', function() {
            document.body.style.overflow = 'auto';
        });
    });
}

// 平滑滚动
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 表单验证
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// 项目管理功能
class ProjectManager {
    constructor() {
        this.projects = [];
        this.currentProject = null;
    }
    
    // 创建新项目
    async createProject(projectData) {
        try {
            const response = await fetch('/create-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('项目创建成功！', 'success');
                window.location.href = `/editor/${result.project_id}`;
            } else {
                this.showNotification('项目创建失败，请重试。', 'error');
            }
        } catch (error) {
            console.error('创建项目时出错:', error);
            this.showNotification('网络错误，请检查连接。', 'error');
        }
    }
    
    // 保存项目
    async saveProject(projectId, content) {
        try {
            const response = await fetch(`/api/save-project/${projectId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('项目已保存', 'success');
            } else {
                this.showNotification('保存失败，请重试', 'error');
            }
        } catch (error) {
            console.error('保存项目时出错:', error);
            this.showNotification('保存失败，网络错误', 'error');
        }
    }
    
    // 发布项目
    async publishProject(projectId) {
        try {
            const response = await fetch(`/api/publish-project/${projectId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('项目发布成功！', 'success');
                window.open(result.url, '_blank');
            } else {
                this.showNotification('发布失败，请重试', 'error');
            }
        } catch (error) {
            console.error('发布项目时出错:', error);
            this.showNotification('发布失败，网络错误', 'error');
        }
    }
    
    // 删除项目
    async deleteProject(projectId) {
        if (!confirm('确定要删除这个项目吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/delete-project/${projectId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('项目已删除', 'success');
                location.reload();
            } else {
                this.showNotification('删除失败，请重试', 'error');
            }
        } catch (error) {
            console.error('删除项目时出错:', error);
            this.showNotification('删除失败，网络错误', 'error');
        }
    }
    
    // 显示通知
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // 自动移除通知
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// 编辑器功能
class VisualEditor {
    constructor(container) {
        this.container = container;
        this.selectedElement = null;
        this.draggedElement = null;
        this.components = [];
        
        this.initializeEditor();
    }
    
    initializeEditor() {
        this.setupDragAndDrop();
        this.setupElementSelection();
        this.setupKeyboardShortcuts();
    }
    
    // 设置拖拽功能
    setupDragAndDrop() {
        // 组件拖拽
        document.querySelectorAll('.component-item').forEach(component => {
            component.addEventListener('dragstart', (e) => {
                this.draggedElement = e.target;
                e.dataTransfer.setData('text/html', e.target.outerHTML);
            });
        });
        
        // 画布拖拽接收
        const canvas = document.querySelector('.editor-canvas');
        if (canvas) {
            canvas.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
            });
            
            canvas.addEventListener('drop', (e) => {
                e.preventDefault();
                this.handleDrop(e);
            });
        }
    }
    
    // 处理拖拽放置
    handleDrop(e) {
        const componentData = e.dataTransfer.getData('text/html');
        const dropZone = e.target.closest('.drop-zone');
        
        if (dropZone) {
            const newElement = this.createElement(componentData);
            dropZone.appendChild(newElement);
            this.selectElement(newElement);
        }
    }
    
    // 创建元素
    createElement(componentData) {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = componentData;
        const element = wrapper.firstElementChild;
        
        // 添加编辑功能
        element.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectElement(element);
        });
        
        return element;
    }
    
    // 选择元素
    selectElement(element) {
        // 移除之前的选择
        document.querySelectorAll('.selected-element').forEach(el => {
            el.classList.remove('selected-element');
        });
        
        // 选择新元素
        element.classList.add('selected-element');
        this.selectedElement = element;
        
        // 更新属性面板
        this.updatePropertiesPanel(element);
    }
    
    // 更新属性面板
    updatePropertiesPanel(element) {
        const propertiesPanel = document.querySelector('.editor-properties');
        if (!propertiesPanel) return;
        
        const tagName = element.tagName.toLowerCase();
        const styles = window.getComputedStyle(element);
        
        propertiesPanel.innerHTML = `
            <div class="p-3">
                <h6 class="fw-bold mb-3">元素属性</h6>
                
                <div class="mb-3">
                    <label class="form-label">标签类型</label>
                    <input type="text" class="form-control" value="${tagName}" readonly>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">文本内容</label>
                    <textarea class="form-control" rows="3" onchange="updateElementText(this.value)">${element.textContent}</textarea>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">CSS类</label>
                    <input type="text" class="form-control" value="${element.className}" onchange="updateElementClass(this.value)">
                </div>
                
                <h6 class="fw-bold mb-3 mt-4">样式设置</h6>
                
                <div class="mb-3">
                    <label class="form-label">背景颜色</label>
                    <input type="color" class="form-control form-control-color" value="${this.rgbToHex(styles.backgroundColor)}" onchange="updateElementStyle('backgroundColor', this.value)">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">文字颜色</label>
                    <input type="color" class="form-control form-control-color" value="${this.rgbToHex(styles.color)}" onchange="updateElementStyle('color', this.value)">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">字体大小</label>
                    <input type="range" class="form-range" min="10" max="72" value="${parseInt(styles.fontSize)}" onchange="updateElementStyle('fontSize', this.value + 'px')">
                    <small class="text-muted">${styles.fontSize}</small>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">内边距</label>
                    <input type="range" class="form-range" min="0" max="50" value="${parseInt(styles.padding)}" onchange="updateElementStyle('padding', this.value + 'px')">
                    <small class="text-muted">${styles.padding}</small>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">外边距</label>
                    <input type="range" class="form-range" min="0" max="50" value="${parseInt(styles.margin)}" onchange="updateElementStyle('margin', this.value + 'px')">
                    <small class="text-muted">${styles.margin}</small>
                </div>
                
                <button class="btn btn-danger btn-sm w-100" onclick="deleteSelectedElement()">
                    <i class="fas fa-trash me-1"></i>
                    删除元素
                </button>
            </div>
        `;
    }
    
    // RGB转十六进制
    rgbToHex(rgb) {
        if (rgb.startsWith('#')) return rgb;
        
        const result = rgb.match(/\d+/g);
        if (!result || result.length < 3) return '#000000';
        
        return '#' + result.slice(0, 3).map(x => {
            const hex = parseInt(x).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    // 设置键盘快捷键
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveProject();
                        break;
                    case 'z':
                        e.preventDefault();
                        this.undo();
                        break;
                    case 'y':
                        e.preventDefault();
                        this.redo();
                        break;
                }
            }
            
            if (e.key === 'Delete' && this.selectedElement) {
                this.deleteSelectedElement();
            }
        });
    }
    
    // 删除选中元素
    deleteSelectedElement() {
        if (this.selectedElement) {
            this.selectedElement.remove();
            this.selectedElement = null;
            
            // 清空属性面板
            const propertiesPanel = document.querySelector('.editor-properties');
            if (propertiesPanel) {
                propertiesPanel.innerHTML = '<div class="p-3 text-center text-muted">请选择一个元素</div>';
            }
        }
    }
}

// 全局函数
window.updateElementText = function(text) {
    if (window.editor && window.editor.selectedElement) {
        window.editor.selectedElement.textContent = text;
    }
};

window.updateElementClass = function(className) {
    if (window.editor && window.editor.selectedElement) {
        window.editor.selectedElement.className = className;
    }
};

window.updateElementStyle = function(property, value) {
    if (window.editor && window.editor.selectedElement) {
        window.editor.selectedElement.style[property] = value;
    }
};

window.deleteSelectedElement = function() {
    if (window.editor) {
        window.editor.deleteSelectedElement();
    }
};

// 初始化全局对象
window.projectManager = new ProjectManager();

// 如果在编辑器页面，初始化编辑器
if (document.querySelector('.editor-container')) {
    window.editor = new VisualEditor(document.querySelector('.editor-container'));
}
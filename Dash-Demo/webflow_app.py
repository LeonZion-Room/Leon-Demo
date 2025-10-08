from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime
import json

# 创建Flask应用
app = Flask(__name__)

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "webflow.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 数据库模型
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template = db.Column(db.String(50), default='blank')
    content = db.Column(db.Text)  # 存储页面内容的JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    preview_image = db.Column(db.String(200))
    content = db.Column(db.Text)  # 模板的HTML/CSS内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 路由定义
@app.route('/')
def index():
    """主页 - 类似Webflow首页"""
    return render_template('index.html')

@app.route('/features')
def features():
    """功能介绍页面"""
    return render_template('features.html')

@app.route('/templates')
def templates():
    """模板库页面"""
    templates = Template.query.all()
    return render_template('templates.html', templates=templates)

@app.route('/pricing')
def pricing():
    """价格页面"""
    return render_template('pricing.html')

@app.route('/dashboard')
def dashboard():
    """用户仪表板"""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/editor')
@app.route('/editor/<int:project_id>')
def editor(project_id=None):
    """可视化编辑器"""
    project = None
    if project_id:
        project = Project.query.get_or_404(project_id)
    return render_template('editor.html', project=project)

@app.route('/create-project', methods=['GET', 'POST'])
def create_project():
    """创建新项目"""
    if request.method == 'POST':
        data = request.get_json()
        project = Project(
            name=data.get('name', 'Untitled Project'),
            description=data.get('description', ''),
            template=data.get('template', 'blank'),
            content=json.dumps(data.get('content', {}))
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({'success': True, 'project_id': project.id})
    
    templates = Template.query.all()
    return render_template('create_project.html', templates=templates)

@app.route('/api/save-project/<int:project_id>', methods=['POST'])
def save_project(project_id):
    """保存项目内容"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    project.content = json.dumps(data.get('content', {}))
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/publish-project/<int:project_id>', methods=['POST'])
def publish_project(project_id):
    """发布项目"""
    project = Project.query.get_or_404(project_id)
    project.published = True
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'url': f'/preview/{project_id}'})

@app.route('/preview/<int:project_id>')
def preview_project(project_id):
    """预览已发布的项目"""
    project = Project.query.get_or_404(project_id)
    if not project.published:
        return redirect(url_for('dashboard'))
    
    content = json.loads(project.content) if project.content else {}
    return render_template('preview.html', project=project, content=content)

@app.route('/api/delete-project/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})

# 初始化数据库和示例数据
def init_db():
    """初始化数据库和示例数据"""
    with app.app_context():
        db.create_all()
        
        # 检查是否已有模板数据
        if Template.query.count() == 0:
            # 添加示例模板
            templates_data = [
                {
                    'name': '商业网站',
                    'category': 'business',
                    'description': '专业的商业网站模板，适合企业展示',
                    'preview_image': '/static/images/template-business.jpg',
                    'content': json.dumps({
                        'sections': [
                            {'type': 'hero', 'title': '您的企业标题', 'subtitle': '企业描述'},
                            {'type': 'features', 'items': []},
                            {'type': 'contact', 'title': '联系我们'}
                        ]
                    })
                },
                {
                    'name': '作品集',
                    'category': 'portfolio',
                    'description': '展示个人作品的精美模板',
                    'preview_image': '/static/images/template-portfolio.jpg',
                    'content': json.dumps({
                        'sections': [
                            {'type': 'hero', 'title': '设计师姓名', 'subtitle': '创意作品集'},
                            {'type': 'gallery', 'items': []},
                            {'type': 'about', 'title': '关于我'}
                        ]
                    })
                },
                {
                    'name': '博客',
                    'category': 'blog',
                    'description': '现代化的博客模板，适合内容创作者',
                    'preview_image': '/static/images/template-blog.jpg',
                    'content': json.dumps({
                        'sections': [
                            {'type': 'hero', 'title': '我的博客', 'subtitle': '分享想法和见解'},
                            {'type': 'posts', 'items': []},
                            {'type': 'sidebar', 'widgets': []}
                        ]
                    })
                },
                {
                    'name': '电商网站',
                    'category': 'ecommerce',
                    'description': '功能完整的电商网站模板',
                    'preview_image': '/static/images/template-ecommerce.jpg',
                    'content': json.dumps({
                        'sections': [
                            {'type': 'hero', 'title': '在线商店', 'subtitle': '发现优质产品'},
                            {'type': 'products', 'items': []},
                            {'type': 'features', 'items': []}
                        ]
                    })
                }
            ]
            
            for template_data in templates_data:
                template = Template(**template_data)
                db.session.add(template)
            
            db.session.commit()
            print("✅ 数据库初始化完成，示例模板已添加")

if __name__ == '__main__':
    init_db()
    print("🚀 启动Webflow风格的Flask应用...")
    print("📱 访问地址: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
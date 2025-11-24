import os
from datetime import datetime
from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# En producción, usa una clave secreta robusta guardada en variables de entorno
app.config['SECRET_KEY'] = 'plasticos-sustentables-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion_tareas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELOS DE BASE DE DATOS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # Relación para saber qué tareas tiene asignadas este usuario
    tasks = db.relationship('Task', backref='assignee', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pendiente') # Pendiente, En Progreso, Completada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    
    # Clave foránea: A quién se le asigna la tarea
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Creador de la tarea (opcional, para auditoría)
    created_by = db.Column(db.String(100), nullable=True)

# --- GESTIÓN DE LOGIN ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- PLANTILLAS HTML (Incrustadas para un solo archivo) ---

base_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plásticos Sustentables - Gestión</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; }
        .navbar { background-color: #2c3e50; }
        .card-task { transition: transform 0.2s; border-left: 5px solid #2c3e50; }
        .card-task:hover { transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .status-Completada { border-left-color: #28a745; }
        .status-Pendiente { border-left-color: #ffc107; }
        .brand-text { font-weight: bold; color: #2ecc71 !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand brand-text" href="{{ url_for('dashboard') }}">Plásticos Sustentables</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {% if current_user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}">Tablero</a></li>
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('profile') }}">Mi Perfil</a></li>
                        <li class="nav-item"><a class="nav-link text-danger" href="{{ url_for('logout') }}">Cerrar Sesión</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}">Iniciar Sesión</a></li>
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('register') }}">Registrarse</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

login_template = """
{% extends "base" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card shadow">
            <div class="card-body">
                <h3 class="text-center mb-4">Iniciar Sesión</h3>
                <form method="POST">
                    <div class="mb-3">
                        <label>Usuario</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Contraseña</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Ingresar</button>
                </form>
                <div class="mt-3 text-center">
                    <small>¿No tienes cuenta? <a href="{{ url_for('register') }}">Regístrate aquí</a></small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

register_template = """
{% extends "base" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card shadow">
            <div class="card-body">
                <h3 class="text-center mb-4">Registro Empleado</h3>
                <form method="POST">
                    <div class="mb-3">
                        <label>Usuario</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Email</label>
                        <input type="email" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Contraseña</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Registrar</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

dashboard_template = """
{% extends "base" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Tablero de Tareas</h2>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTaskModal">+ Nueva Tarea</button>
</div>

<!-- Filtros -->
<div class="card p-3 mb-4 bg-light">
    <form method="GET" class="row g-3">
        <div class="col-md-4">
            <input type="text" name="search" class="form-control" placeholder="Buscar tarea..." value="{{ search_query }}">
        </div>
        <div class="col-md-3">
            <select name="status" class="form-select">
                <option value="">Todos los estados</option>
                <option value="Pendiente" {% if status_filter == 'Pendiente' %}selected{% endif %}>Pendiente</option>
                <option value="Completada" {% if status_filter == 'Completada' %}selected{% endif %}>Completada</option>
            </select>
        </div>
        <div class="col-md-2">
            <button type="submit" class="btn btn-secondary w-100">Filtrar</button>
        </div>
        <div class="col-md-2">
            <a href="{{ url_for('dashboard') }}" class="btn btn-outline-secondary w-100">Limpiar</a>
        </div>
    </form>
</div>

<div class="row">
    {% for task in tasks %}
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="card card-task h-100 status-{{ task.status }}">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <h5 class="card-title">{{ task.title }}</h5>
                    <span class="badge {% if task.status == 'Completada' %}bg-success{% else %}bg-warning{% endif %}">
                        {{ task.status }}
                    </span>
                </div>
                <p class="card-text text-muted small">Asignado a: <strong>{{ task.assignee.username }}</strong></p>
                <p class="card-text">{{ task.description }}</p>
                
                <div class="mt-3">
                    <!-- Acciones Rápidas -->
                    <form action="{{ url_for('update_task_status', task_id=task.id) }}" method="POST" class="d-inline">
                        {% if task.status != 'Completada' %}
                            <button name="status" value="Completada" class="btn btn-sm btn-outline-success">✓</button>
                        {% else %}
                            <button name="status" value="Pendiente" class="btn btn-sm btn-outline-warning">↺</button>
                        {% endif %}
                    </form>
                    
                    <a href="{{ url_for('edit_task', task_id=task.id) }}" class="btn btn-sm btn-outline-primary">Editar</a>
                    <a href="{{ url_for('delete_task', task_id=task.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('¿Eliminar tarea?')">Eliminar</a>
                </div>
            </div>
            <div class="card-footer text-muted small">
                Creado por: {{ task.created_by }}
            </div>
        </div>
    </div>
    {% else %}
    <div class="col-12 text-center py-5">
        <h4 class="text-muted">No se encontraron tareas.</h4>
    </div>
    {% endfor %}
</div>

<!-- Modal Nueva Tarea -->
<div class="modal fade" id="addTaskModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Nueva Tarea</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form action="{{ url_for('create_task') }}" method="POST">
                <div class="modal-body">
                    <div class="mb-3">
                        <label>Título</label>
                        <input type="text" name="title" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Descripción</label>
                        <textarea name="description" class="form-control" rows="3"></textarea>
                    </div>
                    <div class="mb-3">
                        <label>Asignar a Empleado</label>
                        <select name="user_id" class="form-select">
                            {% for user in all_users %}
                                <option value="{{ user.id }}" {% if user.id == current_user.id %}selected{% endif %}>{{ user.username }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Guardar Tarea</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""

edit_task_template = """
{% extends "base" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">Editar Tarea</div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label>Título</label>
                        <input type="text" name="title" class="form-control" value="{{ task.title }}" required>
                    </div>
                    <div class="mb-3">
                        <label>Descripción</label>
                        <textarea name="description" class="form-control" rows="3">{{ task.description }}</textarea>
                    </div>
                    <div class="mb-3">
                        <label>Estado</label>
                        <select name="status" class="form-select">
                            <option value="Pendiente" {% if task.status == 'Pendiente' %}selected{% endif %}>Pendiente</option>
                            <option value="Completada" {% if task.status == 'Completada' %}selected{% endif %}>Completada</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Actualizar</button>
                    <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancelar</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

profile_template = """
{% extends "base" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow">
            <div class="card-header bg-dark text-white">Mi Perfil: {{ current_user.username }}</div>
            <div class="card-body">
                <form method="POST">
                    <h5 class="mb-3">Cambiar Contraseña</h5>
                    <div class="mb-3">
                        <label>Nueva Contraseña</label>
                        <input type="password" name="new_password" class="form-control" placeholder="Dejar en blanco para no cambiar">
                    </div>
                    <button type="submit" class="btn btn-warning w-100">Actualizar Perfil</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email, 
                        password_hash=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))
        
    return render_template_string(register_template, base_template=base_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template_string(login_template, base_template=base_template)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Task.query
    
    # Filtrado
    if search_query:
        query = query.filter(Task.title.contains(search_query))
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    # Ordenar por fecha de creación descendente
    tasks = query.order_by(Task.created_at.desc()).all()
    all_users = User.query.all()
    
    # Renderizamos la plantilla base dentro de la dashboard
    final_template = dashboard_template.replace('{% extends "base" %}', base_template)
    
    return render_template_string(final_template, tasks=tasks, all_users=all_users, 
                                  search_query=search_query, status_filter=status_filter)

@app.route('/task/new', methods=['POST'])
@login_required
def create_task():
    title = request.form.get('title')
    description = request.form.get('description')
    assigned_user_id = request.form.get('user_id')
    
    new_task = Task(
        title=title,
        description=description,
        user_id=assigned_user_id,
        created_by=current_user.username
    )
    db.session.add(new_task)
    db.session.commit()
    flash('Tarea creada correctamente', 'success')
    return redirect(url_for('dashboard'))

@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        db.session.commit()
        flash('Tarea actualizada', 'success')
        return redirect(url_for('dashboard'))
        
    final_template = edit_task_template.replace('{% extends "base" %}', base_template)
    return render_template_string(final_template, task=task)

@app.route('/task/status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('status')
    if new_status:
        task.status = new_status
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/task/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Tarea eliminada', 'success')
    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        if new_pass:
            current_user.password_hash = generate_password_hash(new_pass, method='scrypt')
            db.session.commit()
            flash('Contraseña actualizada con éxito', 'success')
            
    final_template = profile_template.replace('{% extends "base" %}', base_template)
    return render_template_string(final_template)

# --- INICIALIZACIÓN ---

if __name__ == '__main__':
    # Crear la base de datos si no existe
    if not os.path.exists('gestion_tareas.db'):
        with app.app_context():
            db.create_all()
            print("Base de datos creada exitosamente.")
            
    app.run(debug=True)
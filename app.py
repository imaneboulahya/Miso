# =============================================
# IMPORTS
# =============================================
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from flask import jsonify, Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime, timezone
from sqlalchemy.sql import func
from flask_migrate import Migrate
import os
import secrets


# =============================================
# APP CONFIGURATION
# =============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF globally
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# =============================================
# DATABASE MODELS
# =============================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    articles = db.relationship('Article', backref='author', lazy=True)
    liked_articles = db.relationship('Like', backref='user', lazy=True, foreign_keys='Like.user_id')
    comments = db.relationship('Comment', backref='author', lazy=True)
    discussion_messages = db.relationship('DiscussionMessage', backref='author', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300))
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), default=lambda: datetime.now(timezone.utc).strftime('%B %d, %Y'))
    image_url = db.Column(db.String(200), default='default_article.jpg')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='article', lazy=True)
    likes = db.relationship('Like', backref='article', lazy=True)

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    profile_pic = db.Column(db.String(200), default='default_discussion.jpg')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('DiscussionMessage', backref='discussion', lazy=True)

class DiscussionMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))


# =============================================
# FORMS
# =============================================
class LoginForm(FlaskForm):
    class Meta:
        csrf = False
        
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    class Meta:
        csrf = False
        
    username = StringField('Username', validators=[DataRequired(), Length(min=4)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')
    profile_pic = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Choose another.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
        if '@' not in email.data:
            raise ValidationError('Please enter a valid email address')

class ArticleForm(FlaskForm):
    class Meta:
        csrf = False
        
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt', validators=[Length(max=300)])
    category = SelectField('Category', choices=[
        ('art', 'Art'), ('culture', 'Culture'), ('sport', 'Sport'),
        ('economy', 'Economy'), ('technology', 'Technology'), 
        ('health', 'Health'), ('entrepreneurship', 'Entrepreneurship'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    image = FileField('Article Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Publish')

class DiscussionForm(FlaskForm):
    class Meta:
        csrf = False
        
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    profile_pic = FileField('Discussion Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Create Discussion')


# =============================================
# HELPER FUNCTIONS
# =============================================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_suggested_articles(article, limit=3):
    same_category = Article.query.filter(
        Article.category == article.category,
        Article.id != article.id
    ).order_by(db.func.random()).limit(2).all()
    
    random_article = Article.query.filter(
        Article.id != article.id,
        ~Article.id.in_([a.id for a in same_category])
    ).order_by(db.func.random()).first()
    
    return same_category + ([random_article] if random_article else [])


# =============================================
# ROUTES - AUTHENTICATION
# =============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home_after_login'))
        flash('Invalid email or password', 'danger')
    return render_template('log_in_page.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        try:
            profile_pic_filename = 'default.jpg'
            if form.profile_pic.data:
                file = form.profile_pic.data
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    profile_pic_filename = f"{secrets.token_hex(8)}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(file_path)
            
            hashed_pw = generate_password_hash(form.password.data)
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_pw,
                profile_pic=profile_pic_filename
            )
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            return redirect(url_for('home_after_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
    return render_template('sign_up_page.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# =============================================
# ROUTES - MAIN PAGES
# =============================================
@app.route('/')
def home():
    categories = [
        {'name': 'art', 'description': 'Creative expressions', 'color': '#FF9FEE', 'icon': 'fas fa-paint-brush'},
        {'name': 'culture', 'description': 'Global traditions', 'color': '#B3B0FF', 'icon': 'fas fa-globe'},
        {'name': 'sport', 'description': 'Athletic excellence', 'color': '#FD0261', 'icon': 'fas fa-running'},
        {'name': 'economy', 'description': 'Market dynamics', 'color': '#aae354', 'icon': 'fas fa-chart-line'},
        {'name': 'technology', 'description': 'Digital innovations', 'color': '#A4A1AA', 'icon': 'fas fa-laptop-code'},
        {'name': 'health', 'description': 'Mind and body wellness', 'color': '#524F56', 'icon': 'fas fa-heartbeat'},
        {'name': 'entrepreneurship', 'description': 'Startup journeys', 'color': '#252275', 'icon': 'fas fa-lightbulb'},
        {'name': 'other', 'description': 'Miscellaneous gems', 'color': '#91558e', 'icon': 'fas fa-ellipsis-h'}
    ]
    
    for category in categories:
        category['article_count'] = Article.query.filter_by(category=category['name']).count()
    
    articles = Article.query.order_by(Article.id.desc()).limit(6).all()
    return render_template('index.html', categories=categories, articles=articles)

@app.route('/home_after_login')
def home_after_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    categories = [
        {'name': 'art', 'description': 'Creative expressions', 'color': '#FF9FEE', 'icon': 'fas fa-paint-brush'},
        {'name': 'culture', 'description': 'Global traditions', 'color': '#B3B0FF', 'icon': 'fas fa-globe'},
        {'name': 'sport', 'description': 'Athletic excellence', 'color': '#FD0261', 'icon': 'fas fa-running'},
        {'name': 'economy', 'description': 'Market dynamics', 'color': '#aae354', 'icon': 'fas fa-chart-line'},
        {'name': 'technology', 'description': 'Digital innovations', 'color': '#A4A1AA', 'icon': 'fas fa-laptop-code'},
        {'name': 'health', 'description': 'Mind and body wellness', 'color': '#524F56', 'icon': 'fas fa-heartbeat'},
        {'name': 'entrepreneurship', 'description': 'Startup journeys', 'color': '#252275', 'icon': 'fas fa-lightbulb'},
        {'name': 'other', 'description': 'Miscellaneous gems', 'color': '#91558e', 'icon': 'fas fa-ellipsis-h'}
    ]
    
    for category in categories:
        category['article_count'] = Article.query.filter_by(category=category['name']).count()
    
    articles = Article.query.order_by(Article.id.desc()).limit(6).all()
    return render_template('home_after_login.html', categories=categories, articles=articles)


# =============================================
# ROUTES - ARTICLES
# =============================================
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = ArticleForm()
    if form.validate_on_submit():
        try:
            image_filename = 'default_article.jpg'
            if form.image.data:
                file = form.image.data
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    image_filename = f"{secrets.token_hex(8)}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(file_path)
            
            new_article = Article(
                title=form.title.data,
                content=form.content.data,
                excerpt=form.excerpt.data or form.content.data[:300],
                category=form.category.data,
                author_id=session['user_id'],
                image_url=image_filename
            )
            db.session.add(new_article)
            db.session.commit()
            flash('Article published successfully!', 'success')
            return redirect(url_for('home_after_login'))
        except Exception as e:
            db.session.rollback()
            flash('Error publishing article. Please try again.', 'danger')
    return render_template('create.html', form=form)

@app.route('/article/<int:id>')
def article_view(id):
    if 'user_id' not in session:
        return redirect(url_for('article_be', id=id))
    
    article = Article.query.get_or_404(id)
    liked = Like.query.filter_by(user_id=session['user_id'], article_id=article.id).first() is not None
    suggested_articles = get_suggested_articles(article)
    
    return render_template('article.html',
                         article=article,
                         liked=liked,
                         suggested_articles=suggested_articles,
                         current_user_id=session.get('user_id'))

@app.route('/article/<int:article_id>/comment', methods=['POST'])
def add_comment(article_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment_text = request.form.get('comment_text')
    if not comment_text or len(comment_text.strip()) == 0:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('article_view', id=article_id))
    
    try:
        new_comment = Comment(
            text=comment_text,
            author_id=session['user_id'],
            article_id=article_id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding comment', 'danger')
    
    return redirect(url_for('article_view', id=article_id))

@app.route('/article/<int:id>/like', methods=['POST'])
def like_article(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    article = Article.query.get_or_404(id)
    user_id = session['user_id']
    existing_like = Like.query.filter_by(user_id=user_id, article_id=article.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = Like(user_id=user_id, article_id=article.id)
        db.session.add(new_like)
        liked = True
    
    db.session.commit()
    return jsonify({'likes': len(article.likes), 'liked': liked})

@app.route('/delete_article/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        article = Article.query.get_or_404(article_id)
        if article.author_id != session['user_id']:
            return jsonify({'success': False, 'message': 'Not authorized'}), 403
        
        # Delete associated comments and likes
        Comment.query.filter_by(article_id=article.id).delete()
        Like.query.filter_by(article_id=article.id).delete()
        
        # Delete image file if not default
        if article.image_url != 'default_article.jpg':
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], article.image_url)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except OSError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error deleting image: {str(e)}'}), 500
        
        db.session.delete(article)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# =============================================
# ROUTES - DISCUSSIONS
# =============================================
@app.route('/discussions')
def discussions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    base_query = Discussion.query
    if query:
        base_query = base_query.filter(
            (Discussion.title.ilike(f'%{query}%')) | 
            (Discussion.description.ilike(f'%{query}%'))
        )
    
    discussions = base_query.order_by(Discussion.created_at.desc()).paginate(page=page, per_page=9)
    return render_template('discussions_after.html', 
                         discussions=discussions,
                         active_tab='discussions',
                         query=query)

@app.route('/create_discussion', methods=['GET', 'POST'])
def create_discussion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = DiscussionForm()
    if form.validate_on_submit():
        try:
            profile_pic_filename = 'default_discussion.jpg'
            if form.profile_pic.data:
                file = form.profile_pic.data
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    profile_pic_filename = f"{secrets.token_hex(8)}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(file_path)
            
            new_discussion = Discussion(
                title=form.title.data,
                description=form.description.data,
                profile_pic=profile_pic_filename,
                author_id=session['user_id']
            )
            db.session.add(new_discussion)
            db.session.commit()
            flash('Discussion created successfully!', 'success')
            return redirect(url_for('discussions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating discussion: {str(e)}', 'danger')
    
    return render_template('create_discussion.html', form=form)

@app.route('/discussion/<int:id>', methods=['GET', 'POST'])
def view_discussion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    discussion = Discussion.query.get_or_404(id)
    
    if request.method == 'POST':
        message_text = request.form.get('message_text')
        if message_text and len(message_text.strip()) > 0:
            new_message = DiscussionMessage(
                text=message_text,
                author_id=session['user_id'],
                discussion_id=discussion.id
            )
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for('view_discussion', id=id))
    
    messages = DiscussionMessage.query.filter_by(discussion_id=discussion.id)\
                                    .order_by(DiscussionMessage.timestamp.asc())\
                                    .all()
    
    return render_template('discussion_view.html',
                         discussion=discussion,
                         messages=messages,
                         current_user_id=session['user_id'])


# =============================================
# ROUTES - PROFILES
# =============================================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    articles = Article.query.filter_by(author_id=user.id).order_by(Article.id.desc()).all()
    likes_count = db.session.query(db.func.count(Like.id))\
                           .join(Article, Like.article_id == Article.id)\
                           .filter(Article.author_id == user.id)\
                           .scalar() or 0
    
    return render_template('profile.html', 
                         user=user,
                         articles=articles,
                         likes_count=likes_count)

@app.route('/profile/<username>')
def view_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first_or_404()
    articles = Article.query.filter_by(author_id=user.id).order_by(Article.id.desc()).all()
    likes_count = db.session.query(db.func.count(Like.id))\
                           .join(Article, Like.article_id == Article.id)\
                           .filter(Article.author_id == user.id)\
                           .scalar() or 0
    
    return render_template('view_profile.html',
                         user=user,
                         articles=articles,
                         likes_count=likes_count,
                         current_user_id=session.get('user_id'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    try:
        new_username = request.form.get('username')
        if new_username and new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != user.id:
                flash('Username already taken', 'danger')
                return redirect(url_for('profile'))
            user.username = new_username
        
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{secrets.token_hex(8)}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Delete old profile picture if not default
                if user.profile_pic != 'default.jpg':
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_pic)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                user.profile_pic = unique_filename
        
        db.session.commit()
        session['username'] = user.username
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile: ' + str(e), 'danger')
    
    return redirect(url_for('profile'))


# =============================================
# ROUTES - SEARCH
# =============================================
@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('search_be'))
    
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    active_tab = 'articles'
    
    base_query = Article.query
    if category:
        base_query = base_query.filter_by(category=category)
    if query:
        base_query = base_query.filter(
            (Article.title.ilike(f'%{query}%')) | 
            (Article.content.ilike(f'%{query}%')) |
            (Article.category.ilike(f'%{query}%'))
        )
    
    results = base_query.order_by(Article.id.desc()).paginate(page=page, per_page=9)
    return render_template('search_page.html',
                         query=query,
                         results=results,
                         active_category=category,
                         active_tab=active_tab,
                         page=page)

@app.route('/searchbe', methods=['GET', 'POST'])
def search_be():
    if request.method == 'POST':
        query = request.form.get('q', '')
        return redirect(url_for('search_be', q=query))
    
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    base_query = Article.query
    if category and category.lower() != 'all':
        base_query = base_query.filter_by(category=category)
    if query:
        base_query = base_query.filter(
            (Article.title.ilike(f'%{query}%')) | 
            (Article.content.ilike(f'%{query}%')) |
            (Article.category.ilike(f'%{query}%'))
        )
    
    articles = base_query.order_by(Article.id.desc()).all()
    return render_template('search_page_before.html',
                         articles=articles,
                         query=query,
                         active_category=category)

@app.route('/search/profiles')
def search_profiles():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    base_query = User.query
    if query:
        base_query = base_query.filter(
            (User.username.ilike(f'%{query}%')) | 
            (User.email.ilike(f'%{query}%'))
        )
    
    users = base_query.order_by(User.username.asc()).paginate(page=page, per_page=9)
    return render_template('search_profiles.html',
                         query=query,
                         users=users,
                         active_tab='profiles',
                         page=page)


# =============================================
# ROUTES - CATEGORIES
# =============================================
@app.route('/category/<category_name>')
def category_page(category_name):
    valid_categories = ['art', 'culture', 'sport', 'economy', 
                       'technology', 'health', 'entrepreneurship', 'other']
    if category_name not in valid_categories:
        abort(404)
    
    if 'user_id' not in session:
        return redirect(url_for('category_be', category_name=category_name))
    
    articles = Article.query.filter_by(category=category_name).order_by(Article.id.desc()).all()
    category_meta = {
        'art': {'color': '#FF9FEE', 'description': 'Creative expressions'},
        'culture': {'color': '#B3B0FF', 'description': 'Global traditions'},
        'sport': {'color': '#FD0261', 'description': 'Athletic excellence'},
        'economy': {'color': '#aae354', 'description': 'Market dynamics'},
        'technology': {'color': '#A4A1AA', 'description': 'Digital innovations'},
        'health': {'color': '#524F56', 'description': 'Mind and body wellness'},
        'entrepreneurship': {'color': '#252275', 'description': 'Startup journeys'},
        'other': {'color': '#91558e', 'description': 'Miscellaneous gems'}
    }
    
    return render_template(f'categories/{category_name}.html',
                         articles=articles,
                         category_name=category_name,
                         category_color=category_meta[category_name]['color'],
                         category_description=category_meta[category_name]['description'])

@app.route('/categorybe/<category_name>')
def category_be(category_name):
    valid_categories = ['art', 'culture', 'sport', 'economy', 
                       'technology', 'health', 'entrepreneurship', 'other']
    if category_name not in valid_categories:
        abort(404)
    
    articles = Article.query.filter_by(category=category_name).order_by(Article.id.desc()).all()
    category_meta = {
        'art': {'color': '#FF9FEE', 'description': 'Creative expressions'},
        'culture': {'color': '#B3B0FF', 'description': 'Global traditions'},
        'sport': {'color': '#FD0261', 'description': 'Athletic excellence'},
        'economy': {'color': '#aae354', 'description': 'Market dynamics'},
        'technology': {'color': '#A4A1AA', 'description': 'Digital innovations'},
        'health': {'color': '#524F56', 'description': 'Mind and body wellness'},
        'entrepreneurship': {'color': '#252275', 'description': 'Startup journeys'},
        'other': {'color': '#91558e', 'description': 'Miscellaneous gems'}
    }
    
    return render_template('search_page_before.html',
                         articles=articles,
                         active_category=category_name,
                         category_color=category_meta[category_name]['color'],
                         category_description=category_meta[category_name]['description'],
                         query=None,
                         page=1)


# =============================================
# ROUTES - MISC
# =============================================
@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/check_auth')
def check_auth():
    return jsonify({'authenticated': 'user_id' in session})

@app.route('/article_be/<int:id>')
def article_be(id):
    article = Article.query.get_or_404(id)
    suggested_articles = get_suggested_articles(article)
    return render_template('article_be.html',
                         article=article,
                         suggested_articles=suggested_articles)


# =============================================
# APP INITIALIZATION
# =============================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
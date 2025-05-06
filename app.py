from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from flask import jsonify
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime, timezone
import os
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
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
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt', validators=[Length(max=300)])
    category = SelectField('Category', choices=[
        ('art', 'Art'), 
        ('culture', 'Culture'),
        ('sport', 'Sport'),
        ('economy', 'Economy'),
        ('technology', 'Technology'),
        ('health', 'Health'),
        ('entrepreneurship', 'Entrepreneurship'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Publish')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    articles = db.relationship('Article', backref='author', lazy=True)
    liked_articles = db.relationship(
        'Like',
        backref='user',
        lazy=True,
        foreign_keys='Like.user_id'
    )

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    article = db.relationship('Article', backref=db.backref('likes', lazy=True))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300))
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), default=lambda: datetime.now(timezone.utc).strftime('%B %d, %Y'))
    image_url = db.Column(db.String(200), default='default_article.jpg')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    author = db.relationship('User', backref='comments')
    article = db.relationship('Article', backref='comments')

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

@app.route('/')
def home():
    categories = [
        {'name': 'art', 'description': 'Creative expressions', 'color': '#FF9FEE'},
        {'name': 'culture', 'description': 'Global traditions', 'color': '#B3B0FF'},
        {'name': 'sport', 'description': 'Athletic excellence', 'color': '#FD0261'},
        {'name': 'economy', 'description': 'Market dynamics', 'color': '#aae354'},
        {'name': 'technology', 'description': 'Digital innovations', 'color': '#A4A1AA'},
        {'name': 'health', 'description': 'Mind and body wellness', 'color': '#524F56'},
        {'name': 'entrepreneurship', 'description': 'Startup journeys', 'color': '#252275'},
        {'name': 'other', 'description': 'Miscellaneous gems', 'color': '#91558e'}
    ]
    for category in categories:
        category['article_count'] = Article.query.filter_by(category=category['name']).count()
    articles = Article.query.order_by(Article.id.desc()).limit(6).all()
    return render_template('index.html', categories=categories, articles=articles)

@app.route('/categorybe/<category_name>')
def category_be(category_name):
    valid_categories = ['art', 'culture', 'sport', 'economy', 
                       'technology', 'health', 'entrepreneurship', 'other']
    if category_name not in valid_categories:
        abort(404)
    articles = Article.query.filter_by(category=category_name).order_by(Article.id.desc()).all()
    return render_template('search_page_before.html',
                         articles=articles,
                         active_category=category_name,
                         query=None,
                         page=1)

@app.route('/searchbe', methods=['GET', 'POST'])
def search_be():
    if request.method == 'POST':
        query = request.form.get('q', '')
        return redirect(url_for('search_be', q=query))
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    base_query = Article.query
    if query:
        base_query = base_query.filter(
            (Article.title.ilike(f'%{query}%')) | 
            (Article.content.ilike(f'%{query}%')) |
            (Article.category.ilike(f'%{query}%'))
        )
    if category:
        base_query = base_query.filter_by(category=category)
    articles = base_query.order_by(Article.id.desc()).paginate(page=page, per_page=9)
    return render_template('search_page_before.html',
                         query=query,
                         results=articles.items,
                         active_category=category,
                         page=page)

@app.route('/article_be/<int:id>')
def article_be(id):
    article = Article.query.get_or_404(id)
    suggested_articles = get_suggested_articles(article)
    return render_template('article_be.html',
                         article=article,
                         suggested_articles=suggested_articles)

@app.route('/check_auth')
def check_auth():
    return jsonify({'authenticated': 'user_id' in session})

@app.route('/article/<int:id>')
def article_view(id):
    if 'user_id' not in session:
        return redirect(url_for('article_be', id=id))
    
    article = Article.query.get_or_404(id)
    liked = Like.query.filter_by(
        user_id=session['user_id'],
        article_id=article.id
    ).first() is not None
    
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

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('search_be'))
    
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    
    base_query = Article.query
    if query:
        base_query = base_query.filter(
            (Article.title.ilike(f'%{query}%')) | 
            (Article.content.ilike(f'%{query}%')) |
            (Article.category.ilike(f'%{query}%'))
        )
    if category:
        base_query = base_query.filter_by(category=category)
    
    articles = base_query.order_by(Article.id.desc()).paginate(page=page, per_page=9)
    return render_template('search_page.html',
                         query=query,
                         results=articles.items,
                         active_category=category,
                         page=page)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        try:
            profile_pic_filename = 'default.jpg'
            if form.profile_pic.data:
                file = form.profile_pic.data
                if file.filename == '':
                    flash('No selected file', 'danger')
                    return redirect(request.url)
                
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = ArticleForm()
    if form.validate_on_submit():
        try:
            new_article = Article(
                title=form.title.data,
                content=form.content.data,
                excerpt=form.excerpt.data or form.content.data[:300],
                category=form.category.data,
                author_id=session['user_id']
            )
            db.session.add(new_article)
            db.session.commit()
            flash('Article published successfully!', 'success')
            return redirect(url_for('home_after_login'))
        except Exception as e:
            db.session.rollback()
            flash('Error publishing article. Please try again.', 'danger')
    return render_template('create.html', form=form)

@app.route('/article/<int:id>/like', methods=['POST'])
def like_article(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    article = Article.query.get_or_404(id)
    user_id = session['user_id']
    
    existing_like = Like.query.filter_by(
        user_id=user_id,
        article_id=article.id
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = Like(user_id=user_id, article_id=article.id)
        db.session.add(new_like)
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'likes': len(article.likes),
        'liked': liked
    })

@app.route('/category/<category_name>')
def category_page(category_name):
    valid_categories = ['art', 'culture', 'sport', 'economy', 'technology', 'health', 'entrepreneurship', 'other']
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

@app.route('/home_after_login')
def home_after_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    categories = [
        {'name': 'art', 'description': 'Creative expressions', 'color': '#FF9FEE'},
        {'name': 'culture', 'description': 'Global traditions', 'color': '#B3B0FF'},
        {'name': 'sport', 'description': 'Athletic excellence', 'color': '#FD0261'},
        {'name': 'economy', 'description': 'Market dynamics', 'color': '#aae354'},
        {'name': 'technology', 'description': 'Digital innovations', 'color': '#A4A1AA'},
        {'name': 'health', 'description': 'Mind and body wellness', 'color': '#524F56'},
        {'name': 'entrepreneurship', 'description': 'Startup journeys', 'color': '#252275'},
        {'name': 'other', 'description': 'Miscellaneous gems', 'color': '#91558e'}
    ]
    
    for category in categories:
        category['article_count'] = Article.query.filter_by(category=category['name']).count()
    
    articles = Article.query.order_by(Article.id.desc()).limit(6).all()
    return render_template('home_after_login.html', 
                         categories=categories,
                         articles=articles)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    articles = Article.query.filter_by(author_id=user.id).order_by(Article.id.desc()).all()
    return render_template('profile.html', 
                         user=user,
                         articles=articles)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
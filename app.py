#!/usr/bin/env python3
"""
Complete Flask Blog Application - Single File Solution
Fixed all import issues and database problems
"""

import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash

# Configuration
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'VeryStrongSecretKey123!')

# Database configuration
# Use /tmp for database on Render (ephemeral storage)
# Database will reset on each deployment, but that's OK for this demo
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/blog.db'
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'blog.db')

# Database connection variables
conn = None
cursor = None

def open_db():
    global conn, cursor
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

def close_db():
    if cursor:
        cursor.close()
    if conn:
        conn.close()

def do_query(query, params=None):
    if params is None:
        params = []
    cursor.execute(query, params)
    conn.commit()

# Database functions (fixed versions)
def getUser():
    open_db()
    cursor.execute('''SELECT * FROM user LIMIT 1''')
    user = cursor.fetchone()
    close_db()
    return user

def getAuthData():
    open_db()
    cursor.execute('''SELECT * FROM users LIMIT 1''')
    data = cursor.fetchone()
    close_db()
    if data:
        return {'login': data[0], 'password': data[1]}
    return None

def getPostsByCategory(category_name):
    open_db()
    cursor.execute('''SELECT p.*, c.category_name 
                     FROM post p, category c 
                     WHERE p.category_id = c.category_id 
                     AND c.category_name = ? 
                     ORDER BY p.post_id DESC''', [category_name])
    posts = cursor.fetchall()
    close_db()
    return posts

def getIdByCategory(category_name):
    open_db()
    cursor.execute('''SELECT category_id FROM category WHERE category_name = ?''', [category_name])
    result = cursor.fetchone()
    close_db()
    if result:
        return result['category_id']
    else:
        return None

def addPost(category_id, post_text):
    open_db()
    cursor.execute('''INSERT INTO post (category_id, text) VALUES (?, ?)''', [category_id, post_text])
    conn.commit()
    close_db()

def get_all_posts():
    open_db()
    cursor.execute('''SELECT p.*, c.category_name 
                     FROM post p 
                     JOIN category c ON p.category_id = c.category_id 
                     ORDER BY p.post_id DESC''')
    posts = cursor.fetchall()
    close_db()
    return posts

# Initialize database
def init_database():
    """Initialize database with tables and sample data"""
    open_db()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES category (category_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            name TEXT,
            text TEXT,
            image TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            login TEXT,
            password TEXT
        )
    ''')
    
    # Insert sample categories
    categories = [('tech',), ('lifestyle',), ('creative',)]
    for cat in categories:
        cursor.execute('INSERT OR IGNORE INTO category (category_name) VALUES (?)', cat)
    
    # Insert sample user data
    cursor.execute('''INSERT OR REPLACE INTO user (id, name, text, image) 
                      VALUES (1, 'John Doe', 'Welcome to my personal blog where I share thoughts about technology, lifestyle, and creativity. Join me on this journey of discovery and learning!', NULL)''')
    
    # Insert sample auth data
    cursor.execute('''INSERT OR REPLACE INTO users (login, password) 
                      VALUES ('admin', 'password123')''')
    
    # Insert some sample posts
    sample_posts = [
        (1, 'The Future of Web Development: Exploring new frameworks and technologies that are shaping how we build websites. From AI integration to improved performance, the web is evolving rapidly.'),
        (1, 'Understanding Python Flask: A comprehensive guide to building web applications with Flask. Learn about routing, templates, and database integration step by step.'),
        (2, 'Mindful Living in the Digital Age: How to maintain balance while staying connected. Tips for reducing screen time and improving mental well-being in our modern world.'),
        (2, 'Healthy Morning Routines: Start your day right with these simple but effective habits that can transform your productivity and mood throughout the day.'),
        (3, 'The Art of Creative Writing: Techniques for developing compelling characters and engaging storylines that keep readers hooked from start to finish.'),
        (3, 'Photography as Self-Expression: Capturing moments and emotions through the lens. Learn composition techniques and develop your unique photographic style.')
    ]
    
    for category_id, text in sample_posts:
        cursor.execute('SELECT COUNT(*) FROM post WHERE category_id = ? AND text = ?', (category_id, text))
        if cursor.fetchone()[0] == 0:  # Only insert if doesn't exist
            cursor.execute('INSERT INTO post (category_id, text) VALUES (?, ?)', (category_id, text))
    
    conn.commit()
    close_db()

# HTML Templates with lower positioning
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title if title else 'My Blog' }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Header with more space */
        header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 2.2rem;
            font-weight: bold;
            color: white;
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 2.5rem;
        }

        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            transition: all 0.3s ease;
            font-size: 1.1rem;
        }

        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* Hero Section with more vertical space */
        .hero {
            text-align: center;
            padding: 6rem 0;
            color: white;
            margin-bottom: 2rem;
        }

        .hero h1 {
            font-size: 4rem;
            margin-bottom: 2rem;
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero p {
            font-size: 1.4rem;
            margin-bottom: 3rem;
            opacity: 0.9;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        .cta-button {
            display: inline-block;
            padding: 18px 40px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.2rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }

        /* Main Content with more top margin */
        .main-content {
            background: white;
            margin: 4rem 0;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }

        /* Categories Section */
        .categories {
            padding: 4rem 3rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }

        .categories h2 {
            text-align: center;
            margin-bottom: 3rem;
            color: #333;
            font-size: 3rem;
        }

        .category-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 3rem;
            margin-top: 3rem;
        }

        .category-card {
            background: white;
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .category-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(45deg, #667eea, #764ba2);
        }

        .category-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        }

        .category-card h3 {
            margin-bottom: 1.5rem;
            color: #333;
            font-size: 1.8rem;
        }

        .category-card p {
            color: #666;
            margin-bottom: 2rem;
            font-size: 1.1rem;
            line-height: 1.7;
        }

        .read-more {
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
            font-size: 1.1rem;
        }

        .read-more:hover {
            transform: translateX(5px);
        }

        /* Posts Section */
        .posts-section {
            padding: 4rem 3rem;
        }

        .posts-section h2 {
            text-align: center;
            margin-bottom: 3rem;
            color: #333;
            font-size: 3rem;
        }

        .posts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 3rem;
        }

        .post-card {
            background: #f8f9fa;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }

        .post-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }

        .post-image {
            height: 120px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            position: relative;
        }

        .post-content {
            padding: 2rem;
        }

        .post-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            color: #666;
            font-size: 1rem;
        }

        .post-text {
            color: #666;
            line-height: 1.7;
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
        }

        /* Add Post Form */
        .add-post-form {
            background: #f8f9fa;
            padding: 3rem;
            border-radius: 15px;
            margin-bottom: 3rem;
        }

        .add-post-form h3 {
            font-size: 2rem;
            margin-bottom: 2rem;
            color: #333;
        }

        .form-group {
            margin-bottom: 2rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 1rem;
            font-weight: bold;
            color: #333;
            font-size: 1.2rem;
        }

        .form-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1.1rem;
            transition: border-color 0.3s ease;
            resize: vertical;
            min-height: 150px;
        }

        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .submit-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 25px;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        /* Category Hero */
        .category-hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 5rem 0;
        }

        .category-hero h1 {
            font-size: 3rem;
            margin-bottom: 1.5rem;
        }

        .category-hero p {
            font-size: 1.3rem;
            opacity: 0.9;
        }

        .no-posts {
            text-align: center;
            padding: 4rem;
            color: #666;
            font-style: italic;
            font-size: 1.2rem;
        }

        .about-section {
            padding: 4rem 3rem;
            background: #f8f9fa;
            text-align: center;
        }

        .about-section h2 {
            margin-bottom: 3rem;
            color: #333;
            font-size: 3rem;
        }

        .about-section p {
            font-size: 1.2rem;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
        }

        /* Flash Messages */
        .flash-messages {
            padding: 2rem 0;
        }

        .flash {
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.1rem;
        }

        .flash.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .flash.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        /* Footer */
        footer {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            text-align: center;
            padding: 3rem 0;
            margin-top: 4rem;
            font-size: 1.1rem;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .nav-links {
                flex-direction: column;
                gap: 1rem;
            }

            .hero h1 {
                font-size: 2.5rem;
            }

            .hero p {
                font-size: 1.1rem;
            }

            .category-grid,
            .posts-grid {
                grid-template-columns: 1fr;
            }

            .container {
                padding: 0 15px;
            }

            .hero {
                padding: 4rem 0;
            }

            .categories, .posts-section {
                padding: 3rem 2rem;
            }

            .category-card, .add-post-form {
                padding: 2rem;
            }
        }
    </style>
</head>
<body>
    <header>
        <nav class="container">
            <a href="/" class="logo">MyBlog</a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/post/category/tech">Tech</a></li>
                <li><a href="/post/category/lifestyle">Lifestyle</a></li>
                <li><a href="/post/category/creative">Creative</a></li>
                <li><a href="/post/view">All Posts</a></li>
            </ul>
        </nav>
    </header>

    <main>
        {{ flash_messages|safe }}
        {{ content|safe }}
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 MyBlog. Made with ❤️ using Flask & Python</p>
        </div>
    </footer>

    <script>
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Form validation
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const textArea = form.querySelector('textarea[name="post"]');
                    if (textArea && !textArea.value.trim()) {
                        e.preventDefault();
                        alert('Please write something before submitting');
                        textArea.focus();
                    }
                });
            });
        });
    </script>
</body>
</html>
'''

# Routes
@app.route("/")
@app.route("/index")
def index():
    user = getUser()
    flash_messages = render_flash_messages()
    
    content = f'''
    <!-- Hero Section with more space -->
    <section class="hero">
        <div class="container">
            <h1>Welcome to My Blog</h1>
            {"<p>Hello, I'm " + user['name'] + "! Discover amazing stories, insights, and experiences from my journey.</p>" if user and user['name'] else "<p>Discover amazing stories, insights, and experiences from around the world. Join our community of writers and readers.</p>"}
            <a href="#content" class="cta-button">Explore Content</a>
        </div>
    </section>

    <!-- Main Content positioned lower -->
    <div class="main-content container" id="content">
        <!-- Categories Section -->
        <section class="categories">
            <h2>Explore Categories</h2>
            <div class="category-grid">
                <div class="category-card">
                    <h3>Technology</h3>
                    <p>Latest trends in tech, programming tutorials, web development insights, and digital innovations that are shaping our future. From AI to blockchain, explore the cutting edge.</p>
                    <a href="/post/category/tech" class="read-more">Read Tech Posts →</a>
                </div>
                <div class="category-card">
                    <h3>Lifestyle</h3>
                    <p>Tips for better living, health and wellness advice, travel experiences, productivity hacks, and personal development insights to help you live your best life.</p>
                    <a href="/post/category/lifestyle" class="read-more">Read Lifestyle Posts →</a>
                </div>
                <div class="category-card">
                    <h3>Creative Writing</h3>
                    <p>Stories, poetry, creative essays, artistic expressions, writing techniques, and imaginative content that inspires creativity and entertains the soul.</p>
                    <a href="/post/category/creative" class="read-more">Read Creative Posts →</a>
                </div>
            </div>
        </section>

        {"<section class='about-section'><h2>About " + (user['name'] if user and user['name'] else 'This Blog') + "</h2><p>" + user['text'] + "</p><div style='margin-top: 2rem;'><a href='/post/view' class='cta-button'>View All Posts</a></div></section>" if user and user['text'] else ""}
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE, 
                                title="Welcome - My Blog",
                                flash_messages=flash_messages,
                                content=content)

@app.route('/post/category/<category_name>', methods=['GET', 'POST'])
def postCategory(category_name):
    category_id = getIdByCategory(category_name)
    
    if not category_id:
        flash(f'Category "{category_name}" not found!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        post_text = request.form.get('post', '').strip()
        if post_text:
            addPost(category_id, post_text)
            flash('Your post has been published successfully!', 'success')
        else:
            flash('Please write something before submitting.', 'error')
        return redirect(url_for('postCategory', category_name=category_name))
    
    posts = getPostsByCategory(category_name)
    flash_messages = render_flash_messages()
    
    posts_html = ''
    if posts:
        posts_html = '<div class="posts-grid">'
        for post in posts:
            posts_html += f'''
            <article class="post-card">
                <div class="post-image"></div>
                <div class="post-content">
                    <div class="post-meta">
                        <span>{post["category_name"].title()}</span>
                        <span>Post #{post["post_id"]}</span>
                    </div>
                    <div class="post-text">
                        {post["text"]}
                    </div>
                </div>
            </article>
            '''
        posts_html += '</div>'
    else:
        posts_html = '''
        <div class="no-posts">
            <h3>No posts yet in ''' + category_name.title() + '''</h3>
            <p>Be the first to share something amazing! Use the form above to write your first ''' + category_name + ''' post.</p>
            <div style="margin-top: 2rem;">
                <a href="/" class="cta-button">← Back to Home</a>
            </div>
        </div>
        '''
    
    content = f'''
    <!-- Category Hero positioned lower -->
    <section class="category-hero">
        <div class="container">
            <h1>{category_name.title()} Posts</h1>
            <p>Explore all posts in the {category_name} category. Share your thoughts and discover new perspectives.</p>
        </div>
    </section>

    <!-- Main content with more spacing -->
    <div class="main-content container">
        <!-- Add New Post Form -->
        <section class="add-post-section">
            <div class="add-post-form">
                <h3>Share Your {category_name.title()} Thoughts</h3>
                <p style="margin-bottom: 2rem; color: #666; font-size: 1.1rem;">
                    Have something interesting to share about {category_name}? Write your thoughts below and contribute to our community!
                </p>
                <form method="POST">
                    <div class="form-group">
                        <label for="post">Your {category_name.title()} Post:</label>
                        <textarea 
                            name="post" 
                            id="post" 
                            placeholder="Write your {category_name} thoughts here... Share your insights, experiences, or questions!" 
                            required></textarea>
                    </div>
                    <button type="submit" class="submit-btn">Publish Post</button>
                </form>
            </div>
        </section>

        <!-- Posts Section -->
        <section class="posts-section">
            <h2>{category_name.title()} Posts Collection</h2>
            <p style="text-align: center; margin-bottom: 3rem; color: #666; font-size: 1.2rem;">
                {"Showing " + str(len(posts)) + " post" + ("s" if len(posts) != 1 else "") + " in " + category_name if posts else "No posts yet in this category"}
            </p>
            
            {posts_html}
        </section>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE,
                                title=f"{category_name.title()} Posts - My Blog",
                                flash_messages=flash_messages,
                                content=content)

@app.route("/post/view")
def postView():
    all_posts = get_all_posts()
    flash_messages = render_flash_messages()
    
    posts_html = ''
    if all_posts:
        posts_html = '<div class="posts-grid">'
        for post in all_posts:
            posts_html += f'''
            <article class="post-card">
                <div class="post-image"></div>
                <div class="post-content">
                    <div class="post-meta">
                        <span>{post["category_name"].title()}</span>
                        <span>Post #{post["post_id"]}</span>
                    </div>
                    <div class="post-text">
                        {post["text"]}
                    </div>
                    <a href="/post/category/{post["category_name"]}" class="read-more">
                        More {post["category_name"].title()} Posts →
                    </a>
                </div>
            </article>
            '''
        posts_html += '</div>'
    else:
        posts_html = '''
        <div class="no-posts">
            <p>No posts available yet. Start by adding some content!</p>
            <div style="margin-top: 2rem;">
                <a href="/" class="cta-button">← Back to Home</a>
            </div>
        </div>
        '''
    
    content = f'''
    <section class="category-hero">
        <div class="container">
            <h1>All Blog Posts</h1>
            <p>Browse through all blog posts from every category</p>
        </div>
    </section>

    <div class="main-content container">
        <section class="posts-section">
            <h2>All Blog Posts ({len(all_posts)})</h2>
            {posts_html}
        </section>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE,
                                title="All Posts - My Blog",
                                flash_messages=flash_messages,
                                content=content)

@app.route("/about")
def about():
    return redirect(url_for('index'))

def render_flash_messages():
    messages = ''
    with app.app_context():
        flashed = flash._get_flashed_messages() if hasattr(flash, '_get_flashed_messages') else []
        if flashed:
            messages = '<div class="flash-messages container">'
            for category, message in flashed:
                messages += f'<div class="flash {category}">{message}</div>'
            messages += '</div>'
    return messages

if __name__ == "__main__":
    # Initialize database on first run
    init_database()
    print("🚀 Blog application starting...")
    print("📝 Database initialized with sample data")
    
    # Use environment PORT for production (Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🌐 Server running on port: {port}")
    print("📱 Features available:")
    print("   • Home page")
    print("   • Tech posts: /post/category/tech")
    print("   • Lifestyle posts: /post/category/lifestyle") 
    print("   • Creative posts: /post/category/creative")
    print("   • All posts: /post/view")
    
    app.run(debug=False, port=port, host='0.0.0.0')
else:
    # Initialize database when running with gunicorn
    init_database()

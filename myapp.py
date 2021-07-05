from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRETE_KEY'] = 'notez2hack'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)
db: SQLAlchemy


class Post(db.Model):
    __tablename__ = 'post'
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'))


class Author(db.Model):
    __tablename__ = 'author'
    author_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    admin = db.Column(db.Boolean)
    posts = db.relationship('Post')

# create db structure using classes above and add db admin
# db.drop_all()
# db.create_all()
# author = Author(name='Nando', email='nando@nando.com',
#                 password='asdfgqwert', admin=True)
# db.session.add(author)
# db.session.commit()


def mandatory_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        # Verify if there is token in the request
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # if there is no token, return the request and ask for a token
        if not token:
            return jsonify({'message': 'This request need a authentication token'})
        try:
            data = jwt.decode(token, app.config['SECRETE_KEY'])
            active_author = Author.query.filter_by(author_id=data['author_id']).first()
        except:
             return jsonify({'message': 'Invalid token'}, 401)
        return func(active_author, *args, **kwargs)
    return decorated


@app.route('/posts', methods=['GET'])
@mandatory_token
def get_all_posts(active_author):
    posts = Post.query.all()

    posts_list = []
    for post in posts:
        post_data = {}
        post_data['title'] = post.title
        post_data['author_id'] = post.author_id
        posts_list.append(post_data)

    return jsonify({'posts': posts_list})


@app.route('/posts/<int:post_id>', methods=['GET'])
@mandatory_token
def get_post_by_id(active_author, post_id):
    post = Post.query.filter_by(post_id=post_id).first()

    post_data = {}
    post_data['title'] = post.title
    post_data['author_id'] = post.author_id

    return jsonify({'posts': post_data})


@app.route('/posts', methods=['POST'])
@mandatory_token
def new_post(active_author):
    data = request.get_json()
    new_post = Post(title=data['title'], author_id=data['author_id'])  
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': 'New post created successfully'})


@app.route('/posts/<int:post_id>', methods=['PUT'])
@mandatory_token
def update_post(active_author, post_id):
    post = Post.query.filter_by(post_id=post_id).first()

    if not post:
        return jsonify({'message': 'Post not found'})

    post_data = request.get_json()
    post.title = post_data['title']
    db.session.commit()

    return jsonify({'message': 'Post has been updated'})


@app.route('/posts/<int:post_id>', methods=['DELETE'])
@mandatory_token
def delete_post(active_author, post_id):
    post = Post.query.filter_by(post_id=post_id).first()

    if not post:
        return jsonify({'message': 'Post not found'})

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post has been deleted'})


# api authors

@app.route('/authors', methods=['GET'])
@mandatory_token
def get_all_authors(active_author):
    authors = Author.query.all()
    authors_list = []
    for author in authors:
        authors_data = {}
        authors_data['author_id'] = author.author_id
        authors_data['name'] = author.name
        authors_data['email'] = author.email
        authors_list.append(authors_data)
    return jsonify({'authors': authors_list})


@app.route('/authors/<int:author_id>', methods=['GET'])
@mandatory_token
def get_author_by_id(active_author, author_id):
    author = Author.query.filter_by(author_id=author_id).first()

    if not author:
        return jsonify({'message': 'Author not found'})

    author_data = {}
    author_data['author_id'] = author.author_id
    author_data['name'] = author.name
    author_data['email'] = author.email

    return jsonify({'author': author_data})


@app.route('/authors', methods=['POST'])
@mandatory_token
def new_author(active_author):
    data = request.get_json()

    new_author = Author(name=data['name'], password=data['password'],
                        email=data['email'])  
    db.session.add(new_author)
    db.session.commit()

    return jsonify({'message': 'New user created successfully'})


@app.route('/authors/<int:author_id>', methods=['PUT'])
@mandatory_token
def update_author(active_author, author_id):
    author = Author.query.filter_by(author_id=author_id).first()

    if not author:
        return jsonify({'message': 'Author not found'})

    author_data = request.get_json()
    author.name = author_data['name']
    author.email = author_data['email']
    db.session.commit()

    return jsonify({'message': 'Author has been updated'})


@mandatory_token
@app.route('/authors/<int:author_id>', methods=['DELETE'])
def delete_author(active_author, author_id):
    author = Author.query.filter_by(author_id=author_id).first()

    if not author:
        return jsonify({'message': 'Author not found'})

    db.session.delete(author)
    db.session.commit()

    return jsonify({'message': 'Author has been deleted'})


@app.route('/login')
def login():
    authentication_data = request.authorization

    if not authentication_data or not authentication_data.username or not authentication_data.password:
        return make_response('Invalid login', 401, {'WWW-Authenticate': 'Basic realm="You must be logged in."'})

    user = Author.query.filter_by(name=authentication_data.username).first()
    if user.password == authentication_data.password:
        token = jwt.encode({'author_id': user.author_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRETE_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Invalid login', 401, {'WWW-Authenticate': 'Basic realm="You must be logged in."'})


if __name__ == '__main__':
    app.run(debug=True)

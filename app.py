import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.utils import secure_filename
from config import Config

# ================= APP CONFIG =================

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ================= MODELS =================


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    image = db.Column(db.String(300))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    product_name = db.Column(db.String(200))
    total_price = db.Column(db.Float)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================= ROUTES =================


@app.route("/")
def home():
    products = Product.query.all()
    return render_template("home.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"], password=request.form["password"]
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            login_user(user)
            flash(f"Welcome, {user.username}!")
            return redirect(url_for("home"))
        flash("Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect(url_for("home"))


@app.route("/products")
def products():
    products = Product.query.all()
    return render_template("products.html", products=products)


@app.route("/product/<int:id>")
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template("product_detail.html", product=product)


# ================= ADD PRODUCT =================


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        file = request.files.get("image")
        filename = None
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        product = Product(
            name=request.form["name"],
            price=request.form["price"],
            description=request.form["description"],
            image=filename,
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully!")
        return redirect(url_for("products"))
    return render_template("add_product.html")


# ================= EDIT PRODUCT =================


@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.price = request.form["price"]
        product.description = request.form["description"]

        file = request.files.get("image")
        if file and file.filename != "":
            # ลบรูปเก่า
            if product.image:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], product.image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            product.image = filename

        db.session.commit()
        flash("Product updated successfully!")
        return redirect(url_for("products"))

    return render_template("edit_product.html", product=product)


# ================= DELETE PRODUCT =================


@app.route("/delete_product/<int:id>")
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.image:
        path = os.path.join(app.config["UPLOAD_FOLDER"], product.image)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!")
    return redirect(url_for("products"))


# ================= CHECKOUT =================


@app.route("/checkout/<int:id>")
@login_required
def checkout(id):
    product = Product.query.get_or_404(id)
    order = Order(
        user_id=current_user.id, product_name=product.name, total_price=product.price
    )
    db.session.add(order)
    db.session.commit()
    flash("Order placed successfully!")
    return redirect(url_for("orders"))


@app.route("/orders")
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("orders.html", orders=orders)


# ================= MAIN =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

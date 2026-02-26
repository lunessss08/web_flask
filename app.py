from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Product, Category
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# App Configuration
# =========================

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# =========================
# Login Manager Setup
# =========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# Create Database & Default Categories
# =========================

with app.app_context():
    db.create_all()
    if not Category.query.first():
        # สร้างหมวดหมู่เริ่มต้น
        db.session.add(Category(name="Electronics"))
        db.session.add(Category(name="Books"))
        db.session.add(Category(name="Services"))
        db.session.commit()

# =========================
# Routes
# =========================


@app.route("/")
def home():
    return render_template("home.html")


# ---------- Register ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")


# ---------- Logout ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully")
    return redirect(url_for("home"))


# ---------- Dashboard ----------
@app.route("/dashboard")
@login_required
def dashboard():
    products = Product.query.all()
    return render_template("dashboard.html", products=products)


# ---------- Products with Search ----------
@app.route("/products")
def products():
    search = request.args.get("search")

    if search:
        products = Product.query.filter(Product.name.contains(search)).all()
    else:
        products = Product.query.all()

    return render_template("products.html", products=products)


# ---------- Product Detail ----------
@app.route("/product/<int:id>")
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template("product_detail.html", product=product)


# ---------- Add Product ----------
@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Category.query.all()

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form["description"]
        category_id = int(request.form["category_id"])
        image = request.form["image"]  # ใช้ URL รูป

        product = Product(
            name=name,
            price=price,
            description=description,
            category_id=category_id,
            image=image,
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully")
        return redirect(url_for("dashboard"))

    return render_template("add_product.html", categories=categories)


# ---------- Edit Product ----------
@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name = request.form["name"]
        product.price = float(request.form["price"])
        product.description = request.form["description"]
        product.category_id = int(request.form["category_id"])
        product.image = request.form["image"]

        db.session.commit()
        flash("Product updated successfully")
        return redirect(url_for("dashboard"))

    return render_template("edit_product.html", product=product, categories=categories)


# ---------- Delete Product ----------
@app.route("/delete_product/<int:id>")
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully")
    return redirect(url_for("dashboard"))


# ---------- About ----------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------- Contact ----------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================
# Run App
# =========================

if __name__ == "__main__":
    app.run(debug=True)

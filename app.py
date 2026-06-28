from flask import Flask,redirect,render_template,request,jsonify,url_for,make_response
import os
#working with .env variables
from dotenv import load_dotenv
#local development database
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect,FlaskForm
#hash passwords
from flask_bcrypt import Bcrypt
#implement JWT Authentication
from flask_jwt_extended import(
    JWTManager,
    #generate jwt token
    create_access_token,
    #access jwt identity from current user
    get_jwt_identity,
    #requrie jwt to access route
    jwt_required,
    unset_jwt_cookies,
    set_access_cookies
)
from wtforms import EmailField,StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired,Email,EqualTo,Length
from flask_migrate import Migrate

#initialize .env variables
load_dotenv()
#initialize app with flask
app=Flask(__name__)
#load database_url
app.config['SQLALCHEMY_DATABASE_URI']=os.getenv("DATABASE_URL")
#configure jwt cookies
app.config["JWT_TOKEN_LOCATION"]=["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"]="access_token"
app.config["JWT_COOKIE_SECURE"]=False
app.config["JWT_COOKIE_CSRF_PROTECT"]=False
#use secret_key for CRSF Protection
app.config["SECRET_KEY"]=os.getenv("CSRF_KEY")
#use jwt tools
app.config["JWT_SECRET_KEY"]=os.getenv("JWT_SECRET_KEY")
csrf=CSRFProtect()
csrf.init_app(app)
#initialize app with local development database
db=SQLAlchemy(app)
#initialize app and db migrations
migrate=Migrate(app,db)
#initialize app with jwt
jwt=JWTManager()
jwt.init_app(app)
bcrypt=Bcrypt(app)
# #initialize app to use login manager
# login_manager=LoginManager()
# login_manager.init_app(app)
# login_manager.login_view="login"
@app.route("/register",methods=["POST","GET"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        print("Form validated")
        username=form.username.data
        email=form.email.data
        password=form.password.data
        #check if user exists
        user=Users.query.filter_by(username=username).first()
        if user:
            return jsonify({
                "Message":"User already exists"
            }),409
        email_exists=Users.query.filter_by(email=email).first()
        if email_exists:
            return jsonify({
                "message":"Email already registered"
            }),409
        hashed_password=bcrypt.generate_password_hash(password).decode("utf-8")
        new_user=Users(username=username,email=email,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        # access_token=create_access_token(identity=str(new_user.id))
        return redirect(url_for('login'))
        # return jsonify({
        #     "message":"User registered successfully",
        #     "access_token":access_token
        # }),201
    return render_template("register.html",form=form)
@app.route("/login",methods=["POST","GET"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        user=Users.query.filter_by(username=username).first()
        if not user:
            return "User not found",404
            # return jsonify({
            #     "message":"User not found"
            # }),404
        if not bcrypt.check_password_hash(user.password,password):
            return "Invalid password",401

        access_token=create_access_token(identity=str(user.id))
        response=make_response(
            redirect(url_for('dashboard'))

        )
        set_access_cookies(response,access_token)
        # response.set_cookie(
        #     "access_token",
        #     access_token,
        #     httponly=True
        # )
        return response
    return render_template("login.html",form=form)
@app.route("/dashboard",methods=["POST","GET"])
# @login_required
@jwt_required()
def dashboard():
    user_id=get_jwt_identity()
    # user=Users.query.get(int(user))
    #fetch user from the database
    user=db.session.get(Users,int(user_id))
    if not user:
        return redirect(url_for('login'))
    
    return render_template("dashboard.html",user=user)
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/logout")
def logout():
    response=make_response(redirect(url_for("login")))
    unset_jwt_cookies(response)
    return response
@jwt.unauthorized_loader
def unauthorized_callback(reason):
    return redirect(url_for("login"))

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return redirect(url_for("login"))

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return redirect(url_for("login"))
#register form 
class RegisterForm(FlaskForm):
    username=StringField("Username",validators=[InputRequired(),Length(min=4)])
    email=EmailField("Email address",validators=[InputRequired(),Email()])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=8)])
    confirm_password=PasswordField("Confirm password",validators=[InputRequired(),EqualTo("password",message="Passwords must match")])
    submit=SubmitField("Register")
#login form
class LoginForm(FlaskForm):
    username=StringField("Username",validators=[InputRequired(),Length(min=4)])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=8)])
    submit=SubmitField("Login")
#create database models
class Users(db.Model):
    __tablename__="Users"
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),nullable=False,unique=True)
    email=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(255),nullable=False)
#load these automatically
@app.shell_context_processor
def make_shell_contect():
    return{
        "db":db,
        "Users":Users
    }
#run app if being executed from current script
if __name__=="__main__":
    with app.app_context():
        db.create_all()
    #allow debug mode
    app.run(debug=True)
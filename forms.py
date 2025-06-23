from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ConfessionForm(FlaskForm):
    content = TextAreaField('Your Confession', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Submit Confession')

class CommentForm(FlaskForm):
    content = TextAreaField('Your Comment', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Post Comment')

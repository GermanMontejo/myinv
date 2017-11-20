from __future__ import print_function
import xml.dom.minidom
from io import StringIO,BytesIO
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, SimpleDocTemplate
from reportlab.lib.pagesizes import letter
from BeautifulSoup import BeautifulSoup as bs
from PDFOrder import PDFOrder
from flask import Flask, render_template, request, url_for, redirect, session, flash, Markup, make_response 
from dbconnect import connection
from wtforms import Form, BooleanField, TextField, PasswordField, validators, SelectField, IntegerField, TextAreaField, DecimalField, HiddenField, SubmitField, FileField
from wtforms.fields.html5 import DateField
from wtforms.validators import Required
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc
import datetime
from content_management import Content, SelectSupplier, SelectCustomer, SelectGoodsrec, SelectBank, SelectBankId, SelectCustomerId, SelectGoodsrecId, SelectSupplierId, SelectInvoiceId, SelectGoodsrecSEE
from functools import wraps
from XmlGenerator import XmlGenerator
from ZugXmlGenerator import ZugXmlGenerator
from flask_mail import Mail, Message
import datetime
from datetime import datetime,timedelta
from time import mktime
import logging
from logging.handlers import RotatingFileHandler
import re
import sys
import os
import requests

from flask import jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory
import shutil
import glob
from flask_babel import Babel
from flask_babel import gettext, lazy_gettext




reload(sys)
sys.setdefaultencoding('utf8')




app = Flask(__name__)



#  for dashboard tabs information (my data, etc.)
TOPIC_DICT = Content()

#EMail settings#
app = Flask(__name__)

app.config.update(
	DEBUG=False,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'myinvsender@gmail.com',
	MAIL_PASSWORD = 'SCRET'
	)
mail = Mail(app)

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch',
    'es': 'Espanol'
    
}

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())

        

#Index
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/terms/')
def terms():
    return render_template("terms.html")



#Homepage
@app.route('/home/')
def home():
    return render_template("index.html")


# Wrapper for certain URLS which require the user to be logged in. 
	
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash(gettext("Please, log in first"))
            return redirect(url_for('signin'))

    return wrap

### wrapper for protected folder
def special_requirement(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		try:
			if 'mwell' == session['username']:
				return f(*args, **kwargs)
			else:
				return redirect(url_for('dashboard'))
		except:
			return redirect(url_for('dashboard'))
	return wrap

#errorhandler for 404: page not found

@app.errorhandler(404)
def page_not_found(e):
    message = Markup(lazy_gettext('<b>This page doesnt exist.</b><br>Please, go back to the <a href="/dashboard" class="alert-link">dashboard</a>'))
    flash(message)
    return render_template("404.html")

@app.errorhandler(500)
def page_not_found(e):
    message = Markup(gettext('<b>There was an unexpected error</b><br>Please, go back to the <a href="/dashboard" class="alert-link">dashboard</a>'))
    flash(message)
    return render_template("500.html")



##for robots
@app.route('/robots.txt/')
def robots():
    return("User-agent: *\nDisallow: /signup/\nDisallow: /login/\nDisallow: /terms/")


## to be found by google##
@app.route('/google9f47833d7363c6b3.html')
def google():
    return render_template("google9f47833d7363c6b3.html")

@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    try:
      """Generate sitemap.xml. Makes a list of urls and date modified."""
      pages=[]
      ten_days_ago=(datetime.now() - timedelta(days=7)).date().isoformat()
      # static pages
      for rule in app.url_map.iter_rules():
          if "GET" in rule.methods and len(rule.arguments)==0:
              pages.append(
                           ["http://www.myinv.org"+str(rule.rule),ten_days_ago]
                           )

      sitemap_xml = render_template('sitemap_template.xml', pages=pages)
      response= make_response(sitemap_xml)
      response.headers["Content-Type"] = "application/xml"    
    
      return response
    except Exception as e:
        return(str(e))

    





## Dashboard, with variables which go from flask to HTML (TOPICDICT, MYSQL1, etc.)
## note loginrequired.
@app.route('/dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    mySQL1 = SelectSupplier(session['ID']) #displayed my data
    mySQL2 = SelectCustomer(session['ID']) #displayed invoicereceiver
    mySQL3 = SelectGoodsrec(session['ID']) #displayed goodsreceiver
    
    return render_template("dashboard.html", TOPIC_DICT = TOPIC_DICT, mySQL1 = mySQL1, mySQL2 = mySQL2, mySQL3 = mySQL3)


@app.route('/seegoodsrec/', methods=['GET', 'POST'])
@login_required
def seegoodsrec():
    customerID = request.form.get('customerID')
    mySQL3 = SelectGoodsrec(session['ID']) #displayed goodsreceiver with user ID
    mySQL8 = SelectGoodsrecSEE(customerID)
    c, conn = connection()

    x = c.execute("SELECT * FROM goodsrec WHERE Gr_Cm_id = %s", [thwart(str(customerID))])
                          
    if int(x) < 1:
        flash(gettext("Please, create a delivery address for this customer"))
        
    
    
    return render_template("seegoodsrec.html", TOPIC_DICT = TOPIC_DICT,  mySQL3 = mySQL3, customerID=customerID, mySQL8 = mySQL8, x=x)

@app.route('/seebank/')
@login_required
def seebank():
    mySQL4 = SelectBank(session['ID']) 
    return render_template("seebank.html", TOPIC_DICT = TOPIC_DICT,  mySQL4 = mySQL4)

#Logout button
## note loginrequired.
@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash(gettext("You successfully logged out"))
    gc.collect()
    return redirect(url_for('index'))



	
###USER REGISTRATION###
##Registration form##
class RegistrationForm(Form):
    username = TextField(lazy_gettext('Username'), [validators.Length(min=4, max=20)])
    email = TextField(lazy_gettext('Email Address'), [validators.Length(min=6, max=50)])
    password = PasswordField(lazy_gettext('Password'), [
        validators.Required(),
        validators.EqualTo('confirm', message=lazy_gettext('Passwords must match'))
    ])
    confirm = PasswordField(lazy_gettext('Repeat Password'))
    accept_tos = BooleanField(lazy_gettext('I accept the <a href="/terms/" target="_blank">Terms of Service and Privacy Policy</a>'), [validators.Required()])
 
## Registration URL, insert in DB and check if username is already taken.
## Connection to DB established with db_connect.py
@app.route('/signup/', methods=['GET','POST'])
def signup():
    try:
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute("SELECT * FROM user_login WHERE Us_username = (%s)",
                          [(thwart(username))])
            
            
            
            if int(x) > 0:
                flash(lazy_gettext("That username is already taken, please choose another "))
                return render_template('signup.html', form=form)
            else:
                c.execute("INSERT INTO user_login (Us_username, Us_password, Us_email, Us_tracking) VALUES (%s, %s, %s, %s)",
                          (thwart(username), thwart(password), thwart(email), thwart("/dashboard/")))
                
                conn.commit()
                message = Markup(gettext("Dear <b>") +str(username)+gettext("</b>, <br><b>Thanks</b> for signin up to myinv!<br><br> These messages will guide you through the application.<br>You can close them as you go. <br><br>Use the dashboard to create your <b>e-invoice</b> and administrate your data."))
                flash(message)
                
                c.close()
                conn.close()
                gc.collect()

                c, conn = connection()
                session['logged_in'] = True
                session['username'] = username
                queryResult = c.execute("SELECT * FROM user_login WHERE Us_username = (%s)",
                                          [thwart(request.form['username'])])
                session['ID'] =  c.fetchone()[0]
                c.close()
                conn.close()
                gc.collect()
                
                return redirect(url_for('dashboard'))
            
        message = Markup(gettext('Complete the form<br> <br> <b>These messages are a help as you go</b>'))
        flash(message)
        #flash(gettext('Invalid login. Please try again.'))
        return render_template("signup.html", form=form)

    except Exception as e:
        return(str(e)) 
        

## LOGIN PAGE## request.form comes from HTML. 
## Saving session[ID] and username
@app.route('/signin/', methods=['GET','POST'])
def signin():
    try:        
        c,conn = connection()
        
        error = None
        if request.method == 'POST':

            data = c.execute("SELECT * FROM user_login WHERE Us_username = (%s)",
                    [thwart(request.form['username'])])
            data = c.fetchone()[2]
#Obtaining session ID which is foreign key for supplier and primary key for userlogin
            session['ID'] = c.execute("SELECT * FROM user_login WHERE Us_username = (%s)",
                                          [thwart(request.form['username'])])
            session['ID'] =  c.fetchone()[0]
            

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                message = Markup(gettext("Dear <b>") +str(session['username'])+ gettext("</b>, <br> Thanks for using myinv!<br><br> These messages will guide you through the application.<br>You can close them as you go. <br><br>Use the dashboard to create your <b>e-invoice</b> and administrate your data."))
                flash(message)
                #flash('Thanks for using myinv!" +\n+ "\n\nUse the dashboard to create your e-invoice and adminstrate your data.")
                return redirect(url_for('dashboard'))

            else:
                error = gettext("The credentials are invalid. Contact for help: myinvsender@gmail.com")
        gc.collect()
        message = Markup(gettext("Log in with your credentials<br><br> <b>These messages are a help as you go</b>"))
        flash(message)
        return render_template('signin.html', error=error)
    except Exception, e:
        error = gettext("The credentials are invalid. Contact for help: myinvsender@gmail.com")
        
        return render_template('signin.html', error=error)



    
#### MY DATA #####
    ##CREATE##
##Form##
class CreatemydataForm(Form):
    name = TextField(lazy_gettext('Name'), [validators.Length(min=2, max=20)])
    street = TextField(lazy_gettext('Street'), [validators.Length(min=2, max=20)])
    pcode = TextField(lazy_gettext('Postalcode'), [validators.Length(min=2, max=20)])
    city = TextField(lazy_gettext('City'), [validators.Length(min=2, max=20)])
    country = TextField(lazy_gettext('Country'), [validators.Length(min=2, max=20)])
    vatreg = TextField(lazy_gettext('VAT Registration Number'), [validators.Length(min=6, max=20)])
    email = TextField(lazy_gettext('Email Address'), [validators.Length(min=6, max=50)])
    phone = TextField(lazy_gettext('Telephone Number'), [validators.Length(min=6, max=50)])
    contact = TextField(lazy_gettext('Contact person'), [validators.Length(min=2, max=50)])
    
## Route with form from above. 
## Checking if VAT Registration number is already used, if not insert data into DB. 
## Inserting also foreign key SP_Us_id from user login. variable session[ID] saved. 
@app.route('/createmydata/', methods=['GET','POST'])
@login_required
def createmydata():
    global sessioncurr 
    try:
        form = CreatemydataForm(request.form)
        
        if request.method == 'POST' and form.validate():
            name = form.name.data
            street = form.street.data
            pcode = form.pcode.data
            city = form.city.data
            country = form.country.data
            vatreg = form.vatreg.data
            email = form.email.data
            phone = form.phone.data
            contact = form.contact.data
            sessioncurr = session['ID'] 
            #password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute("SELECT * FROM supplier WHERE Sp_vatregno = (%s)",
                          [(thwart(vatreg))])

            if int(x) > 0:
                flash(gettext("This VAT Registration number is already taken, please check for existing account or contact myinvsender@gmail.com"))
                return render_template('createmydata.html', form=form)
            else:           
                c.execute("INSERT INTO supplier (Sp_Us_id, Sp_name, Sp_street, Sp_postcode, Sp_city, Sp_Country, Sp_vatregno, Sp_email, Sp_phone, Sp_contact) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                          (thwart(str(sessioncurr)),thwart(str(name)), thwart(str(street)), thwart(str(pcode)), thwart(str(city)), thwart(str(country)), thwart(str(vatreg)), thwart(str(email)), thwart(str(phone)), thwart(str(contact))))
                        
                conn.commit()

                flash(gettext("You've successfully created your data"))
                c.close()
                conn.close()
                gc.collect()
                c, conn = connection()


                return redirect(url_for('createinvoice'))

        return render_template("createmydata.html", form=form)

    except Exception as e:
        return(str(e))

#### MY DATA #####
    ##MODIFY ##
		
		
#### MY CUSTOMERDATA #####
    ##CREATE##
    ##INVOICERECEIVER##
    
class CreateinvoicerecForm(Form):
    name = TextField(lazy_gettext('Name'), [validators.Length(min=2, max=20)])
    street = TextField(lazy_gettext('Street'), [validators.Length(min=2, max=20)])
    pcode = TextField(lazy_gettext('Postalcode'), [validators.Length(min=2, max=20)])
    city = TextField(lazy_gettext('City'), [validators.Length(min=2, max=20)])
    country = TextField(lazy_gettext('Country'), [validators.Length(min=2, max=20)])
    vatreg = TextField(lazy_gettext('VAT Registration Number'), [validators.Length(min=6, max=20)])
    email = TextField(lazy_gettext('Email Address'), [validators.Length(min=6, max=50)])
    paycon = TextField(lazy_gettext('Payment terms'), [validators.Length(min=6, max=50)])
    pobox = TextField(lazy_gettext('Po box'), [validators.Length(min=0, max=50)])
    

@app.route('/createinvoicerec/', methods=['GET','POST'])
@login_required
def createinvoicerec():
    global sessioncurr
    try:
        form = CreateinvoicerecForm(request.form)
        if request.method == 'POST' and form.validate():
            name = form.name.data
            street = form.street.data
            pcode = form.pcode.data
            city = form.city.data
            country = form.country.data
            vatreg = form.vatreg.data
            email = form.email.data
            paycon = form.paycon.data
            pobox = form.pobox.data
            sessioncurr = session['ID']
            #password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute("SELECT * FROM customer WHERE Cm_vatregno = (%s)",
                          [(thwart(vatreg))])

            if int(x) > 5:
                flash(gettext("This VAT REG No is already assigned to one of your customers"))
                return render_template('createinvoicerec.html', form=form)
            else:
                c.execute("INSERT INTO customer (Cm_Us_id, Cm_name, Cm_street, Cm_postcode, Cm_city, Cm_Country, Cm_vatregno, Cm_email, Cm_paymentcond, Cm_pobox) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                          (thwart(str(sessioncurr)),thwart(name), thwart(street), thwart(pcode), thwart(city), thwart(country), thwart(vatreg), thwart(email), thwart(paycon), thwart(pobox)))
                
                conn.commit()
                flash(gettext("You've successfully created a new customer"))
                c.close()
                conn.close()
                gc.collect()

                

                #session['logged_in'] = True
                #session['username'] = username

                return redirect(url_for('createinvoice'))

        return render_template("createinvoicerec.html", form=form)

    except Exception as e:
        return(str(e))

#### MY CUSTOMERDATA #####
    ##CREATE##
    ##GOODSRECEIVER##
class CreategoodsrecForm(Form):
    name = TextField(lazy_gettext('Name'), [validators.Length(min=2, max=20)])
    street = TextField(lazy_gettext('Street'), [validators.Length(min=2, max=20)])
    pcode = TextField(lazy_gettext('Postalcode'), [validators.Length(min=2, max=20)])
    city = TextField(lazy_gettext('City'), [validators.Length(min=2, max=20)])
    country = TextField(lazy_gettext('Country'), [validators.Length(min=2, max=20)])    

@app.route('/creategoodsrec/', methods=['GET','POST'])
@login_required
def creategoodsrec():
    mySQL2 = SelectCustomer(session['ID']) #displayed invoicereceiver
    global sessioncur
    try:
        form = CreategoodsrecForm(request.form)
        if request.method == 'POST' and form.validate():
            customer = request.form.get('customer')
            name = form.name.data
            street = form.street.data
            pcode = form.pcode.data
            city = form.city.data
            country = form.country.data
            sessioncurr = session['ID']
            
            c, conn = connection()

            customerID = c.execute("SELECT Cm_Id FROM customer WHERE Cm_name ='" + thwart(str(customer)) +"' AND Cm_Us_id =" + thwart(str(session['ID'])) +"  limit 1")
            
                                          
            customerID = c.fetchone()[0]
                        
            
            x = c.execute("SELECT * FROM goodsrec WHERE Gr_name ='" + thwart(str(name)) +"' AND Gr_Cm_id = '" + thwart(str(customerID)) +"'")

            

            if int(x) > 0:
                flash(gettext("This name is already assigned to one of your goods recipients for this customer"))
                return render_template('creategoodsrec.html', form=form,  mySQL2 = mySQL2)
            else:
                
                customerID = c.execute("SELECT Cm_Id FROM customer WHERE Cm_name ='" + thwart(str(customer)) +"' AND Cm_Us_id =" + thwart(str(session['ID'])) +"  limit 1")
                                          
                customerID = c.fetchone()[0]
                
                c.execute("INSERT INTO goodsrec (Gr_Cm_id,Gr_Us_id, Gr_name, Gr_street, Gr_postcode, Gr_city, Gr_Country) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                          (thwart(str(customerID)),thwart(str(sessioncurr)),thwart(name), thwart(street), thwart(pcode), thwart(city), thwart(country)))
                
                conn.commit()
                flash(gettext("You've successfully created a new delivery address"))
                c.close()
                conn.close()
                gc.collect()

                #session['logged_in'] = True
                #session['username'] = session['username']

                return redirect(url_for('createinvoice'))
        flash(gettext("Select respective customer"))
        return render_template("creategoodsrec.html", form=form,  mySQL2 = mySQL2)

    except Exception as e:
        return(str(e))

#### MY CUSTOMERDATA #####
    ##CREATE##
    ##Bankdata##

class CreatebankForm(Form):
    iban = TextField(lazy_gettext('IBAN'), [validators.Length(min=2, max=30)])
    swift = TextField(lazy_gettext('SWIFT or BIC'), [validators.Length(min=2, max=20)])
    name = TextField(lazy_gettext('Bankname'), [validators.Length(min=2, max=20)])
    city = TextField(lazy_gettext('City'), [validators.Length(min=2, max=20)])
    


@app.route('/createbank/', methods=['GET','POST'])
@login_required
def createbank(): 
    global sessioncur
    try:
        form = CreatebankForm(request.form)
        if request.method == 'POST' and form.validate():
            #iban = sha256_crypt.encrypt((str(form.iban.data)))
            iban = form.iban.data
            city = form.city.data
            name = form.name.data
            swift = form.swift.data
            #swift = sha256_crypt.encrypt((str(form.swift.data)))
            
            sessioncurr = session['ID']
            
            c, conn = connection()

            x = c.execute("SELECT * FROM bank WHERE Bk_iban = (%s)",
                          [(thwart(iban))])

            if int(x) > 0:
                flash(gettext("This bank account has already been created, pick another or contact myinvsender@gmail.com"))
                return render_template('createbank.html', form=form)
            else:

                supplierID = c.execute("SELECT Sp_id FROM supplier WHERE Sp_Us_id ='" + str(sessioncurr) +"' limit 1")
                                          
                supplierID = c.fetchone()[0]
                
                c.execute("INSERT INTO bank (Bk_Sp_id,Bk_Us_id, Bk_iban, Bk_name, Bk_city, Bk_swift) VALUES (%s, %s, %s, %s, %s, %s)",
                          (thwart(str(supplierID)),thwart(str(sessioncurr)),thwart(iban), thwart(city), thwart(name), thwart(swift)))
                
                conn.commit()
                flash(gettext("Bank data successfully created"))
                c.close()
                conn.close()
                gc.collect()

                #session['logged_in'] = True
                #session['username'] = session['username']

                return redirect(url_for('createinvoice'))

        return render_template('createbank.html', form=form)

    except Exception as e:
        return(str(e))
    
#### MY CUSTOMERDATA #####
    ##MODIFY##
    #### MY INVOICE #####
    ##CREATE##
    ##INVOICE CREATION##
## AT THE MOMENT ONLY FOR HEADER##
    


class CreateinvoiceForm(Form):
    #Headerdata
    ident = SelectField(lazy_gettext('Debit or Credit note'), choices = [('debit', lazy_gettext('Debit')), ('credit', lazy_gettext('Credit'))])
    invno = TextField(lazy_gettext('Invoice Number'), [validators.Required(message='Field is required, please fill')])
    invdate = DateField(lazy_gettext('Invoice date'), format='%m/%d/%Y')
    currency = SelectField(lazy_gettext('Currency'), choices = [('EUR', 'EUR'), ('CHF', 'CHF'), ('USD', 'USD'), ('SEK', 'SEK'), ('DKK', 'DKK')])
    transport = DecimalField(lazy_gettext('Transport cost'), default=0,  places=2)
    deldate = DateField(lazy_gettext('Delivery date'), format='%m/%d/%Y')
    rebate = DecimalField(lazy_gettext('Discount amount'), default=0,  places=2)
    text = TextField(lazy_gettext('Additional text'), [validators.Length(min=0, max=50)])
    
    #Itemdata
    costobject = TextField(lazy_gettext('Purchaseorder or Costcenter'), [validators.Length(min=0, max=12)])
    descr = TextField(lazy_gettext('Article Description'), [validators.Length(min=0, max=20)])
    quant = IntegerField(lazy_gettext('Quantity'), default=1)
    unit = SelectField(lazy_gettext('Unit of measure'), choices = [('PCS', lazy_gettext('Piece')), ('h', lazy_gettext('Hour'))])
    netamount = DecimalField(lazy_gettext('Net amount'), default=0,  places=2)
    vatrate = DecimalField(lazy_gettext('VAT rate (%)'), default=0,  places=2)
    vatamount = DecimalField(lazy_gettext('VAT amount'), default=0,  places=2)
    grossamount = DecimalField(lazy_gettext('Gross amount'), default=0, places=2)
    

@app.route('/createinvoice/', methods=['GET','POST'])
@login_required
def createinvoice():
    mySQL1 = SelectSupplier(session['ID']) #displayed my data
    mySQL2 = SelectCustomer(session['ID']) #displayed invoicereceiver
    mySQL3 = SelectGoodsrec(session['ID'])
    mySQL4 = SelectBank(session['ID'])
    global sessioncur
    try:
        form = CreateinvoiceForm(request.form)
        if request.method == 'POST' and form.validate(): 
            #HEADER
            #This fetches from HTML
            customer = request.form.get('customer')
            print (customer)
            goodsrec = request.form.get('goodsrec')
            print (goodsrec)
            ident = form.ident.data
            invno = form.invno.data
            #return form.invdate.data.strftime('%Y-%m-%d')
            invdate = form.invdate.data
            currency = form.currency.data
            transport = form.transport.data
            deldate = form.deldate.data
            rebate = form.rebate.data
            text = form.text.data
            #ITEM
            costobject = form.costobject.data
            descr = form.descr.data
            quant = form.quant.data
            unit = form.unit.data
            netamount = form.netamount.data
            vatrate = form.vatrate.data
            vatamount = form.vatamount.data
            grossamount = form.grossamount.data

            sessioncurr = session['ID']
            
            c, conn = connection()

            #Used to make depend not only on all invoice numbers but also CustomerID

            customerID = c.execute("SELECT Cm_Id FROM customer WHERE Cm_name ='" + str(customer) +"' limit 1")
                                          
            customerID = c.fetchone()[0]

            supplierID = c.execute("SELECT Sp_id FROM supplier WHERE Sp_Us_id ='" + str(sessioncurr) +"' limit 1")
                                          
            supplierID = c.fetchone()[0]            
            
            x = c.execute("SELECT * FROM invoice WHERE Iv_invno ='" + thwart(str(invno)) +"' AND Iv_Sp_id = '" + thwart(str(supplierID)) +"'")
            if int(x) > 0:
                
                message = Markup(gettext("This invoice was already submitted!<br><b>Please use a new invoice number</b><br><br><b>Make sure to selcect the delivery address</b>"))
                flash(message)
                
                
                return render_template('createinvoice.html', form=form,  mySQL1 = mySQL1,  mySQL2 = mySQL2,  mySQL3 = mySQL3, TOPIC_DICT = TOPIC_DICT, mySQL4 = mySQL4, customer = customer, goodsrec = goodsrec )
            else:
                #Used for entries in Database as Foreign Keys
                try:
                    customerID = c.execute("SELECT Cm_Id FROM customer WHERE Cm_name ='" + str(customer) +"' limit 1")
                                          
                    customerID = c.fetchone()[0]
                    goodsrecID = c.execute("SELECT Gr_id FROM goodsrec WHERE Gr_name ='" + str(goodsrec) +"' limit 1")
                                          
                    goodsrecID = c.fetchone()[0]
                except:
		    message = Markup(gettext("<b>Make sure to <b>select</b> a customer and delivery address<br>If not created yet, see below<br><strong>&#8595;</strong></b>"))
                    flash(message)
                    return render_template("createinvoice.html", form=form,  mySQL1 = mySQL1,  mySQL2 = mySQL2,  mySQL3 = mySQL3 , TOPIC_DICT = TOPIC_DICT, mySQL4 = mySQL4)
                

                supplierID = c.execute("SELECT Sp_id FROM supplier WHERE Sp_Us_id ='" + str(sessioncurr) +"' limit 1")
                                          
                supplierID = c.fetchone()[0]

                bankID = c.execute("SELECT Bk_id FROM bank WHERE Bk_Sp_id ='" + str(supplierID) +"' limit 1")
                                          
                bankID = c.fetchone()[0]

                goodsrecID = c.execute("SELECT Gr_id FROM goodsrec WHERE Gr_name ='" + str(goodsrec) +"' limit 1")
                                          
                goodsrecID = c.fetchone()[0]

                # Used later for issueinvoice and also as variables when mail is sent

                session['customerEmail'] =  c.execute("SELECT Cm_email FROM customer WHERE Cm_name ='" + str(customer) +"' limit 1")
                
                session['customerEmail'] =  c.fetchone()[0]

                session['invno'] =  form.invno.data
                
                session['supplierEmail'] =  c.execute("SELECT Sp_email FROM supplier WHERE Sp_Us_id ='" + str(sessioncurr) +"' limit 1")
                
                session['supplierEmail'] =  c.fetchone()[0]

                

                # Inserting in DBs                
                c.execute("INSERT INTO invoice (Iv_Sp_id, Iv_Cm_id, Iv_Gr_id, Iv_Bk_id, Iv_ident, Iv_invno, Iv_invdate, Iv_currency, Iv_transport, Iv_deldate, Iv_rebate, Iv_text) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                          (thwart(str(supplierID)),thwart(str(customerID)),thwart(str(goodsrecID)),thwart(str(bankID)),thwart(str(ident)), thwart(str(invno)), thwart(str(invdate)), thwart(str(currency)), thwart(str(transport)), thwart(str(deldate)), thwart(str(rebate)), thwart(str(text))))
                
                conn.commit()

                #Foreign keys for table item which is invoice
                
                
                invoiceID = c.execute("SELECT * FROM invoice WHERE Iv_invno ='" + thwart(str(invno)) +"' AND Iv_Sp_id = '" + thwart(str(supplierID)) +"'")
                                          
                invoiceID = c.fetchone()[0]
                
                session['invId'] = invoiceID

                mySQL3 = SelectGoodsrec(session['ID'])

                c.execute("INSERT INTO item (It_In_id, It_number, It_description, It_quantity, It_unit, It_net, It_vatrate, It_vatamount, It_gross) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                          (thwart(str(invoiceID)), thwart(str(costobject)), thwart(str(descr)), thwart(str(quant)), thwart(str(unit)), thwart(str(netamount)), thwart(str(vatrate)), thwart(str(vatamount)), thwart(str(grossamount))))
                
                conn.commit()
                #Sergio, esto me da un error: 'mySQL3' is undefined
                #InvoiceString, InvoiceXML=XmlGenerator(str(SelectInvoiceId(session['ID'])))")
                message = Markup(gettext('Your <b>e-invoice</b> has been created successfully!<br><br>You can issue it now:<b><br><br><a href="/send-mail" class="alert-link">Issue e-invoice</a><br><br><a href="/Zugsendmail" class="alert-link">Issue as ZUGFeRD</a></b>'))
                flash(message)

                

               



                c.close()
                conn.close()
                gc.collect()

                #session['logged_in'] = True
                #session['username'] = session['username']
                
                
                return redirect(url_for('issueinvoice'))
            
        
        
        if len(mySQL2)< 1:
            message = Markup(gettext("<b>Make sure to <b>create</b> a customer and delivery address<br>If not created yet, see below<br><strong>&#8595;</strong></b>"))
            flash(message)
        else:
            message = Markup(gettext("Complete the form and submit your <b>e-invoice</b>."))
            flash(message)
        return render_template("createinvoice.html", form=form,  mySQL1 = mySQL1,  mySQL2 = mySQL2,  mySQL3 = mySQL3 , TOPIC_DICT = TOPIC_DICT, mySQL4 = mySQL4)

    except Exception as e:
        message = Markup(gettext("Check the form, there are still errors.<br><br><b></b><br><br> <b>Reselect the customer</b>"))
        flash(message)
        
        return render_template('createinvoice.html', form=form,  mySQL1 = mySQL1,  mySQL2 = mySQL2,  mySQL3 = mySQL3, TOPIC_DICT = TOPIC_DICT, mySQL4 = mySQL4, customer = customer, goodsrec = goodsrec )
    
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)




@app.route('/get_goods_receivers/')
@login_required
def get_goods_receivers():
    customer = request.args.get('customer')
    print (customer)
    if customer:
        c, conn = connection()
        customerID = c.execute("SELECT Cm_Id FROM customer WHERE Cm_name ='" + thwart(str(customer)) +"' AND Cm_Us_id =" + thwart(str(session['ID'])) +"  limit 1")
        customerID = c.fetchone()[0]
        print (customerID)
        c.execute("SELECT * FROM goodsrec WHERE Gr_Cm_id = %s", [thwart(str(customerID))])
        mySQL8 = c.fetchall()
        c.close()
        # x[0] here is Gr_id (for application use)
        # x[3] here is the Gr_name field (for user display)
        data = [{"id": x[0], "name": x[3]} for x in mySQL8]
        print (data)
    return jsonify(data)


@app.route('/issueinvoice/', methods=['GET','POST'])
@login_required
def issueinvoice():
    customerEmail = session.get('customerEmail')
    supplierEmail = session.get('supplierEmail')
    mySQL2 = SelectCustomer(session['ID']) #displayed invoicereceiver
    mySQL3 = SelectGoodsrec(session['ID'])
    return render_template("issueinvoice.html", TOPIC_DICT = TOPIC_DICT,  mySQL2 = mySQL2,  mySQL3 = mySQL3, customerEmail = customerEmail, supplierEmail = supplierEmail)

## Tab issue invoice, sends mail
## recipients has to be a variable from DB
## Needs to attach PDF and XML
@app.route('/send-mail/')
@login_required
def send_mail():
        customerEmail = session.get('customerEmail')
        supplierEmail = session.get('supplierEmail')
        invno = session.get('invno')
        username = session['username']
        invId = session['invId']
        xmlStr,xmlFile = XmlGenerator(invId)
        
	try:
		msg = Message("www.myinv.org - "+invno+" e-invoice",
		sender="myinvsender@gmail.com",
		recipients=[customerEmail,supplierEmail])

		msg.body = '\nYou have received an e-invoice via www.myinv.org with reference: '+invno+'\n\nBest Regards\n\nwww.myinv.org'
		
    # Version anterior del prettify
		#soup = bs(xmlStr)
		#xmlStr = soup.prettify()
		myxmlinv = xml.dom.minidom.parseString(xmlStr)
		xmlStr = myxmlinv.toprettyxml(encoding="utf-8")
		msg.attach("Invoice_"+str(invno)+".xml","application/xml",xmlStr)
		    
		buff = BytesIO()
				
		# INV ' + invoice.invno.text + '
		pdfdoc = SimpleDocTemplate(buff, pagesize = letter)
		
		frame = Frame(pdfdoc.leftMargin,
				pdfdoc.bottomMargin,
				pdfdoc.width,
				pdfdoc.height,
				id = 'normal')
		
		template = PageTemplate(id = 'test', frames = frame)
		
		pdfdoc.addPageTemplates(template)
		
		pdforder = PDFOrder(xmlStr)
		Document = pdforder.createPDF()
   
		pdfdoc.build(Document)
   
		pdf = buff.getvalue()
   
		buff.close()
		
		msg.attach("Invoice_"+str(invno)+".pdf", "application/pdf", str(pdf))
		
		#with app.open_resource("/var/www/FlaskApp/FlaskApp/static/resume.pdf") as fp: 
                #     msg.attach("/var/www/FlaskApp/FlaskApp/static/resume.pdf", "resume/pdf", fp.read())
                #with app.open_resource("/var/www/FlaskApp/FlaskApp/static/resume.xml") as fp1:
                #    msg.attach("/var/www/FlaskApp/FlaskApp/static/resume.xml", "resume/xml", fp1.read())
                  
		mail.send(msg)
		message = Markup(gettext("<b>Your e-invoice has been sent by email<br><br>Thanks for using myinv</b>"))
                flash(message)
		
		return redirect(url_for('dashboard'))
	except Exception, e:
		return(str(e))




###Upload logo
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadlogo/', methods=['GET', 'POST'])
@login_required
def upload_file():
    supplierEmail = session.get('supplierEmail')
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash(gettext('No file part'))
            return redirect(url_for('dashboard'))
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash(gettext('No selected file'))
            return redirect(url_for('createinvoice'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = '/var/www/FlaskApp/FlaskApp/logo/'+str(session['username'])+'/'
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs (path)
            file.save(os.path.join('/var/www/FlaskApp/FlaskApp/logo/'+str(session['username'])+'/', filename))
            message = Markup(gettext("Your <b>logo</b> is now added to the invoice<br>"))
            flash(message)
            return redirect(url_for('createinvoice'))
        else:
            message = Markup(gettext("This file extension is not allowed!<br> Make sure you upload: png, jpg, jpeg or gif format"))
            flash(message)
            return redirect(url_for('createinvoice'))
    message = Markup(gettext("Replace the <b>myinv</b> default with your <b>logo</>"))
    flash(message)
    return render_template("uploadlogo.html")
    


   
    
@app.route('/Zugsendmail/')
@login_required
def Zugsendmail():
        customerEmail = session.get('customerEmail')
        supplierEmail = session.get('supplierEmail')
        invno = session.get('invno')
        username = session['username']
        invId = session['invId']
        xmlStr,xmlFile = XmlGenerator(invId)
        ZugxmlStr,ZugxmlFile = ZugXmlGenerator(invId)
        
	try:
		msg = Message("www.myinv.org - "+invno+" ZugFerd",
		sender="myinvsender@gmail.com",
		recipients=[customerEmail,supplierEmail])

		msg.body = '\nYou have received an e-invoice via www.myinv.org with reference: '+invno+'\n\nThe format is ZugFerd\n\nBest Regards\n\nwww.myinv.org'
		

		myxmlinv = xml.dom.minidom.parseString(xmlStr)
		xmlStr = myxmlinv.toprettyxml(encoding="utf-8")

		Zugmyxmlinv = xml.dom.minidom.parseString(ZugxmlStr)
		ZugxmlStr = Zugmyxmlinv.toprettyxml(encoding="utf-8")
		msg.attach("ZugFerd_Inv_"+str(invno)+".xml","application/xml",ZugxmlStr)
		    
		buff = BytesIO()
				
		
		pdfdoc = SimpleDocTemplate(buff, pagesize = letter)
		
		frame = Frame(pdfdoc.leftMargin,
				pdfdoc.bottomMargin,
				pdfdoc.width,
				pdfdoc.height,
				id = 'normal')
		
		template = PageTemplate(id = 'test', frames = frame)
		
		pdfdoc.addPageTemplates(template)
		
		pdforder = PDFOrder(xmlStr)
		Document = pdforder.createPDF()
   
		pdfdoc.build(Document)
   
		pdf = buff.getvalue()
   
		buff.close()
		
		msg.attach("ZugFerd_Inv_"+str(invno)+".pdf", "application/pdf", str(pdf))
		
		
                  
		mail.send(msg)
		message = Markup(gettext("<b>Your e-invoice has been sent by email<br><br>Thanks for using myinv</b>"))
                flash(message)
		
		return redirect(url_for('dashboard'))
	except Exception, e:
		return(str(e))

### Preview the invoice
@app.route('/previewissue/')
@login_required
def previewissue():
    customerEmail = session.get('customerEmail')
    supplierEmail = session.get('supplierEmail')
    invno = session.get('invno')
    invId = session['invId']
    xmlStr,xmlFile = XmlGenerator(invId)
    username = session['username']

    try:
        myxmlinv = xml.dom.minidom.parseString(xmlStr)
        xmlStr = myxmlinv.toprettyxml(encoding="utf-8")
        
	buff = BytesIO()
				
		# INV ' + invoice.invno.text + '
	pdfdoc = SimpleDocTemplate(buff, pagesize = letter)
	
		
	frame = Frame(pdfdoc.leftMargin,
				pdfdoc.bottomMargin,
				pdfdoc.width,
				pdfdoc.height,
				id = 'normal')
		
	template = PageTemplate(id = 'test', frames = frame)
		
	pdfdoc.addPageTemplates(template)
		
	pdforder = PDFOrder(xmlStr)
	Document = pdforder.createPDF()
	pdfdoc.title = 'Preview e-invoice: Invoice_'+str(invId)+'.pdf '
       
	pdfdoc.build(Document)
	
   
	with open("/var/www/FlaskApp/FlaskApp/static/preview/Invoice_"+str(invId)+""+str(customerEmail)+".pdf", "wb") as f:
            f.write(buff.getvalue())
        buff.close()

        return redirect(url_for('static', filename='/preview/Invoice_'+str(invId)+''+str(customerEmail)+'.pdf'))
        
    except Exception, e:
		return(str(e))
            	
#############################################
	    ###########################
	    ##############################

if __name__ == "__main__":
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run()


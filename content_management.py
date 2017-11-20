from dbconnect import connection
import gc

### Retrieval of my data shown in dashboard
def SelectSupplier(id):
    c,conn = connection()
    c.execute("SELECT * FROM supplier WHERE Sp_Us_id =" +str(id))
    mySQL1 = c.fetchone()
    c.close()
    conn.close()
    gc.collect()
    return mySQL1

### Retrieval of customer data shown in dashboard
def SelectCustomer(id):
    c,conn = connection()
    c.execute("SELECT * FROM customer WHERE Cm_Us_id =" +str(id))
    mySQL2 = c.fetchall()
    c.close()
    conn.close()
    gc.collect()
    return mySQL2

### Retrieval of goods receiver data shown in dashboard
def SelectGoodsrec(id):
    c,conn = connection()
    c.execute("SELECT * FROM goodsrec WHERE Gr_Us_id=" +str(id))
    mySQL3 = c.fetchone()
    c.close()
    conn.close()
    gc.collect()
    return mySQL3

### Retrieval of bank data shown in dashboard
def SelectBank(id):
    c,conn = connection()
    c.execute("SELECT * FROM bank WHERE Bk_Us_id=" +str(id))
    mySQL4 = c.fetchone()
    c.close()
    conn.close()
    gc.collect()
    return mySQL4
    
def SelectBankId(id):
    c,conn = connection()
    c.execute("SELECT Bk_id FROM bank WHERE Bk_Us_id=" +str(id) +" order by Bk_id desc limit 1")
    BankId = c.fetchone()[0]
    c.close()
    conn.close()
    gc.collect()
    return BankId

def SelectCustomerId(id):
    c,conn = connection()
    c.execute("SELECT Cm_id FROM customer WHERE Cm_Us_id=" +str(id) +" order by Cm_id desc limit 1")
    CustomerId = c.fetchone()[0]
    c.close()
    conn.close()
    gc.collect()
    return CustomerId

def SelectGoodsrecId(id):
    c,conn = connection()
    c.execute("SELECT Gr_id FROM goodsrec WHERE Gr_Us_id=" +str(id) +" order by Gr_id desc limit 1")
    GoodsrecId = c.fetchone()[0]
    c.close()
    conn.close()
    gc.collect()
    return GoodsrecId
 
def SelectSupplierId(id):
    c,conn = connection()
    c.execute("SELECT Sp_id FROM supplier WHERE Sp_Us_id=" +str(id) +" order by Sp_id desc limit 1")
    SupplierId = c.fetchone()[0]
    c.close()
    conn.close()
    gc.collect()
    return SupplierId
    
def SelectInvoiceId(id):
    c,conn = connection()
    c.execute("SELECT Iv_id FROM invoice WHERE Iv_Sp_id=" +str(SelectSupplierId(id)) +" order by Gr_id desc limit 1")
    InvoiceId = c.fetchone()[0]
    c.close()
    conn.close()
    gc.collect()
    return InvoiceId

### Retrieval of goods receiver data shown in seegodsrec

def SelectGoodsrecSEE(id):
    c,conn = connection()
    c.execute("SELECT * FROM goodsrec WHERE Gr_Cm_id=" +str(id))
    mySQL8 = c.fetchall()
    c.close()
    conn.close()
    gc.collect()
    return mySQL8

#def SelectCustomerSEE(id):
#    c,conn = connection()
#    c.execute("SELECT * FROM customer WHERE Cm_id=" +str(id))
#    mySQL9 = c.fetchone()
#    c.close()
#    conn.close()
#    gc.collect()
#    return mySQL9

#def SelectCustomerID_from_Cm_name(id):
#    c,conn = connection()
#    c.execute("SELECT Cm_Id FROM customer WHERE Cm_name=" +str(id))
#    mySQL10 = c.fetchone()
#    c.close()
#    conn.close()
#    gc.collect()
#    return mySQL10
    
## Used for display in tabs
def Content():
    TOPIC_DICT = {"mydata":[["Create my data","/createmydata/","Modify my data","/modifymydata/"]],
                  "customerdata":[["Create new customer","/createinvoicerec/","Modify invoice receiver","/modifyinvoicerec/"]],
                  "goodsrec":[["Create Delivery Address","/creategoodsrec/","View details","/seegoodsrec/"]],
                  "bank":[["Create my bankaccount","/createbank/","View details","/seebank/"]],
                  "issue invoice":[["Issue as myinv","/send-mail/"]],
                  "create invoice":[["Create your e-invoice","/createinvoice/"],]
                  }
    return TOPIC_DICT

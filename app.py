# ==================imports===================
import sqlite3
import re
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.font import Font
from tkinter import ttk
from time import strftime
from PIL import ImageTk, Image
from win32api import GetMonitorInfo, MonitorFromPoint
import logging
from os import makedirs, getcwd, path
from csv import reader, writer
from datetime import datetime
from custom_generators import StickerGenerator, EscPosCmdGenerator
from subprocess import run
import keyboard
from time import sleep
import hashlib
from json import load, dump
import win32print
from re import match

# ============================================
global root
root = Tk()
style = ttk.Style()
screen_size = (GetMonitorInfo(MonitorFromPoint((0,0))).get("Work")[2], GetMonitorInfo(MonitorFromPoint((0,0))).get("Work")[3])
screen_size = (screen_size[0], screen_size[1])
sub_screen_size = (int(screen_size[0]*0.8), int(screen_size[1]*0.8))
sub_screen_x, sub_screen_y = int((screen_size[0]-sub_screen_size[0])//2), int((screen_size[1]-sub_screen_size[1])//2)

designed_screen_size = (1536, 864)
screen_ratio = (screen_size[0]/designed_screen_size[0], screen_size[1]/designed_screen_size[1])

################ Fonts #################
large_font = Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*20), weight="bold")
medium_font = Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16))
small_font = Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*11))

################ Admin Images #################
admin_login_img = Image.open('./assets/admin_login.png')
login_img = Image.open('./assets/login.png')
admin_img = Image.open('./assets/admin.png')
inventory_icon_img = Image.open('./assets/inventory_icon.png')
emp_icon_img = Image.open('./assets/emp_icon.png')
invoice_icon_img = Image.open('./assets/invoice_icon.png')
settings_icon_img = Image.open('./assets/settings_icon.png')
logout_img = Image.open('./assets/logout.png')
inventory_img = Image.open('./assets/inventory.png')
update_product_img = Image.open('./assets/update_product.png')
add_product_img = Image.open('./assets/add_product.png')
generate_barcode_img = Image.open('./assets/generate_barcode.png')
employee_img = Image.open('./assets/employee.png')
add_employee_img = Image.open('./assets/add_employee.png')
update_employee_img = Image.open('./assets/update_employee.png')
invoice_img = Image.open('./assets/invoice.png')
settings_img = Image.open('./assets/settings.png')

################ Employee Images #################
emp_login_img = Image.open('./assets/employee_login.png')
login_img = Image.open('./assets/login.png')
billing_screen_img = Image.open('./assets/billing_screen.png')
print_img = Image.open('./assets/print.png')
save_img = Image.open('./assets/save.png')

################ Main Images #################
main_img = Image.open('./assets/main.png')
emp_login_icon_img = Image.open('./assets/emp_login_icon.png')
admin_login_icon_img = Image.open('./assets/admin_login_icon.png')

###############################################

config_data = load(open("./config.json", "r"))
barcode_max_len = config_data["billing"]["barcode_max_len"]
barcode_patteren = r'^\d{'+str(barcode_max_len)+r'}$'

with sqlite3.connect("./Database/store.db") as db:
    cur = db.cursor()

makedirs("./logs", exist_ok=True)
logging.basicConfig(filename="./logs/app.log", level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')

format_name = lambda name: name.strip().lower().replace(" and ", " & ").replace("-", " ").replace("_", " ").title().replace(" ", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "")

inventory_columns = ("product_id","product_name","product_hsn","product_brand","product_size","product_color",\
                    "product_stock","product_mrp","product_discounted_price","product_gst","gender","product_cost",\
                    "supplier_phone","supplier_name","supplier_mail")
inv_col_d = {col: i for i, col in enumerate(inventory_columns)}

employee_columns = ('emp_id', 'emp_username', 'emp_name', 'emp_mail', 'emp_phone', 'emp_address', 'emp_designation')
invoice_columns = ('bill_no', 'date', 'e_id', 'c_num', 'c_name', 'total', 'net_total', 'payment_method', 'payment_status')


################### Common Functions ####################
def resize_image(img, size):
    return ImageTk.PhotoImage(img.resize(size, Image.BICUBIC))

def valid_phone(phn):
    if re.match(r"[6789]\d{9}$", phn):
        return True
    return False

def admin_pg_exit():
    sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=adm)
    if sure == True:
        adm.destroy()
        root.deiconify()
        admin_login_pg.adm_username_entry.delete(0, END)
        admin_login_pg.adm_password_entry.delete(0, END)

def adm_sub_pg_exit(window):
    sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=window)
    if sure == True:
        window.destroy()
        adm.destroy()
        root.deiconify()

def biller_pg_exit():
    sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=biller)
    if sure == True:
        biller.destroy()
        root.deiconify()
        emp_login_pg.emp_username_entry.delete(0, END)
        emp_login_pg.emp_password_entry.delete(0, END)

def validate_int(val):
    if val.isdigit():
        return True
    elif val == "":
        return True
    return False

def validate_float(val):
    if val.isdigit():
        return True
    elif val == "":
        return True
    elif val.count('.') == 1 and val.replace('.', '').isdigit():
        return True
    return False

############ Admin Functions ################

def get_available_product_id():
    results = cur.execute("SELECT MAX(CAST(product_id AS INTEGER)) FROM inventory").fetchall()
    if len(results) == 0 or results[0][0] == None:
        return 1
    return int(results[0][0]) + 1

def get_available_emp_id():
    results = cur.execute("SELECT MAX(CAST(emp_id AS INTEGER)) FROM employee").fetchall()
    if len(results) == 0 or results[0][0] == None:
        return 1
    return int(results[0][0]) + 1

def launch_inventory(window_to_withdraw=None):
    if window_to_withdraw:
        window_to_withdraw.withdraw()
    global inv
    global inv_pg
    inv = Toplevel()
    inv_pg = Inventory(inv)
    inv_pg.time()
    inv.protocol("WM_DELETE_WINDOW", lambda inv=inv: adm_sub_pg_exit(inv))
    inv.mainloop()

def launch_employee(window_to_withdraw=None):
    if window_to_withdraw:
        window_to_withdraw.withdraw()
    global emp
    global emp_mngmnt_pg
    emp = Toplevel()
    emp_mngmnt_pg = Employee(emp)
    emp_mngmnt_pg.time()
    emp.protocol("WM_DELETE_WINDOW", lambda emp=emp: adm_sub_pg_exit(emp))
    emp.mainloop()

def launch_invoices(window_to_withdraw=None):
    global invc
    if window_to_withdraw:
        window_to_withdraw.withdraw()
    adm.withdraw()
    global invc
    invc = Toplevel()
    invoice_mngmnt_pg = Invoice(invc)
    invoice_mngmnt_pg.time()
    invc.protocol("WM_DELETE_WINDOW", lambda invc=invc: adm_sub_pg_exit(invc))
    invc.mainloop()

def launch_settings(window_to_withdraw=None):
    if window_to_withdraw:
        window_to_withdraw.withdraw()
    global setting
    global settings_pg
    setting = Toplevel()
    settings_pg = ConfigSettings(setting)
    setting.protocol("WM_DELETE_WINDOW", lambda setting=setting: adm_sub_pg_exit(setting))
    setting.mainloop()

############ Employee Functions ################
def get_bill_number():

    pre_bill_num = cur.execute("SELECT bill_no FROM bill ORDER BY bill_no DESC LIMIT 1").fetchone()
    if pre_bill_num:
        pre_bill_num = 'RBF' + str(int(pre_bill_num[0][3:])+1).zfill(7)
    else:
        pre_bill_num = 'RBF0000001'
    return pre_bill_num

############################################################################
######################### ADMIN CLASSES ####################################
############################################################################
class AdminLoginPage:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Admin Login")

        self.label1 = Label(admin_lgn)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(admin_login_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.adm_username_entry = Entry(admin_lgn)
        self.adm_username_entry.place(relx=0.378, rely=0.4625, width=screen_ratio[0]*370, height=screen_ratio[1]*45)
        self.adm_username_entry.configure(font=medium_font, relief="flat")
        self.adm_username_entry.bind("<Return>", lambda event: self.adm_password_entry.focus())
        self.adm_username_entry.bind("<Down>", lambda event: self.adm_password_entry.focus())

        self.adm_password_entry = Entry(admin_lgn)
        self.adm_password_entry.place(relx=0.378, rely=0.6275, width=screen_ratio[0]*370, height=screen_ratio[1]*45)
        self.adm_password_entry.configure(font=medium_font, relief="flat", show="*")
        self.adm_password_entry.bind("<Return>", self.login)
        self.adm_password_entry.bind("<Up>", lambda event: self.adm_username_entry.focus())

        self.login_btn = Button(admin_lgn)
        self.login_btn.place(relx=0.441, rely=0.7415, width=180, height=50)
        img = resize_image(login_img, (int(screen_ratio[0]*180), int(screen_ratio[1]*50)))
        self.login_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.login, background="#ffffff")
        self.login_btn.img = img


    def login(self, Event=None):

        username = self.adm_username_entry.get()
        password = self.adm_password_entry.get()
        password = hashlib.sha256(password.encode()).hexdigest()

        with sqlite3.connect("./Database/store.db") as db:
            cur = db.cursor()
        find_user = "SELECT * FROM employee WHERE emp_username = ? AND emp_password = ?"
        cur.execute(find_user, [(username), (password)])
        results = cur.fetchall()
        if results:
            if results[0][7].lower() == "admin":
                admin_login_pg.adm_username_entry.delete(0, END)
                admin_login_pg.adm_password_entry.delete(0, END)

                admin_lgn.withdraw()
                global adm
                global adm_pg
                adm = Toplevel()
                adm_pg = AdminPage(adm)
                adm.protocol("WM_DELETE_WINDOW", admin_pg_exit)
                adm.mainloop()
            else:
                messagebox.showerror("Oops!!", "You are not an admin.", parent=admin_lgn)

        else:
            messagebox.showerror("Error", "Incorrect username or password.", parent=admin_lgn)
            admin_login_pg.adm_password_entry.delete(0, END)

class AdminPage:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("ADMIN Mode")


        self.label1 = Label(adm)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(admin_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.logout_btn = Button(adm)
        self.logout_btn.place(relx=0.9, rely=0.065, width=screen_ratio[0]*102, height=screen_ratio[1]*50)
        img = resize_image(logout_img, (int(screen_ratio[0]*102), int(screen_ratio[1]*50)))
        self.logout_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.Logout, background="#ffffff")
        self.logout_btn.img = img

        self.inventory_btn = Button(adm)
        self.inventory_btn.place(relx=0.425, rely=0.2, width=screen_ratio[0]*200, height=screen_ratio[1]*200)
        img = resize_image(inventory_icon_img, (int(screen_ratio[0]*200), int(screen_ratio[1]*200)))
        self.inventory_btn.configure(image=img, borderwidth="0", cursor="hand2", command=lambda: launch_inventory(adm),background="#ffffff")
        self.inventory_btn.img = img

        self.employee_btn = Button(adm)
        self.employee_btn.place(relx=0.725, rely=0.2, width=screen_ratio[0]*200, height=screen_ratio[1]*200)
        img = resize_image(emp_icon_img, (int(screen_ratio[0]*200), int(screen_ratio[1]*200)))
        self.employee_btn.configure(image=img, borderwidth="0", cursor="hand2", command=lambda: launch_employee(adm), background="#ffffff")
        self.employee_btn.img = img

        self.invoice_btn = Button(adm)
        self.invoice_btn.place(relx=0.425, rely=0.55, width=screen_ratio[0]*200, height=screen_ratio[1]*200)
        img = resize_image(invoice_icon_img, (int(screen_ratio[0]*200), int(screen_ratio[1]*200)))
        self.invoice_btn.configure(image=img, borderwidth="0", cursor="hand2", command=lambda: launch_invoices(adm), background="#ffffff")
        self.invoice_btn.img = img

        self.settings_btn = Button(adm)
        self.settings_btn.place(relx=0.725, rely=0.55, width=screen_ratio[0]*200, height=screen_ratio[1]*200)
        img = resize_image(settings_icon_img, (int(screen_ratio[0]*200), int(screen_ratio[1]*200)))
        self.settings_btn.configure(image=img, borderwidth="0", cursor="hand2", command=lambda: launch_settings(adm), background="#ffffff")
        self.settings_btn.img = img

        
    def Logout(self):
        sure = messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=adm)
        if sure == True:
            adm.destroy()
            admin_lgn.deiconify()
            admin_login_pg.adm_username_entry.delete(0, END)
            admin_login_pg.adm_password_entry.delete(0, END)

class Inventory:
    def __init__(self, top=None):
        # top.geometry("1366x768")
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Inventory Management")

        self.label1 = Label(inv)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(inventory_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.clock = Label(inv)
        self.clock.place(relx=0.1695, rely=0.1575, width=screen_ratio[0]*105, height=screen_ratio[1]*40)
        self.clock.configure(
            font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*14)),
            foreground="#000000",
            background="#FFFFFF"
        )

        self.logout_btn = Button(inv)
        self.logout_btn.place(relx=0.895, rely=0.08, width=screen_ratio[0]*102, height=screen_ratio[1]*50)
        img = resize_image(logout_img, (int(screen_ratio[0]*102), int(screen_ratio[1]*50)))
        self.logout_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.Logout, background="#ffffff")
        self.logout_btn.img = img
        
        self.product_key_entry = Entry(inv)
        self.product_key_entry.place(relx=0.043, rely=0.337, width=screen_ratio[0]*300, height=screen_ratio[1]*40)
        self.product_key_entry.configure(font=medium_font, relief="flat")
        self.product_key_entry.bind("<Return>", lambda event: self.search_products())

        self.product_search_btn = Button(inv)
        self.product_search_btn.place(relx=0.1, rely=0.407, width=screen_ratio[0]*126, height=screen_ratio[1]*35)
        self.product_search_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Search", activebackground="#FFE59C", 
                                          font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"), 
                                          command=self.search_products)
        self.add_product_btn = Button(inv)
        self.add_product_btn.place(relx=0.06, rely=0.553, width=screen_ratio[0]*250, height=screen_ratio[1]*45)
        self.add_product_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Add Product(s)", activebackground="#FFE59C",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.add_product)
        
        self.generate_barcode_btn = Button(inv)
        self.generate_barcode_btn.place(relx=0.06, rely=0.658, width=screen_ratio[0]*250, height=screen_ratio[1]*45)
        self.generate_barcode_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Generate Barcode", activebackground="#FFE59C",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.generate_barcode)
        self.exit_btn = Button(inv)
        self.exit_btn.place(relx=0.086, rely=0.862, width=screen_ratio[0]*170, height=screen_ratio[1]*45)
        self.exit_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Exit", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.Exit)

        style.theme_use("clam")
        style.configure("tree.Treeview", highlightthickness=0, bd=0, font=small_font) # Modify the font of the body
        style.configure("tree.Treeview.Heading", font=("Segoe UI Semibold", int(0.5*(screen_ratio[0]+screen_ratio[1])*14)), background='#FFDF7F', foreground='black', borderwidth=0) # Modify the font of the headings
        style.layout("tree.Treeview", [('tree.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders
        style.configure("tree.Treeview", rowheight=int(screen_ratio[0]*30))
        self.tree = ttk.Treeview(inv, style="tree.Treeview")
        self.scrollbarx = Scrollbar(inv, orient=HORIZONTAL)
        self.scrollbary = Scrollbar(inv, orient=VERTICAL)
        self.scrollbarx.configure(command=self.tree.xview)
        self.scrollbary.configure(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbary.set, xscrollcommand=self.scrollbarx.set)

        self.tree.place(relx=0.28, rely=0.164, width=screen_ratio[0]*990, height=screen_ratio[1]*610)
        self.scrollbary.place(relx=0.954, rely=0.203, width=screen_ratio[0]*22, height=screen_ratio[1]*548)
        self.scrollbarx.place(relx=0.28, rely=0.9, width=screen_ratio[0]*990, height=screen_ratio[1]*22)

        self.tree.configure(columns=inventory_columns)

        self.tree_d = {col: i for i, col in enumerate(self.tree["columns"])}
        self.tree.heading("product_id", text="ID", anchor=W)
        self.tree.heading("product_name", text="Product Name", anchor=W)
        self.tree.heading("product_hsn", text="HSN", anchor=W)
        self.tree.heading("product_brand", text="Brand", anchor=W)
        self.tree.heading("product_size", text="Size", anchor=W)
        self.tree.heading("product_color", text="Color", anchor=W)
        self.tree.heading("product_stock", text="Stock", anchor=W)
        self.tree.heading("product_mrp", text="MRP", anchor=W)
        self.tree.heading("product_discounted_price", text="Our Price", anchor=W)
        self.tree.heading("product_gst", text="GST%", anchor=W)
        self.tree.heading("gender", text="Gender", anchor=W)
        self.tree.heading("product_cost", text="Cost Price", anchor=W)
        self.tree.heading("supplier_phone", text="Supl Phn", anchor=W)
        self.tree.heading("supplier_name", text="Supl Name", anchor=W)
        self.tree.heading("supplier_mail", text="Supl Mail", anchor=W)

        self.tree['show'] = 'headings'
        self.tree.column("product_id", width=int(screen_ratio[0]*60), anchor=W)
        self.tree.column("product_name", width=int(screen_ratio[0]*180), anchor=W)
        self.tree.column("product_hsn", width=int(screen_ratio[0]*100), anchor=W)
        self.tree.column("product_brand", width=int(screen_ratio[0]*140), anchor=W)
        self.tree.column("product_size", width=int(screen_ratio[0]*60), anchor=W)
        self.tree.column("product_color", width=int(screen_ratio[0]*120), anchor=W)
        self.tree.column("product_stock", width=int(screen_ratio[0]*60), anchor=W)
        self.tree.column("product_mrp", width=int(screen_ratio[0]*100), anchor=W)
        self.tree.column("product_discounted_price", width=int(screen_ratio[0]*100), anchor=W)
        self.tree.column("product_gst", width=int(screen_ratio[0]*80), anchor=W)
        self.tree.column("gender", width=int(screen_ratio[0]*100), anchor=W)
        self.tree.column("product_cost", width=int(screen_ratio[0]*100), anchor=W)
        self.tree.column("supplier_phone", width=int(screen_ratio[0]*140), anchor=W)
        self.tree.column("supplier_name", width=int(screen_ratio[0]*180), anchor=W)
        self.tree.column("supplier_mail", width=int(screen_ratio[0]*200), anchor=W)

        self.tree.bind("<Delete>", lambda event: self.delete_product())
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-Button-1>", self.update_product)

        self.DisplayData()

        # check if the stock is 0 or less than 0 and show warmimg and delete the product from the database
        cur.execute("SELECT product_id, product_stock FROM inventory WHERE product_stock <= 0")
        results = cur.fetchall()
        if len(results) > 0:
            sure = messagebox.askyesno("Warning", "Some products are out of stock. Do you want to delete them?", parent=inv)
            if sure:
                for result in results:
                    cur.execute("DELETE FROM inventory WHERE product_id=?", (result[0],))
                db.commit()
                messagebox.showinfo("Success!!", "Products deleted successfully.", parent=inv)
                self.DisplayData()


    def DisplayData(self):
        self.tree.delete(*self.tree.get_children())
        cur.execute("SELECT * FROM inventory")
        fetch = cur.fetchall()
        for data in fetch:
            self.tree.insert("", "end", values=(data))
            # change datatype of product_id to string
            self.tree.set(self.tree.get_children()[-1], self.tree_d["product_id"], str(data[self.tree_d["product_id"]]))

    def search_products(self):

        if self.product_key_entry.get() == "":
            self.DisplayData()
            return
        
        # self.tree.delete(*self.tree.get_children())
        cur.execute(f"SELECT * FROM inventory WHERE product_id LIKE '%{self.product_key_entry.get()}%' OR product_name LIKE '%{self.product_key_entry.get()}%' \
                    OR product_brand LIKE '%{self.product_key_entry.get()}%' OR product_size LIKE '%{self.product_key_entry.get()}%'")
        results = cur.fetchall()
        if len(results) > 0:
            self.tree.delete(*self.tree.get_children())
            for data in results:
                self.tree.insert("", "end", values=(data))
        else:
            messagebox.showinfo("Error!!", "No such product matches in Product ID/Product Name.", parent=inv)

    def delete_product(self):
        
        ids = self.tree.selection()
        if len(ids) == 0:
            return
        sure = messagebox.askyesno("Delete", "Are you sure you want to delete these product(s)?", parent=inv)
        if sure == True:
            for i in ids:
                cur.execute("DELETE FROM inventory WHERE product_id=?", (self.tree.item(i)["values"][self.tree_d["product_id"]],))
                self.tree.delete(i)   
            db.commit()
            messagebox.showinfo("Success!!", "Product(s) deleted successfully.", parent=inv)

    def update_product(self, event=None):

        if len(self.tree.selection()) == 1:
            # check if double tap is happening on header
            if self.tree.identify_region(event.x, event.y) == "heading":
                return
            global p_update
            p_update = Toplevel()
            update_product_pg = UpdateProductDetails(p_update)
            update_product_pg.product_hsn_entry.focus()
            update_product_pg.event = event
            p_update.bind("<Return>", lambda event: update_product_pg.update_product_details())
            p_update.protocol("WM_DELETE_WINDOW", lambda: self.exit_custom(p_update))
            
            update_product_pg.product_id_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_id"]])
            update_product_pg.product_id_entry.configure(state="disabled")
            update_product_pg.product_name_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_name"]])
            update_product_pg.product_hsn_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_hsn"]])
            update_product_pg.product_brand_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_brand"]])
            update_product_pg.product_size_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_size"]])
            update_product_pg.product_color_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_color"]])
            update_product_pg.product_stock_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_stock"]])
            update_product_pg.product_mrp_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_mrp"]])
            update_product_pg.product_gst_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_gst"]])
            update_product_pg.gender_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["gender"]])
            update_product_pg.product_discounted_price.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_discounted_price"]])
            update_product_pg.product_cost_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["product_cost"]])
            update_product_pg.supplier_phone_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["supplier_phone"]])
            update_product_pg.supplier_name_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["supplier_name"]])
            update_product_pg.supplier_mail_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["supplier_mail"]])

            # entries unique to given barcode
            for entry in [update_product_pg.product_id_entry, update_product_pg.product_name_entry, update_product_pg.product_brand_entry, update_product_pg.product_size_entry, update_product_pg.product_color_entry]:
                entry.configure(font=medium_font, relief="flat", state="disabled")
            p_update.mainloop()

        elif len(self.tree.selection()) == 0:
            messagebox.showerror("Error","Please choose a product to update.", parent=inv)
        else:
            messagebox.showerror("Error","Can only update one product at a time.", parent=inv)

    def show_context_menu(self, event):
        self.sel = self.tree.selection()
        if len(self.sel) == 0:
            return
        if self.tree.identify_region(event.x, event.y) == "heading":
            return
        menu = Menu(inv, tearoff=0)
        menu.add_command(label="Update", command=lambda event=event: self.update_product(event=event))
        menu.add_command(label="Delete", command=self.delete_product)
        menu.post(event.x_root, event.y_root)

    def add_product(self):
        global p_add
        global add_product_pg
        p_add = Toplevel()
        add_product_pg = AddProductDetails(p_add)
        p_add.protocol("WM_DELETE_WINDOW", lambda: self.exit_custom(p_add))
        add_product_pg.product_name_entry.focus()
        p_add.mainloop()

    def generate_barcode(self):

        if len(self.tree.selection()) == 0:
            messagebox.showerror("Error", "Please select a product to generate barcode.", parent=inv)
            return
        
        products = []
        for i in self.tree.selection():
            products.append({"product_id": self.tree.item(i)["values"][self.tree_d["product_id"]], \
                            "product_name": self.tree.item(i)["values"][self.tree_d["product_name"]], \
                            "product_color": self.tree.item(i)["values"][self.tree_d["product_color"]], \
                            "product_size": self.tree.item(i)["values"][self.tree_d["product_size"]], \
                            "product_mrp": self.tree.item(i)["values"][self.tree_d["product_mrp"]], \
                            "product_discounted_price": self.tree.item(i)["values"][self.tree_d["product_discounted_price"]]})

        svg_file_path = getcwd() + r'\sticker_canvas.svg'
        sticker_generator = StickerGenerator(products, svg_file_path)
        try:
            sticker_generator.generate_stickers()
        except Exception as e:
            messagebox.showerror("Error", e, parent=inv)
            return
        
        # open msedge.exe with generated barcode
        ms_edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        run([ms_edge_path, svg_file_path], shell=True)
        sleep(1)

        # trigger print
        keyboard.press_and_release('ctrl+p')

    def time(self):
        string = strftime("%I:%M:%S %p")
        self.clock.config(text=string)
        self.clock.after(1000, self.time)


    def Exit(self):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=inv)
        if sure == True:
            inv.destroy()
            adm.deiconify()


    def exit_custom(self, parent):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=parent)
        if sure == True:
            parent.destroy()
            inv.deiconify()
            self.DisplayData()


    def Logout(self):
        sure = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if sure == True:
            inv.destroy()
            admin_lgn.deiconify()
            admin_login_pg.adm_username_entry.delete(0, END)
            admin_login_pg.adm_password_entry.delete(0, END)

class AddProductDetails:
    def __init__(self, top=None):
        top.geometry(f"{sub_screen_size[0]}x{sub_screen_size[1]}+{sub_screen_x}+{sub_screen_y}")
        top.resizable(0, 0)
        top.title("Add Product")

        self.label1 = Label(p_add)
        self.label1.place(relx=0.0, rely=0.0, width= sub_screen_size[0], height=sub_screen_size[1])
        img = resize_image(add_product_img, sub_screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.int_validator, self.float_validator = p_add.register(validate_int), p_add.register(validate_float)

        self.product_id_entry = Entry(p_add)
        self.product_id_entry.place(relx=0.3375, rely=0.155, width=screen_ratio[0]*400, height=screen_ratio[1]*40)
        self.product_id_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*18)), relief="flat")
        self.product_id_entry.insert(0, get_available_product_id())
        self.product_id_entry.configure(state="disabled")

        self.product_name_entry = Entry(p_add)
        self.product_name_entry.place(relx=0.075, rely=0.319, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_name_entry.configure(font=medium_font, relief="flat")
        self.product_name_entry.bind("<Return>", lambda event: self.product_hsn_entry.focus())
        self.product_name_entry.bind("<Down>", lambda event: self.product_hsn_entry.focus())
        self.product_name_entry.bind("<Up>", lambda event: self.product_id_entry.focus())

        self.product_hsn_entry = Entry(p_add)
        self.product_hsn_entry.place(relx=0.075, rely=0.449, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_hsn_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.product_hsn_entry.insert(0, "610510")
        self.product_hsn_entry.bind("<Return>", lambda event: self.product_brand_entry.focus())
        self.product_hsn_entry.bind("<Down>", lambda event: self.product_brand_entry.focus())

        self.product_brand_entry = Entry(p_add)
        self.product_brand_entry.place(relx=0.075, rely=0.579, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_brand_entry.configure(font=medium_font, relief="flat")
        self.product_brand_entry.bind("<Return>", lambda event: self.product_mrp_entry.focus())
        self.product_brand_entry.bind("<Down>", lambda event: self.product_mrp_entry.focus())
        self.product_brand_entry.bind("<Up>", lambda event: self.product_hsn_entry.focus())

        self.product_mrp_entry = Entry(p_add)
        self.product_mrp_entry.place(relx=0.075, rely=0.711, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_mrp_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_mrp_entry.bind("<Return>", lambda event: self.product_gst_entry.focus())
        self.product_mrp_entry.bind("<Down>", lambda event: self.product_gst_entry.focus())
        self.product_mrp_entry.bind("<Up>", lambda event: self.product_brand_entry.focus())

        self.product_gst_entry = Entry(p_add)
        self.product_gst_entry.place(relx=0.075, rely=0.8425, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_gst_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_gst_entry.bind("<Return>", lambda event: self.product_stock_entry.focus())
        self.product_gst_entry.bind("<Down>", lambda event: self.product_stock_entry.focus())
        self.product_gst_entry.bind("<Up>", lambda event: self.product_mrp_entry.focus())

        self.product_stock_entry = Entry(p_add)
        self.product_stock_entry.place(relx=0.375, rely=0.319, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_stock_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.product_stock_entry.insert(0, "1")
        self.product_stock_entry.bind("<Return>", lambda event: self.product_size_entry.focus())
        self.product_stock_entry.bind("<Down>", lambda event: self.product_size_entry.focus())
        self.product_stock_entry.bind("<Up>", lambda event: self.product_gst_entry.focus())

        self.product_size_entry = Entry(p_add)
        self.product_size_entry.place(relx=0.375, rely=0.449, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_size_entry.configure(font=medium_font, relief="flat")
        self.product_size_entry.bind("<Return>", lambda event: self.product_color_entry.focus())
        self.product_size_entry.bind("<Down>", lambda event: self.product_color_entry.focus())
        self.product_size_entry.bind("<Up>", lambda event: self.product_stock_entry.focus())

        self.product_color_entry = Entry(p_add)
        self.product_color_entry.place(relx=0.375, rely=0.579, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_color_entry.configure(font=medium_font, relief="flat")
        self.product_color_entry.bind("<Return>", lambda event: self.product_discounted_price.focus())
        self.product_color_entry.bind("<Down>", lambda event: self.product_discounted_price.focus())
        self.product_color_entry.bind("<Up>", lambda event: self.product_size_entry.focus())

        self.product_discounted_price = Entry(p_add)
        self.product_discounted_price.place(relx=0.375, rely=0.711, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_discounted_price.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_discounted_price.bind("<Return>", lambda event: self.product_cost_entry.focus())
        self.product_discounted_price.bind("<Down>", lambda event: self.product_cost_entry.focus())
        self.product_discounted_price.bind("<Up>", lambda event: self.product_color_entry.focus())

        self.product_cost_entry = Entry(p_add)
        self.product_cost_entry.place(relx=0.375, rely=0.8425, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_cost_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_cost_entry.bind("<Return>", lambda event: self.gender_entry.focus())
        self.product_cost_entry.bind("<Down>", lambda event: self.gender_entry.focus())
        self.product_cost_entry.bind("<Up>", lambda event: self.product_discounted_price.focus())

        self.gender_entry = Entry(p_add)
        self.gender_entry.place(relx=0.648, rely=0.319, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.gender_entry.configure(font=medium_font, relief="flat")
        self.gender_entry.bind("<Return>", lambda event: self.supplier_phone_entry.focus())
        self.gender_entry.bind("<Down>", lambda event: self.supplier_phone_entry.focus())
        self.gender_entry.bind("<Up>", lambda event: self.product_cost_entry.focus())

        self.supplier_phone_entry = Entry(p_add)
        self.supplier_phone_entry.place(relx=0.648, rely=0.449, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_phone_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.supplier_phone_entry.bind("<Return>", lambda event: self.supplier_name_entry.focus())
        self.supplier_phone_entry.bind("<Down>", lambda event: self.supplier_name_entry.focus())
        self.supplier_phone_entry.bind("<Up>", lambda event: self.gender_entry.focus())

        self.supplier_name_entry = Entry(p_add)
        self.supplier_name_entry.place(relx=0.648, rely=0.579, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_name_entry.configure(font=medium_font, relief="flat")
        self.supplier_name_entry.bind("<Return>", lambda event: self.supplier_mail_entry.focus())
        self.supplier_name_entry.bind("<Down>", lambda event: self.supplier_mail_entry.focus())
        self.supplier_name_entry.bind("<Up>", lambda event: self.supplier_phone_entry.focus())

        self.supplier_mail_entry = Entry(p_add)
        self.supplier_mail_entry.place(relx=0.648, rely=0.709, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_mail_entry.configure(font=medium_font, relief="flat")
        self.supplier_mail_entry.bind("<Up>", lambda event: self.supplier_name_entry.focus())

        self.import_data_btn = Button(p_add)
        self.import_data_btn.place(relx=0.08, rely=0.157, width=screen_ratio[0]*180, height=screen_ratio[1]*35)
        self.import_data_btn.configure(background="#C1ECA4", borderwidth="0", cursor="hand2", text="Import CSV", activebackground="#C1ECA4",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.import_data)

        self.clear_btn = Button(p_add)
        self.clear_btn.place(relx=0.655, rely=0.8283, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.clear_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="CLEAR", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.clearr)
        
        self.add_btn = Button(p_add)
        self.add_btn.place(relx=0.813, rely=0.8283, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.add_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="ADD", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.add_product_details)
        
        for widget in p_add.winfo_children():
            
            if isinstance(widget, Entry):
                widget.bind("<FocusIn>", lambda event, widget=widget: widget.select_range(0, END))
                
    def import_data(self):

        file_path = askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path == "":
            return
        
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            data = reader(f, delimiter=",") if file_path.endswith(".csv") else reader(f)
            if not (0 < len(list(data)) <= 2000):
                messagebox.showerror("Error!!", "Please add upto 2000 products at a time.", parent=p_add)
                return
        
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            data = reader(f, delimiter=",") if file_path.endswith(".csv") else reader(f)
            headers = next(data)
            headers = headers[:(len(inventory_columns)-1)]
            headers = [h.strip() for h in headers]

            if headers != list(inventory_columns[1:]):
                messagebox.showerror("Error!!", "Colmuns names not matching with database.\n\nPlease follow this order & format:\n" + ', '.join(inventory_columns[1:]), parent=p_add)
                return
            failed_csv_path = '/'.join(file_path.split('/')[:-1]) + f"/failed_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.csv"
    
            succefully_added, failed_to_add = 0, 0
            for row in data:
                if all([cell == '' for cell in row]):
                    continue
                row = row[:(len(inventory_columns)-1)]                  # product id is auto generated
                p_id = get_available_product_id()
                p_name, p_brand, p_size, p_color = format_name(row[inv_col_d["product_name"]-1]), format_name(row[inv_col_d["product_brand"]-1]), \
                                                    format_name(row[inv_col_d["product_size"]-1]), format_name(row[inv_col_d["product_color"]-1])   
                try:
                    p_hsn = int(row[inv_col_d["product_hsn"]-1]) if row[inv_col_d["product_hsn"]-1] != '' else 610510
                except:
                    p_hsn = 610510
                
                p_mrp, p_gst = row[inv_col_d["product_mrp"]-1], row[inv_col_d["product_gst"]-1]
                required_fields = [p_id, p_name, p_brand, p_mrp, p_gst, p_size, p_color]
                if any([field == '' for field in required_fields]):
                    with open(failed_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                        csv_writer = writer(f)
                        csv_writer.writerow(row)
                    failed_to_add += 1
                    continue
                try:
                    p_mrp, p_gst = float(p_mrp), float(p_gst)
                except:
                    with open(failed_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                        csv_writer = writer(f)
                        csv_writer.writerow(row)
                    failed_to_add += 1
                    continue

                p_stock = int(row[inv_col_d["product_stock"]-1]) if row[inv_col_d["product_stock"]-1] != '' else 1

                gender = "Unisex" if row[inv_col_d['gender']-1] == '' else format_name(row[inv_col_d['gender']-1])
                p_cost =  float(row[inv_col_d["product_cost"]-1]) if row[inv_col_d["product_cost"]-1] != '' else ''

                try:
                    p_discounted_price = p_mrp if row[inv_col_d["product_discounted_price"]-1] == '' else float(row[inv_col_d["product_discounted_price"]-1])
                except:
                    p_discounted_price = p_mrp

                try:
                    s_phone = int(row[inv_col_d["supplier_phone"]-1])
                except:
                    s_phone = ''
                s_name, s_mail = format_name(row[inv_col_d["supplier_name"]-1]),row[inv_col_d["supplier_mail"]-1].strip()

                try:
                    cur.execute(f"INSERT INTO inventory (product_id, product_name, product_hsn, product_brand, product_size, product_color, product_stock, \
                                product_mrp, product_gst, gender, product_cost, product_discounted_price,supplier_phone, supplier_name, supplier_mail) \
                                VALUES ('{p_id}', '{p_name}', '{p_hsn}', '{p_brand}', '{p_size}', '{p_color}', '{p_stock}', '{p_mrp}', '{p_gst}', '{gender}', \
                                '{p_cost}', '{p_discounted_price}', '{s_phone}', '{s_name}', '{s_mail}')")
                    
                    succefully_added += 1

                except Exception as e:

                    with open(failed_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                        csv_writer = writer(f)
                        csv_writer.writerow(row)
                    failed_to_add += 1

        db.commit()
        messagebox.showinfo("Info", f"Successfully added items:\t{succefully_added}\nFailed to add items:\t{failed_to_add}\nFailed data (if any) is saved at: {failed_csv_path}", parent=p_add)

    def add_product_details(self, event=None):

        p_id, p_name, p_hsn, p_brand = self.product_id_entry.get().strip().upper(), format_name(self.product_name_entry.get()), self.product_hsn_entry.get(), format_name(self.product_brand_entry.get())
        p_mrp, p_stock, p_gst, p_size = self.product_mrp_entry.get(), self.product_stock_entry.get(),self.product_gst_entry.get(), format_name(self.product_size_entry.get())
        p_color, gender, p_cost, p_discounted_price = format_name(self.product_color_entry.get()), format_name(self.gender_entry.get()), self.product_cost_entry.get(), self.product_discounted_price.get()
        s_phone, s_name, s_mail = self.supplier_phone_entry.get(), format_name(self.supplier_name_entry.get()), self.supplier_mail_entry.get().strip()

        required_fields = [p_id, p_name, p_hsn, p_brand, p_mrp, p_gst, p_size, p_color]
        if any([field == '' for field in required_fields]):
            messagebox.showerror("Error!!", "Please fill all the required fields.", parent=p_add)
            return
        
        p_mrp, p_stock, p_gst = float(p_mrp), int(p_stock), float(p_gst)
        gender = "Unisex" if gender == '' else gender
        p_cost = p_mrp if p_cost == '' else float(p_cost)
        p_discounted_price = p_mrp if p_discounted_price == '' else float(p_discounted_price)

        if p_discounted_price > p_mrp:
            self.product_discounted_price.focus_set()
            messagebox.showerror("Error!!", "Discount cannot be more than MRP.", parent=p_add)
            return

        if p_gst > 100:
            self.product_gst_entry.focus_set()
            messagebox.showerror("Error!!", "GST cannot be more than 100%.", parent=p_add)
            return

        try:
            cur.execute(f"INSERT INTO inventory (product_id, product_name, product_hsn, product_brand, product_size, product_color, product_stock, \
                        product_mrp, product_gst, gender, product_cost, product_discounted_price, supplier_phone, supplier_name, supplier_mail) \
                        VALUES ('{p_id}', '{p_name}', '{p_hsn}', '{p_brand}', '{p_size}', '{p_color}', '{p_stock}', '{p_mrp}', '{p_gst}', '{gender}', \
                        '{p_cost}', '{p_discounted_price}', '{s_phone}', '{s_name}', '{s_mail}')")
            db.commit()
            messagebox.showinfo("Success!!", "Product added successfully.", parent=p_add)
            self.product_id_entry.configure(state="normal")
            self.clearr()
            self.product_id_entry.insert(0, get_available_product_id())
            self.product_id_entry.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error!!", "Something went wrong while updating database.", parent=p_add)
            logging.exception(e)
                        
        self.product_name_entry.focus_set()

    def clearr(self):
        
        for widget in p_add.winfo_children():
            if isinstance(widget, Entry) and widget != self.product_stock_entry and widget != self.product_hsn_entry:
                widget.delete(0, END)
        self.product_name_entry.focus_set()

class UpdateProductDetails:
    def __init__(self, top=None):
        top.geometry(f"{sub_screen_size[0]}x{sub_screen_size[1]}+{sub_screen_x}+{sub_screen_y}")
        top.resizable(0, 0)
        top.title("Update Product")

        self.label1 = Label(p_update)
        self.label1.place(relx=0.0, rely=0.0, width=sub_screen_size[0], height=sub_screen_size[1])
        img = resize_image(update_product_img, sub_screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.int_validator, self.float_validator = p_update.register(validate_int), p_update.register(validate_float)

        self.product_id_entry = Entry(p_update)
        self.product_id_entry.place(relx=0.3375, rely=0.155, width=screen_ratio[0]*400, height=screen_ratio[1]*40)
        self.product_id_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*18)), relief="flat")
        self.product_id_entry.bind("<Return>", lambda event: self.product_name_entry.focus())
        self.product_id_entry.bind("<Down>", lambda event: self.product_name_entry.focus())

        self.product_name_entry = Entry(p_update)
        self.product_name_entry.place(relx=0.075, rely=0.319, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_name_entry.configure(font=medium_font, relief="flat")
        self.product_name_entry.bind("<Return>", lambda event: self.product_hsn_entry.focus())
        self.product_name_entry.bind("<Down>", lambda event: self.product_hsn_entry.focus())
        self.product_name_entry.bind("<Up>", lambda event: self.product_id_entry.focus())

        self.product_hsn_entry = Entry(p_update)
        self.product_hsn_entry.place(relx=0.075, rely=0.449, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_hsn_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.product_hsn_entry.bind("<Return>", lambda event: self.product_brand_entry.focus())
        self.product_hsn_entry.bind("<Down>", lambda event: self.product_brand_entry.focus())

        self.product_brand_entry = Entry(p_update)
        self.product_brand_entry.place(relx=0.075, rely=0.579, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_brand_entry.configure(font=medium_font, relief="flat")
        self.product_brand_entry.bind("<Return>", lambda event: self.product_mrp_entry.focus())
        self.product_brand_entry.bind("<Down>", lambda event: self.product_mrp_entry.focus())
        self.product_brand_entry.bind("<Up>", lambda event: self.product_hsn_entry.focus())

        self.product_mrp_entry = Entry(p_update)
        self.product_mrp_entry.place(relx=0.075, rely=0.711, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_mrp_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_mrp_entry.bind("<Return>", lambda event: self.product_gst_entry.focus())
        self.product_mrp_entry.bind("<Down>", lambda event: self.product_gst_entry.focus())
        self.product_mrp_entry.bind("<Up>", lambda event: self.product_brand_entry.focus())

        self.product_gst_entry = Entry(p_update)
        self.product_gst_entry.place(relx=0.075, rely=0.8425, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.product_gst_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_gst_entry.bind("<Return>", lambda event: self.product_stock_entry.focus())
        self.product_gst_entry.bind("<Down>", lambda event: self.product_stock_entry.focus())
        self.product_gst_entry.bind("<Up>", lambda event: self.product_mrp_entry.focus())

        self.product_stock_entry = Entry(p_update)
        self.product_stock_entry.place(relx=0.375, rely=0.319, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_stock_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.product_stock_entry.bind("<Return>", lambda event: self.product_size_entry.focus())
        self.product_stock_entry.bind("<Down>", lambda event: self.product_size_entry.focus())
        self.product_stock_entry.bind("<Up>", lambda event: self.product_gst_entry.focus())

        self.product_size_entry = Entry(p_update)
        self.product_size_entry.place(relx=0.375, rely=0.449, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_size_entry.configure(font=medium_font, relief="flat")
        self.product_size_entry.bind("<Return>", lambda event: self.product_color_entry.focus())
        self.product_size_entry.bind("<Down>", lambda event: self.product_color_entry.focus())
        self.product_size_entry.bind("<Up>", lambda event: self.product_stock_entry.focus())

        self.product_color_entry = Entry(p_update)
        self.product_color_entry.place(relx=0.375, rely=0.579, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_color_entry.configure(font=medium_font, relief="flat")
        self.product_color_entry.bind("<Return>", lambda event: self.product_discounted_price.focus())
        self.product_color_entry.bind("<Down>", lambda event: self.product_discounted_price.focus())
        self.product_color_entry.bind("<Up>", lambda event: self.product_size_entry.focus())

        self.product_discounted_price = Entry(p_update)
        self.product_discounted_price.place(relx=0.375, rely=0.711, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_discounted_price.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_discounted_price.bind("<Return>", lambda event: self.product_cost_entry.focus())
        self.product_discounted_price.bind("<Down>", lambda event: self.product_cost_entry.focus())
        self.product_discounted_price.bind("<Up>", lambda event: self.product_color_entry.focus())

        self.product_cost_entry = Entry(p_update)
        self.product_cost_entry.place(relx=0.375, rely=0.8425, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.product_cost_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.float_validator, "%P"))
        self.product_cost_entry.bind("<Return>", lambda event: self.gender_entry.focus())
        self.product_cost_entry.bind("<Down>", lambda event: self.gender_entry.focus())
        self.product_cost_entry.bind("<Up>", lambda event: self.product_discounted_price.focus())

        self.gender_entry = Entry(p_update)
        self.gender_entry.place(relx=0.648, rely=0.319, width=screen_ratio[0]*290, height=screen_ratio[1]*33)
        self.gender_entry.configure(font=medium_font, relief="flat")
        self.gender_entry.bind("<Return>", lambda event: self.supplier_phone_entry.focus())
        self.gender_entry.bind("<Down>", lambda event: self.supplier_phone_entry.focus())
        self.gender_entry.bind("<Up>", lambda event: self.product_cost_entry.focus())

        self.supplier_phone_entry = Entry(p_update)
        self.supplier_phone_entry.place(relx=0.648, rely=0.449, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_phone_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.supplier_phone_entry.bind("<Return>", lambda event: self.supplier_name_entry.focus())
        self.supplier_phone_entry.bind("<Down>", lambda event: self.supplier_name_entry.focus())
        self.supplier_phone_entry.bind("<Up>", lambda event: self.gender_entry.focus())

        self.supplier_name_entry = Entry(p_update)
        self.supplier_name_entry.place(relx=0.648, rely=0.579, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_name_entry.configure(font=medium_font, relief="flat")
        self.supplier_name_entry.bind("<Return>", lambda event: self.supplier_mail_entry.focus())
        self.supplier_name_entry.bind("<Down>", lambda event: self.supplier_mail_entry.focus())
        self.supplier_name_entry.bind("<Up>", lambda event: self.supplier_phone_entry.focus())

        self.supplier_mail_entry = Entry(p_update)
        self.supplier_mail_entry.place(relx=0.648, rely=0.709, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.supplier_mail_entry.configure(font=medium_font, relief="flat")
        self.supplier_mail_entry.bind("<Up>", lambda event: self.supplier_name_entry.focus())

        # self.search_btn = Button(p_update)
        # self.search_btn.place(relx=0.718, rely=0.155, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        # self.search_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="SEARCH", activebackground="#FFE59C",
        #                             font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
        #                             command=self.search_product_id)

        self.cancel_btn = Button(p_update)
        self.cancel_btn.place(relx=0.655, rely=0.8283, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.cancel_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="CANCEL", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.cancel_update)
        
        self.update_btn = Button(p_update)
        self.update_btn.place(relx=0.813, rely=0.8283, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.update_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="UPDATE", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.update_product_details)
        
        for widget in p_update.winfo_children():
            
            if isinstance(widget, Entry):
                widget.bind("<FocusIn>", lambda event, widget=widget: widget.select_range(0, END))

    def update_product_details(self):
            
        sure = messagebox.askyesno("Update", "Are you sure you want to update the product details?", parent=p_update)
        if not sure:
            return
        
        try:
            p_id, p_name, p_hsn, p_brand = self.product_id_entry.get().strip().upper(), format_name(self.product_name_entry.get()), self.product_hsn_entry.get(), format_name(self.product_brand_entry.get())
            p_mrp, p_stock, p_gst, p_size = self.product_mrp_entry.get(), self.product_stock_entry.get(),self.product_gst_entry.get(), format_name(self.product_size_entry.get())
            p_color, gender, p_cost, p_discounted_price = format_name(self.product_color_entry.get()), format_name(self.gender_entry.get()), self.product_cost_entry.get(), self.product_discounted_price.get()
            s_phone, s_name, s_mail = self.supplier_phone_entry.get(), format_name(self.supplier_name_entry.get()), self.supplier_mail_entry.get().strip()

            p_mrp, p_discounted_price, p_stock, p_gst = float(p_mrp), float(p_discounted_price), int(p_stock), float(p_gst)
            gender = "Unisex" if gender == '' else gender
            p_cost = p_mrp if p_cost == '' else float(p_cost)
            p_discounted_price = p_mrp if p_discounted_price == '' else float(p_discounted_price)

            if p_discounted_price > p_mrp:
                self.product_discounted_price.focus_set()
                messagebox.showerror("Error!!", "Discounted price cannot be more than MRP.", parent=p_add)
                return

            if p_gst > 100:
                self.product_gst_entry.focus_set()
                messagebox.showerror("Error!!", "GST cannot be more than 100%.", parent=p_add)
                return

            cur.execute(f"UPDATE inventory SET product_name='{p_name}', product_hsn='{p_hsn}', product_brand='{p_brand}', product_size='{p_size}', \
                        product_color='{p_color}', product_stock='{p_stock}', product_mrp='{p_mrp}', product_gst='{p_gst}', gender='{gender}', \
                        product_cost='{p_cost}', product_discounted_price='{p_discounted_price}', supplier_phone='{s_phone}', supplier_name='{s_name}', \
                        supplier_mail='{s_mail}' WHERE product_id='{p_id}'")
            db.commit()
            messagebox.showinfo("Success!!", "Product updated successfully.", parent=p_update)
            p_update.destroy()
            inv.deiconify()
            inv_pg.tree.focus_set()
            inv_pg.DisplayData()
            item_id = inv_pg.tree.identify_row(self.event.y)
            inv_pg.tree.selection_set(item_id)
            inv_pg.tree.focus(item_id)
            
        except Exception as e:
            messagebox.showerror("Error!!", "Something went wrong while updating database.", parent=p_update)
            logging.exception(e)
        
    def cancel_update(self):
            
        sure = messagebox.askyesno("Cancel", "Are you sure you want to cancel?", parent=p_update)
        if not sure:
            return
        p_update.destroy()
        inv.deiconify()

class Employee:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Employee Management")

        self.label1 = Label(emp)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(employee_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img


        self.clock = Label(emp)
        self.clock.place(relx=0.1695, rely=0.1575, width=screen_ratio[0]*105, height=screen_ratio[1]*40)
        self.clock.configure(
            font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*14)),
            foreground="#000000",
            background="#FFFFFF"
        )

        self.logout_btn = Button(emp)
        self.logout_btn.place(relx=0.895, rely=0.08, width=screen_ratio[0]*102, height=screen_ratio[1]*50)
        img = resize_image(logout_img, (int(screen_ratio[0]*102), int(screen_ratio[1]*50)))
        self.logout_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.Logout, background="#ffffff")
        self.logout_btn.img = img
        
        self.employee_key_entry = Entry(emp)
        self.employee_key_entry.place(relx=0.043, rely=0.337, width=screen_ratio[0]*300, height=screen_ratio[1]*40)
        self.employee_key_entry.configure(font=medium_font, relief="flat")
        self.employee_key_entry.bind("<Return>", lambda event: self.search_employees())

        self.employee_search_btn = Button(emp)
        self.employee_search_btn.place(relx=0.1, rely=0.407, width=screen_ratio[0]*126, height=screen_ratio[1]*35)
        self.employee_search_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Search", activebackground="#FFE59C", 
                                          font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"), 
                                          command=self.search_employees)
        self.add_employee_btn = Button(emp)
        self.add_employee_btn.place(relx=0.06, rely=0.553, width=screen_ratio[0]*250, height=screen_ratio[1]*45)
        self.add_employee_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Add employee(s)", activebackground="#FFE59C",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.add_employee)
   
        self.exit_btn = Button(emp)
        self.exit_btn.place(relx=0.086, rely=0.862, width=screen_ratio[0]*170, height=screen_ratio[1]*45)
        self.exit_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Exit", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.Exit)


        style.theme_use("clam")
        style.configure("tree.Treeview", highlightthickness=0, bd=0, font=small_font) # Modify the font of the body
        style.configure("tree.Treeview.Heading", font=("Segoe UI Semibold", int(0.5*(screen_ratio[0]+screen_ratio[1])*14)), background='#FFDF7F', foreground='black', borderwidth=0) # Modify the font of the headings
        style.layout("tree.Treeview", [('tree.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders
        style.configure("tree.Treeview", rowheight=int(screen_ratio[0]*40))
        self.tree = ttk.Treeview(emp, style="tree.Treeview")
        self.scrollbarx = Scrollbar(emp, orient=HORIZONTAL)
        self.scrollbary = Scrollbar(emp, orient=VERTICAL)
        self.scrollbarx.configure(command=self.tree.xview)
        self.scrollbary.configure(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbary.set, xscrollcommand=self.scrollbarx.set)

        self.tree.place(relx=0.28, rely=0.164, width=screen_ratio[0]*990, height=screen_ratio[1]*610)
        self.scrollbary.place(relx=0.954, rely=0.203, width=screen_ratio[0]*22, height=screen_ratio[1]*548)
        self.scrollbarx.place(relx=0.28, rely=0.9, width=screen_ratio[0]*990, height=screen_ratio[1]*22)

        self.tree.configure(columns=employee_columns)
        self.tree_d = {col: i for i, col in enumerate(self.tree["columns"])}

        self.tree.heading("emp_id", text="Employee ID", anchor=W)
        self.tree.heading("emp_username", text="Username", anchor=W)
        self.tree.heading("emp_name", text="Name", anchor=W)
        self.tree.heading("emp_phone", text="Phone", anchor=W)
        self.tree.heading("emp_mail", text="Mail", anchor=W)
        self.tree.heading("emp_address", text="Address", anchor=W)
        self.tree.heading("emp_designation", text="Designation", anchor=W)

        self.tree['show'] = 'headings'
        self.tree.column("emp_id", width=int(screen_ratio[0]*150), anchor=W)
        self.tree.column("emp_username", width=int(screen_ratio[0]*180), anchor=W)
        self.tree.column("emp_name", width=int(screen_ratio[0]*180), anchor=W)
        self.tree.column("emp_phone", width=int(screen_ratio[0]*140), anchor=W)
        self.tree.column("emp_mail", width=int(screen_ratio[0]*220), anchor=W)
        self.tree.column("emp_address", width=int(screen_ratio[0]*250), anchor=W)
        self.tree.column("emp_designation", width=int(screen_ratio[0]*120), anchor=W)

        self.tree.bind("<Delete>", lambda event: self.delete_emp())
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-Button-1>", self.update_emp)


        self.DisplayData()

    def DisplayData(self):
        self.tree.delete(*self.tree.get_children())
        cur.execute("SELECT * FROM employee")
        fetch = cur.fetchall()
        for data in fetch:
            data = list(data)
            self.tree.insert("", "end", values=(data[0], data[1], data[2], data[3], data[4], data[5], data[7]))


    def search_employees(self):

        search = self.employee_key_entry.get().strip()
        if search == '':
            self.DisplayData()
            return
        cur.execute(f"SELECT * FROM employee WHERE emp_id LIKE '%{search}%' OR emp_name LIKE '%{search}%' OR emp_designation LIKE '%{search}%'")
        fetch = cur.fetchall()
        if len(fetch) == 0:
            messagebox.showerror("Error!!", "No employee found.", parent=emp)
            return
        self.tree.delete(*self.tree.get_children())
        for data in fetch:
            self.tree.insert("", "end", values=(data[0], data[1], data[2], data[3], data[4], data[5], data[7]))


    def delete_emp(self):
        
        ids = self.tree.selection()
        if len(ids) == 0:
            return
        sure = messagebox.askyesno("Delete", "Are you sure you want to delete the selected employee(s)?", parent=emp)
        if sure == True:
            for i in ids:
                # check that tree id has data
                try:
                    self.tree.item(i)["values"][0]
                except:
                    continue
                if self.tree.item(i)["values"][0] in [1, '1']:
                    messagebox.showerror("Error","Cannot update master admin.", parent=emp)
                    continue
                cur.execute("DELETE FROM employee WHERE emp_id=?", (self.tree.item(i)["values"][0],))
                self.tree.delete(i)
            db.commit()
            messagebox.showinfo("Success!!", "Employee(s) deleted successfully.", parent=emp)

    def update_emp(self, event=None):

        if len(self.tree.selection()) == 1:
            if self.tree.identify_region(event.x, event.y) == "heading":
                return
            
            global e_update
            e_update = Toplevel()
            update_emp_pg = UpdateEmployeeDetails(e_update)
            update_emp_pg.employee_username_entry.focus()
            update_emp_pg.event = event
            e_update.bind("<Return>", lambda event: update_emp_pg.update_employee_details())
            e_update.protocol("WM_DELETE_WINDOW", lambda: self.exit_custom(e_update))

            update_emp_pg.employee_id_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_id"]])
            update_emp_pg.employee_id_entry.configure(state="disabled")
            update_emp_pg.employee_username_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_username"]])
            update_emp_pg.employee_name_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_name"]])
            update_emp_pg.employee_phone_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_phone"]])
            update_emp_pg.employee_mail_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_mail"]])
            update_emp_pg.employee_desg_entry.insert(0, self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_designation"]])
            emp_address = self.tree.item(self.tree.selection()[0])["values"][self.tree_d["emp_address"]]
            if emp_address != '' and '\n' in emp_address:
                update_emp_pg.employee_address1_entry.insert(0, emp_address.split("\n")[0])
                update_emp_pg.employee_address2_entry.insert(0, emp_address.split("\n")[1])
            else:
                update_emp_pg.employee_address1_entry.insert(0, '')
                update_emp_pg.employee_address2_entry.insert(0, '')

        elif len(self.tree.selection()) == 0:
            messagebox.showerror("Error","Please choose an employee to update.", parent=emp)
        else:
            messagebox.showerror("Error","Can only update one employee at a time.", parent=emp)

    def show_context_menu(self, event):
        self.sel = self.tree.selection()
        if len(self.sel) == 0:
            return
        if self.tree.identify_region(event.x, event.y) == "heading":
            return
        menu = Menu(emp, tearoff=0)
        menu.add_command(label="Update", command=lambda event=event: self.update_emp(event))
        menu.add_command(label="Delete", command=self.delete_emp)
        menu.post(event.x_root, event.y_root)

    def add_employee(self):
        global e_add
        e_add = Toplevel()
        update_product_pg = AddEmployeeDetails(e_add)
        update_product_pg.employee_username_entry.focus()
        e_add.protocol("WM_DELETE_WINDOW", lambda: self.exit_custom(e_add))


    def exit_custom(self, window):

        sure = messagebox.askyesno("Exit", "Are you sure you want to exit?", parent=window)
        if sure == True:
            window.destroy()
            emp.deiconify()
            self.DisplayData()

    def Exit(self):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=emp)
        if sure == True:
            emp.destroy()
            adm.deiconify()

    def time(self):
        string = strftime("%I:%M:%S %p")
        self.clock.config(text=string)
        self.clock.after(1000, self.time)

    def Logout(self):
        sure = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if sure == True:
            emp.destroy()
            admin_lgn.deiconify()
            # admin_lgn.adm_username_entry.delete(0, END)
            # admin_lgn.adm_password_entry.delete(0, END)

class AddEmployeeDetails:
    def __init__(self, top=None):
        top.geometry(f"{sub_screen_size[0]}x{sub_screen_size[1]}+{sub_screen_x}+{sub_screen_y}")
        top.resizable(0, 0)
        top.title("Add Employee")

        self.label1 = Label(e_add)
        self.label1.place(relx=0.0, rely=0.0, width= sub_screen_size[0], height=sub_screen_size[1])
        img = resize_image(add_employee_img, sub_screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.int_validator, self.float_validator = e_add.register(validate_int), e_add.register(validate_float)

        self.employee_id_entry = Entry(e_add)
        self.employee_id_entry.place(relx=0.3375, rely=0.155, width=screen_ratio[0]*400, height=screen_ratio[1]*40)
        self.employee_id_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*18)), relief="flat")
        self.employee_id_entry.insert(0, get_available_emp_id())
        self.employee_id_entry.configure(state="disabled")

        self.employee_username_entry = Entry(e_add)
        self.employee_username_entry.place(relx=0.215, rely=0.3335, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_username_entry.configure(font=medium_font, relief="flat")
        self.employee_username_entry.bind("<Return>", lambda event: self.employee_pswd_entry.focus())
        self.employee_username_entry.bind("<Down>", lambda event: self.employee_pswd_entry.focus())

        self.employee_pswd_entry = Entry(e_add)
        self.employee_pswd_entry.place(relx=0.215, rely=0.465, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_pswd_entry.configure(font=medium_font, relief="flat", show="*")
        self.employee_pswd_entry.bind("<Return>", lambda event: self.employee_pswd_re_entry.focus())
        self.employee_pswd_entry.bind("<Down>", lambda event: self.employee_pswd_re_entry.focus())
        self.employee_pswd_entry.bind("<Up>", lambda event: self.employee_username_entry.focus())

        self.pswd_dont_match = Label(e_add)
        self.pswd_dont_match.configure(text="Passwords don't match.", font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*10)), foreground="#FF0000", background="#ffffff", anchor=W)

        self.employee_pswd_re_entry = Entry(e_add)
        self.employee_pswd_re_entry.place(relx=0.215, rely=0.5965, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_pswd_re_entry.configure(font=medium_font, relief="flat", show="*")
        self.employee_pswd_re_entry.bind("<Return>", lambda event: self.employee_name_entry.focus())
        self.employee_pswd_re_entry.bind("<Down>", lambda event: self.employee_name_entry.focus())
        self.employee_pswd_re_entry.bind("<Up>", lambda event: self.employee_pswd_entry.focus())
        self.employee_pswd_re_entry.bind("<FocusOut>", self.check_password)

        self.employee_name_entry = Entry(e_add)
        self.employee_name_entry.place(relx=0.215, rely=0.728, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_name_entry.configure(font=medium_font, relief="flat")
        self.employee_name_entry.bind("<Return>", lambda event: self.employee_phone_entry.focus())
        self.employee_name_entry.bind("<Down>", lambda event: self.employee_phone_entry.focus())
        self.employee_name_entry.bind("<Up>", lambda event: self.employee_pswd_entry.focus())

        self.employee_phone_entry = Entry(e_add)
        self.employee_phone_entry.place(relx=0.215, rely=0.8595, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_phone_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.employee_phone_entry.bind("<Return>", lambda event: self.employee_desg_entry.focus())
        self.employee_phone_entry.bind("<Down>", lambda event: self.employee_desg_entry.focus())
        self.employee_phone_entry.bind("<Up>", lambda event: self.employee_name_entry.focus())


        style.theme_use("clam")
        style.map("desg_options.TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#000000")], selectforeground=[("readonly", "black")], 
                    selectbackground=[("readonly", "#ffffff")], background=[("readonly", "#ffffff")], bordercolor=[("readonly", "#ffffff")])
        self.employee_desg = StringVar()
        self.employee_desg.set("Employee")
        self.employee_desg_entry = ttk.Combobox(e_add, textvariable=self.employee_desg,values=["Admin", "Employee"], state="readonly", style="desg_options.TCombobox")
        self.employee_desg_entry.place(relx=0.513, rely=0.332, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_desg_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*14)))
        self.employee_desg_entry.bind("<Return>", lambda event: self.employee_mail_entry.focus())
        self.employee_desg_entry.bind("<Down>", lambda event: self.employee_mail_entry.focus())
        self.employee_desg_entry.bind("<Up>", lambda event: self.employee_phone_entry.focus())

        self.employee_mail_entry = Entry(e_add)
        self.employee_mail_entry.place(relx=0.513, rely=0.464, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_mail_entry.configure(font=medium_font, relief="flat")
        self.employee_mail_entry.bind("<Return>", lambda event: self.employee_address1_entry.focus())
        self.employee_mail_entry.bind("<Down>", lambda event: self.employee_address1_entry.focus())
        self.employee_mail_entry.bind("<Up>", lambda event: self.employee_desg_entry.focus())

        self.employee_address1_entry = Entry(e_add)
        self.employee_address1_entry.place(relx=0.513, rely=0.595, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_address1_entry.configure(font=medium_font, relief="flat")
        self.employee_address1_entry.bind("<Return>", lambda event: self.employee_address2_entry.focus())
        self.employee_address1_entry.bind("<Down>", lambda event: self.employee_address2_entry.focus())
        self.employee_address1_entry.bind("<Up>", lambda event: self.employee_mail_entry.focus())

        self.employee_address2_entry = Entry(e_add)
        self.employee_address2_entry.place(relx=0.513, rely=0.725, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_address2_entry.configure(font=medium_font, relief="flat")

        self.clear_btn = Button(e_add)
        self.clear_btn.place(relx=0.52, rely=0.84, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.clear_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="CLEAR", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.clearr)
        
        self.add_btn = Button(e_add)
        self.add_btn.place(relx=0.675, rely=0.84, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.add_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="ADD", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.add_employee_details)
        
        for widget in e_add.winfo_children():
            if isinstance(widget, Entry):
                widget.bind("<FocusIn>", lambda event, widget=widget: widget.select_range(0, END))
        
    def check_password(self, event=None):

        if self.employee_pswd_entry.get() != self.employee_pswd_re_entry.get():
            self.pswd_dont_match.place(relx=0.215, rely=0.52, width=screen_ratio[0]*325, height=screen_ratio[1]*16)
            self.employee_pswd_re_entry.focus()
        else:
            self.pswd_dont_match.place_forget()

    def clearr(self):

        for widget in e_add.winfo_children():
            if isinstance(widget, Entry):
                widget.delete(0, END)
        self.employee_username_entry.focus_set()


    def add_employee_details(self):
        
        e_id, e_username, e_pswd, e_name = self.employee_id_entry.get().strip(), self.employee_username_entry.get().strip(), self.employee_pswd_entry.get().strip(), self.employee_name_entry.get().strip()
        e_phone, e_desg, e_mail, e_add1, e_add2 = self.employee_phone_entry.get(), self.employee_desg.get(), self.employee_mail_entry.get().strip(), self.employee_address1_entry.get().strip(), self.employee_address2_entry.get().strip()

        required_fields = [e_username, e_pswd, e_name, e_phone, e_desg]
        if '' in required_fields:
            messagebox.showerror("Error!!", "Please fill all the required fields.", parent=e_add)
            return
        
        results = cur.execute("SELECT * FROM employee WHERE emp_username=?", (e_username,)).fetchall()
        if len(results) != 0:
            messagebox.showerror("Error!!", "Username already exists.", parent=e_add)
            return
        
        if not valid_phone(e_phone):
            messagebox.showerror("Error!!", "Invalid phone number.", parent=e_add)
            return
        
        sure = messagebox.askyesno("Add", "Are you sure you want to add this employee?", parent=e_add)
        if not sure:
            return
        e_pswd = hashlib.sha256(e_pswd.encode()).hexdigest()
        e_add12 = e_add1.replace("\n", "") + "\n" + e_add2.replace("\n", "")
        try:

            cur.execute(f"INSERT INTO employee (emp_id, emp_username, emp_password, emp_name, emp_phone, emp_designation, emp_mail, emp_address) \
                        VALUES ('{e_id}', '{e_username}', '{e_pswd}', '{e_name}', '{e_phone}', '{e_desg}', '{e_mail}', '{e_add12}')")
            db.commit()
            messagebox.showinfo("Success!!", "Employee added successfully.", parent=e_add)
            self.employee_id_entry.configure(state="normal")
            self.clearr()
            self.employee_id_entry.insert(0, get_available_emp_id())
            self.employee_id_entry.configure(state="disabled")
            self.employee_username_entry.focus_set()
        except Exception as e:
            messagebox.showerror("Error!!", "Something went wrong while adding employee.", parent=e_add)
            logging.exception(e)

class UpdateEmployeeDetails:
    def __init__(self, top=None):
        top.geometry(f"{sub_screen_size[0]}x{sub_screen_size[1]}+{sub_screen_x}+{sub_screen_y}")
        top.resizable(0, 0)
        top.title("Update Employee")

        self.label1 = Label(e_update)
        self.label1.place(relx=0.0, rely=0.0, width= sub_screen_size[0], height=sub_screen_size[1])
        img = resize_image(update_employee_img, sub_screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.int_validator, self.float_validator = e_update.register(validate_int), e_update.register(validate_float)

        self.employee_id_entry = Entry(e_update)
        self.employee_id_entry.place(relx=0.3375, rely=0.155, width=screen_ratio[0]*400, height=screen_ratio[1]*40)
        self.employee_id_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*18)), relief="flat")

        self.employee_username_entry = Entry(e_update)
        self.employee_username_entry.place(relx=0.215, rely=0.3335, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_username_entry.configure(font=medium_font, relief="flat")
        self.employee_username_entry.bind("<Return>", lambda event: self.employee_pswd_entry.focus())
        self.employee_username_entry.bind("<Down>", lambda event: self.employee_pswd_entry.focus())

        self.employee_pswd_entry = Entry(e_update)
        self.employee_pswd_entry.place(relx=0.215, rely=0.465, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_pswd_entry.configure(font=medium_font, relief="flat", show="*")
        self.employee_pswd_entry.bind("<Return>", lambda event: self.employee_pswd_re_entry.focus())
        self.employee_pswd_entry.bind("<Down>", lambda event: self.employee_pswd_re_entry.focus())
        self.employee_pswd_entry.bind("<Up>", lambda event: self.employee_username_entry.focus())

        self.pswd_dont_match = Label(e_update)
        self.pswd_dont_match.configure(text="Passwords don't match.", font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*10)), foreground="#FF0000", background="#ffffff", anchor=W)

        self.employee_pswd_re_entry = Entry(e_update)
        self.employee_pswd_re_entry.place(relx=0.215, rely=0.5965, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_pswd_re_entry.configure(font=medium_font, relief="flat", show="*")
        self.employee_pswd_re_entry.bind("<Return>", lambda event: self.employee_name_entry.focus())
        self.employee_pswd_re_entry.bind("<Down>", lambda event: self.employee_name_entry.focus())
        self.employee_pswd_re_entry.bind("<Up>", lambda event: self.employee_pswd_entry.focus())
        self.employee_pswd_re_entry.bind("<FocusOut>", self.check_password)

        self.employee_name_entry = Entry(e_update)
        self.employee_name_entry.place(relx=0.215, rely=0.728, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_name_entry.configure(font=medium_font, relief="flat")
        self.employee_name_entry.bind("<Return>", lambda event: self.employee_phone_entry.focus())
        self.employee_name_entry.bind("<Down>", lambda event: self.employee_phone_entry.focus())
        self.employee_name_entry.bind("<Up>", lambda event: self.employee_pswd_entry.focus())

        self.employee_phone_entry = Entry(e_update)
        self.employee_phone_entry.place(relx=0.215, rely=0.8595, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_phone_entry.configure(font=medium_font, relief="flat", validate="key", validatecommand=(self.int_validator, "%P"))
        self.employee_phone_entry.bind("<Return>", lambda event: self.employee_desg_entry.focus())
        self.employee_phone_entry.bind("<Down>", lambda event: self.employee_desg_entry.focus())
        self.employee_phone_entry.bind("<Up>", lambda event: self.employee_name_entry.focus())

        style.theme_use("clam")
        style.map("desg_options.TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#000000")], selectforeground=[("readonly", "black")], 
                    selectbackground=[("readonly", "#ffffff")], background=[("readonly", "#ffffff")], bordercolor=[("readonly", "#ffffff")])
        self.employee_desg = StringVar()
        self.employee_desg.set("Employee")
        self.employee_desg_entry = ttk.Combobox(e_update, textvariable=self.employee_desg,values=["Admin", "Employee"], state="readonly", style="desg_options.TCombobox")
        self.employee_desg_entry.place(relx=0.513, rely=0.332, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_desg_entry.configure(font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*14)))
        self.employee_desg_entry.bind("<Return>", lambda event: self.employee_mail_entry.focus())
        self.employee_desg_entry.bind("<Down>", lambda event: self.employee_mail_entry.focus())
        self.employee_desg_entry.bind("<Up>", lambda event: self.employee_phone_entry.focus())

        self.employee_mail_entry = Entry(e_update)
        self.employee_mail_entry.place(relx=0.513, rely=0.464, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_mail_entry.configure(font=medium_font, relief="flat")
        self.employee_mail_entry.bind("<Return>", lambda event: self.employee_address1_entry.focus())
        self.employee_mail_entry.bind("<Down>", lambda event: self.employee_address1_entry.focus())
        self.employee_mail_entry.bind("<Up>", lambda event: self.employee_desg_entry.focus())

        self.employee_address1_entry = Entry(e_update)
        self.employee_address1_entry.place(relx=0.513, rely=0.595, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_address1_entry.configure(font=medium_font, relief="flat")
        self.employee_address1_entry.bind("<Return>", lambda event: self.employee_address2_entry.focus())
        self.employee_address1_entry.bind("<Down>", lambda event: self.employee_address2_entry.focus())
        self.employee_address1_entry.bind("<Up>", lambda event: self.employee_mail_entry.focus())

        self.employee_address2_entry = Entry(e_update)
        self.employee_address2_entry.place(relx=0.513, rely=0.725, width=screen_ratio[0]*325, height=screen_ratio[1]*33)
        self.employee_address2_entry.configure(font=medium_font, relief="flat")

        self.cancel_btn = Button(e_update)
        self.cancel_btn.place(relx=0.52, rely=0.84, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.cancel_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="CLEAR", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.cancel)
        
        self.update_btn = Button(e_update)
        self.update_btn.place(relx=0.675, rely=0.84, width=screen_ratio[0]*120, height=screen_ratio[1]*35)
        self.update_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="UPDATE", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.update_employee_details)
        
        for widget in e_update.winfo_children():
            if isinstance(widget, Entry):
                widget.bind("<FocusIn>", lambda event, widget=widget: widget.select_range(0, END))
        
    def check_password(self, event=None):

        if self.employee_pswd_entry.get() != self.employee_pswd_re_entry.get():
            self.pswd_dont_match.place(relx=0.215, rely=0.52, width=screen_ratio[0]*325, height=screen_ratio[1]*16)
            self.employee_pswd_re_entry.focus()
        else:
            self.pswd_dont_match.place_forget()
    
    def cancel(self):
        sure = messagebox.askyesno("Cancel", "Are you sure you want to cancel?", parent=e_update)
        if not sure:
            return
        e_update.destroy()
        inv.deiconify()

    def update_employee_details(self):
            
        e_id, e_username, e_pswd, e_name = self.employee_id_entry.get(), self.employee_username_entry.get(), self.employee_pswd_entry.get(), self.employee_name_entry.get()
        e_phone, e_desg, e_mail, e_add1, e_add2 = self.employee_phone_entry.get(), self.employee_desg.get(), self.employee_mail_entry.get(), self.employee_address1_entry.get(), self.employee_address2_entry.get()

        required_fields = [e_username, e_pswd, e_name, e_phone, e_desg]
        if '' in required_fields:
            messagebox.showerror("Error!!", "Please fill all the required fields.", parent=e_update)
            return
        
        if not valid_phone(e_phone):
            messagebox.showerror("Error!!", "Invalid phone number.", parent=e_update)
            return
        
        sure = messagebox.askyesno("Update", "Are you sure you want to update this employee?", parent=e_update)
        if not sure:
            return
        e_pswd = hashlib.sha256(e_pswd.encode()).hexdigest()
        try:
            cur.execute(f"UPDATE employee SET emp_username='{e_username}', emp_password='{e_pswd}', emp_name='{e_name}', emp_phone='{e_phone}', emp_designation='{e_desg}', emp_mail='{e_mail}', emp_address='{e_add1 + ' ' + e_add2}' WHERE emp_id='{e_id}'")
            db.commit()
            messagebox.showinfo("Success!!", "Employee updated successfully.", parent=e_update)
            e_update.destroy()
            emp.deiconify()
            emp_mngmnt_pg.DisplayData()
            item_id = emp_mngmnt_pg.tree.identify_row(self.event.y)
            emp_mngmnt_pg.tree.selection_set(item_id)
            emp_mngmnt_pg.tree.focus(item_id)

        except Exception as e:
            messagebox.showerror("Error!!", "Something went wrong while updating employee.", parent=e_update)
            logging.exception(e)\

class Invoice:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Invoice Management")

        self.label1 = Label(invc)
        self.label1.place(relx=0.0, rely=0.0, width= screen_size[0], height=screen_size[1])
        img = resize_image(invoice_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.clock = Label(invc)
        self.clock.place(relx=0.1695, rely=0.1575, width=screen_ratio[0]*105, height=screen_ratio[1]*40)
        self.clock.configure(
            font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*14)),
            foreground="#000000",
            background="#FFFFFF"
        )

        self.logout_btn = Button(invc)
        self.logout_btn.place(relx=0.895, rely=0.08, width=screen_ratio[0]*102, height=screen_ratio[1]*50)
        img = resize_image(logout_img, (int(screen_ratio[0]*102), int(screen_ratio[1]*50)))
        self.logout_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.Logout, background="#ffffff")
        self.logout_btn.img = img

        self.bill_key_entry = Entry(invc)
        self.bill_key_entry.place(relx=0.043, rely=0.337, width=screen_ratio[0]*300, height=screen_ratio[1]*40)
        self.bill_key_entry.configure(font=medium_font, relief="flat")
        self.bill_key_entry.bind("<Return>", lambda event: self.search_bill())

        self.bill_search_btn = Button(invc)
        self.bill_search_btn.place(relx=0.1, rely=0.407, width=screen_ratio[0]*126, height=screen_ratio[1]*35)
        self.bill_search_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Search", activebackground="#FFE59C",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.search_bill)
        
        # self.from_date = DateEntry(invc, selectmode='day')
        # self.from_date.place(relx=0.4, rely=0.4, width=screen_ratio[0]*126, height=screen_ratio[1]*35)

        self.export_btn = Button(invc)
        self.export_btn.place(relx=0.28, rely=0.095, width=screen_ratio[0]*160, height=screen_ratio[1]*35)
        self.export_btn.configure(background="#C1ECA4", borderwidth="0", cursor="hand2", text="Export to CSV", activebackground="#C1ECA4",
                                        font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                        command=self.export_bill)
        
        self.exit_btn = Button(invc)
        self.exit_btn.place(relx=0.086, rely=0.862, width=screen_ratio[0]*170, height=screen_ratio[1]*45)
        self.exit_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="Exit", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.Exit)
        
        style.theme_use("clam")
        style.configure("tree.Treeview", highlightthickness=0, bd=0, font=small_font) # Modify the font of the body
        style.configure("tree.Treeview.Heading", font=("Segoe UI Semibold", int(0.5*(screen_ratio[0]+screen_ratio[1])*14)), background='#FFDF7F', foreground='black', borderwidth=0) # Modify the font of the headings
        style.layout("tree.Treeview", [('tree.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders
        style.configure("tree.Treeview", rowheight=int(screen_ratio[0]*40))
        self.tree = ttk.Treeview(invc, style="tree.Treeview")
        self.scrollbarx = Scrollbar(invc, orient=HORIZONTAL)
        self.scrollbary = Scrollbar(invc, orient=VERTICAL)
        self.scrollbarx.configure(command=self.tree.xview)
        self.scrollbary.configure(command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbary.set, xscrollcommand=self.scrollbarx.set)
        
        self.tree.place(relx=0.28, rely=0.164, width=screen_ratio[0]*990, height=screen_ratio[1]*610)
        self.scrollbary.place(relx=0.954, rely=0.203, width=screen_ratio[0]*22, height=screen_ratio[1]*548)
        self.scrollbarx.place(relx=0.28, rely=0.9, width=screen_ratio[0]*990, height=screen_ratio[1]*22)

        self.tree.configure(columns=invoice_columns)
        self.tree_d = {col: i for i, col in enumerate(self.tree["columns"])}

        self.tree.heading("bill_no", text="Bill No.", anchor=W)
        self.tree.heading("date", text="Date", anchor=W)
        self.tree.heading("e_id", text="Emp ID", anchor=W)
        self.tree.heading("c_num", text="Cust No.", anchor=W)
        self.tree.heading("c_name", text="Cust Name", anchor=W)
        self.tree.heading("total", text="Total", anchor=W)
        self.tree.heading("net_total", text="Net Total", anchor=W)
        self.tree.heading("payment_method", text="Pay Method", anchor=W)
        self.tree.heading("payment_status", text="Pay Status", anchor=W)

        self.tree['show'] = 'headings'
        self.tree.column("bill_no", width=int(screen_ratio[0]*110), anchor=W)
        self.tree.column("date", width=int(screen_ratio[0]*140), anchor=W)
        self.tree.column("e_id", width=int(screen_ratio[0]*80), anchor=W)
        self.tree.column("c_num", width=int(screen_ratio[0]*120), anchor=W)
        self.tree.column("c_name", width=int(screen_ratio[0]*140), anchor=W)
        self.tree.column("total", width=int(screen_ratio[0]*123), anchor=W)
        self.tree.column("net_total", width=int(screen_ratio[0]*123), anchor=W)
        self.tree.column("payment_method", width=int(screen_ratio[0]*150), anchor=W)
        self.tree.column("payment_status", width=int(screen_ratio[0]*100), anchor=W)

        self.tree.bind("<Delete>", lambda event: self.delete_bill())
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.DisplayData()

    def DisplayData(self):
        self.tree.delete(*self.tree.get_children())
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        cur.execute("SELECT * FROM bill")
        fetch = cur.fetchall()
        for data in fetch:
            self.tree.insert("", "end", values=(data['bill_no'], data['date'], data['e_id'], data['c_num'], data['c_name'], data['total'], round(float(data['net_total']),2), data['payment_method'],data['payment_status']))

    def search_bill(self):
        search = self.bill_key_entry.get().strip()
        if search == '':
            self.DisplayData()
            return
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        cur.execute(f"SELECT * FROM bill WHERE bill_no LIKE '{search}%' OR c_num LIKE '{search}%' OR c_name LIKE '{search}%'")
        fetch = cur.fetchall()
        if len(fetch) == 0:
            messagebox.showerror("Error!!", "No invoice found.", parent=invc)
            return
        self.tree.delete(*self.tree.get_children())
        for data in fetch:
            self.tree.insert("", "end", values=(data['bill_no'], data['date'], data['e_id'], data['c_num'], data['c_name'], data['total'], data['net_total'], data['payment_method'],data['payment_status']))

    def export_bill(self):

        # get all the bills
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        results = cur.execute("SELECT * FROM bill").fetchall()
        if len(results) == 0:
            messagebox.showerror("Error!!", "No invoice found.", parent=invc)
            return
        
        # ask folder to save sales report tp csv
        folder_selected = askdirectory()
        if folder_selected == '':
            return
        
        # bill csv
        dt = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        with open(f"{folder_selected}/bill_report_{dt}.csv", 'w', newline='') as f:
            csv_writer = writer(f)
            csv_writer.writerow(["Bill No.", "Date", "Employee ID", "Customer Number", "Customer Name", "Total", "Net Total", "Payment Method", "Payment Status"])
            for row in results:
                csv_writer.writerow([row['bill_no'], row['date'], row['e_id'], row['c_num'], row['c_name'], row['total'], row['net_total'], row['payment_method'], row['payment_status']])
        
        # sales csv
        failed_bills = []
        with open(f"{folder_selected}/sales_report_{dt}.csv", 'w', newline='') as file:
            csv_writer = writer(file)
            csv_writer.writerow(['ID', 'Bill No', 'Date', 'Product ID', 'Quantity', 'Discounted Price', 'Double Discounted Price', 'GST', 'Taxable Amount', 'GST Amount', 'payment_method'])
            for i, bill in enumerate(results):
                try:
                    discount = float(bill['total']) - float(bill['net_total'])

                    for item in bill['bill_details'].split(','):
                        id = item.split(':')[0].split('-')[1]
                        qty = int(item.split(':')[1].strip())
                        prod_data = cur.execute("select * from inventory where product_id = ?", (id,)).fetchone()
                        discounted_price = float(prod_data['product_discounted_price'])
                        weighted_disc_per_item = round(discount*(discounted_price/float(bill['total'])),2)
                        # including gst
                        double_discounted_price = round(discounted_price - weighted_disc_per_item,2)
                        taxable_amount = round((double_discounted_price * qty) / (1 + (float(prod_data['product_gst'])/100)),2)
                        gst_amount = round((double_discounted_price * qty) - taxable_amount,2)

                        payment_methods = '-'.join([i.split(':')[0] for i in bill['payment_method'].split('\n')])
                        csv_writer.writerow([i+1, bill['bill_no'], bill['date'], id, qty, discounted_price, double_discounted_price, prod_data['product_gst'], taxable_amount, gst_amount, payment_methods])
                except:
                    failed_bills.append(dict(bill))
                    pass

        if len(failed_bills) > 0:
            with open(f"{folder_selected}/failed_bills_{dt}.csv", 'w', newline='') as file:
                csv_writer = writer(file)
                csv_writer.writerow(failed_bills[0].keys())
                for bill in failed_bills:
                    csv_writer.writerow(bill.values())
            
        messagebox.showinfo("Success!!", "Bill and Sales report exported successfully.", parent=invc)

    def delete_bill(self):
        ids = self.tree.selection()
        if len(ids) == 0:
            return
        sure = messagebox.askyesno("Delete", "Are you sure you want to delete the selected invoice(s)?", parent=invc)
        if sure == True:
            for i in ids:
                cur.execute("DELETE FROM bill WHERE bill_no=?", (self.tree.item(i)["values"][0],))
                self.tree.delete(i)
            db.commit()
            messagebox.showinfo("Success!!", "Invoice(s) deleted successfully.", parent=invc)

    def reprint_bill(self):
        ids = self.tree.selection()
        if len(ids) == 0:
            return
        sure = messagebox.askyesno("Re-Print", "Are you sure you want to re-print the selected invoice(s)?", parent=invc)
        if not sure:
            return
        for i in ids:
            bill_no = self.tree.item(i)["values"][0]
            esc_pos_cmds = []
            if not path.isfile(f"./docs/{bill_no}.txt"):
                messagebox.showerror("Error!!", f"Bill {bill_no} not found.", parent=invc)
                continue
            try:
                with open(f"./docs/{bill_no}.txt", 'rb') as f:
                    for line in f.readlines():
                        esc_pos_cmds.append(line.strip())
                        esc_pos_cmds.append(b'\n')
            except Exception as e:
                messagebox.showerror("Error!!", f"Something went wrong while fetching bill {bill_no}.", parent=invc)
                logging.exception(e)
                continue

            try:
                default_printer_name = win32print.GetDefaultPrinter()
                p = win32print.OpenPrinter(default_printer_name, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
                job = win32print.StartDocPrinter(p, 1, ("test of raw data", None, "RAW"))
                win32print.StartPagePrinter(p)
                for command in esc_pos_cmds:
                    win32print.WritePrinter(p, command)
                win32print.EndPagePrinter(p)
                win32print.ClosePrinter(p)
                messagebox.showinfo("Success!!", f"Bill {bill_no} printed successfully.", parent=invc)
            except Exception as e:
                messagebox.showerror("Error!!", f"Something went wrong while printing bill {bill_no}.", parent=invc)
                logging.exception(e)
                continue

    def save_as_pdf(self):
        messagebox.showinfo("Success!!", "Feature coming soon.", parent=invc)
        return

    def show_context_menu(self, event):
        self.sel = self.tree.identify_row(event.y)

        if len(self.sel) == 0:
            return
        if self.tree.identify_region(event.x, event.y) == "heading":
            return
        menu = Menu(invc, tearoff=0)
        menu.add_command(label="Re-Print", command=self.reprint_bill)
        menu.add_command(label="Save as PDF", command=self.save_as_pdf)
        menu.add_command(label="Delete", command=self.delete_bill)
        menu.post(event.x_root, event.y_root)

    def Exit(self):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=invc)
        if sure == True:
            invc.destroy()
            adm.deiconify()

    def time(self):
        string = strftime("%I:%M:%S %p")
        self.clock.config(text=string)
        self.clock.after(1000, self.time)

    def Logout(self):
        sure = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if sure == True:
            invc.destroy()
            admin_lgn.deiconify()
            admin_lgn.adm_username_entry.delete(0, END)
            admin_lgn.adm_password_entry.delete(0, END)

class ConfigSettings:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Configurations and Settings")

        self.store_details = config_data['store']

        self.label1 = Label(setting)
        self.label1.place(relx=0.0, rely=0.0, width= screen_size[0], height=screen_size[1])
        img = resize_image(settings_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.store_name_entry = Entry(setting)
        self.store_name_entry.place(relx=0.134, rely=0.31, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_name_entry.configure(font=medium_font, relief="flat")
        self.store_name_entry.bind("<Return>", lambda event: self.store_gstin_entry.focus())
        self.store_name_entry.bind("<Down>", lambda event: self.store_gstin_entry.focus())
        self.store_name_entry.insert(0, self.store_details['store_name'])

        self.store_gstin_entry = Entry(setting)
        self.store_gstin_entry.place(relx=0.134, rely=0.441, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_gstin_entry.configure(font=medium_font, relief="flat")
        self.store_gstin_entry.bind("<Return>", lambda event: self.store_address1_entry.focus())
        self.store_gstin_entry.bind("<Down>", lambda event: self.store_address1_entry.focus())
        self.store_gstin_entry.bind("<Up>", lambda event: self.store_name_entry.focus())
        self.store_gstin_entry.insert(0, self.store_details['store_gstin'])

        self.store_address1_entry = Entry(setting)
        self.store_address1_entry.place(relx=0.134, rely=0.572, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_address1_entry.configure(font=medium_font, relief="flat")
        self.store_address1_entry.bind("<Return>", lambda event: self.store_address2_entry.focus())
        self.store_address1_entry.bind("<Down>", lambda event: self.store_address2_entry.focus())
        self.store_address1_entry.bind("<Up>", lambda event: self.store_gstin_entry.focus())
        self.store_address1_entry.insert(0, self.store_details['store_address1'])

        self.store_address2_entry = Entry(setting)
        self.store_address2_entry.place(relx=0.134, rely=0.703, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_address2_entry.configure(font=medium_font, relief="flat")
        self.store_address2_entry.bind("<Return>", lambda event: self.store_phone_entry.focus())
        self.store_address2_entry.bind("<Down>", lambda event: self.store_phone_entry.focus())
        self.store_address2_entry.bind("<Up>", lambda event: self.store_address1_entry.focus())
        self.store_address2_entry.insert(0, self.store_details['store_address2'])

        self.store_phone_entry = Entry(setting)
        self.store_phone_entry.place(relx=0.134, rely=0.834, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_phone_entry.configure(font=medium_font, relief="flat")
        self.store_phone_entry.bind("<Return>", lambda event: self.store_email_entry.focus())
        self.store_phone_entry.bind("<Down>", lambda event: self.store_email_entry.focus())
        self.store_phone_entry.bind("<Up>", lambda event: self.store_address2_entry.focus())
        self.store_phone_entry.insert(0, self.store_details['store_phone'])

        self.store_email_entry = Entry(setting)
        self.store_email_entry.place(relx=0.515, rely=0.31, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_email_entry.configure(font=medium_font, relief="flat")
        self.store_email_entry.bind("<Return>", lambda event: self.store_website_entry.focus())
        self.store_email_entry.bind("<Down>", lambda event: self.store_website_entry.focus())
        self.store_email_entry.bind("<Up>", lambda event: self.store_phone_entry.focus())
        self.store_email_entry.insert(0, self.store_details['store_email'])

        self.store_website_entry = Entry(setting)
        self.store_website_entry.place(relx=0.515, rely=0.441, width=screen_ratio[0]*400, height=screen_ratio[1]*36)
        self.store_website_entry.configure(font=medium_font, relief="flat")
        self.store_website_entry.bind("<Up>", lambda event: self.store_email_entry.focus())
        self.store_website_entry.insert(0, self.store_details['store_website'])

        self.cancel_btn = Button(setting)
        self.cancel_btn.place(relx=0.5275, rely=0.705, width=screen_ratio[0]*140, height=screen_ratio[1]*44)
        self.cancel_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="CANCEL", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.cancel)
        
        self.config_update_btn = Button(setting)
        self.config_update_btn.place(relx=0.683, rely=0.705, width=screen_ratio[0]*140, height=screen_ratio[1]*44)
        self.config_update_btn.configure(background="#FFE59C", borderwidth="0", cursor="hand2", text="UPDATE", activebackground="#FFE59C",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"),
                                command=self.update_config)
        
        for widget in setting.winfo_children():
            if isinstance(widget, Entry):
                widget.bind("<FocusIn>", lambda event, widget=widget: widget.select_range(0, END))


    def cancel(self):
        sure = messagebox.askyesno("Cancel", "Are you sure you want to cancel?", parent=setting)
        if not sure:
            return
        setting.destroy()
        adm.deiconify()

    def update_config(self):
        
        store_name, store_gstin, store_address1, store_address2, = self.store_name_entry.get().strip(), self.store_gstin_entry.get().strip(), self.store_address1_entry.get().strip(), self.store_address2_entry.get().strip()
        store_phone, store_email, store_website = self.store_phone_entry.get().strip(), self.store_email_entry.get().strip(), self.store_website_entry.get().strip()

        required_fields = [store_name, store_gstin, store_address1, store_address2, store_phone]
        if '' in required_fields:
            messagebox.showerror("Error!!", "Please fill all the required fields.", parent=setting)
            return
  
        sure = messagebox.askyesno("Update", "Are you sure you want to update these details?", parent=setting)
        if not sure:
            return
        
        try:
            config_data['store'] = {
                'store_name': store_name,
                'store_gstin': store_gstin,
                'store_address1': store_address1,
                'store_address2': store_address2,
                'store_phone': store_phone,
                'store_email': store_email,
                'store_website': store_website
            }
            with open('config.json', 'w') as f:
                dump(config_data, f, indent=4)
            messagebox.showinfo("Success!!", "Details updated successfully.", parent=setting)
            setting.destroy()
            adm.deiconify()
        except Exception as e:
            messagebox.showerror("Error!!", "Something went wrong while updating details.", parent=setting)
            logging.exception(e)

#########################################################
################### Employee WINDOW #####################
#########################################################

class EmployeeLoginPage:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Employee login")

        self.label1 = Label(emp_lgn)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(emp_login_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.emp_username_entry = Entry(emp_lgn)
        self.emp_username_entry.place(relx=0.378, rely=0.4625, width=screen_ratio[0]*370, height=screen_ratio[1]*45)
        self.emp_username_entry.configure(font=medium_font, relief="flat")
        self.emp_username_entry.bind("<Return>", lambda Event: self.emp_password_entry.focus())
        self.emp_username_entry.bind("<Down>", lambda Event: self.emp_password_entry.focus())

        self.emp_password_entry = Entry(emp_lgn)
        self.emp_password_entry.place(relx=0.378, rely=0.6275, width=screen_ratio[0]*370, height=screen_ratio[1]*45)
        self.emp_password_entry.configure(font=medium_font, relief="flat", show="*")
        self.emp_password_entry.bind("<Return>", self.login)
        self.emp_password_entry.bind("<Up>", lambda Event: self.emp_username_entry.focus())

        self.login_btn = Button(emp_lgn)
        self.login_btn.place(relx=0.441, rely=0.7415, width=180, height=50)
        img = resize_image(login_img, (int(screen_ratio[0]*180), int(screen_ratio[1]*50)))
        self.login_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.login, background="#ffffff")
        self.login_btn.img = img

    def login(self, Event=None):
        global username
        username = self.emp_username_entry.get()
        password = self.emp_password_entry.get()
        password = hashlib.sha256(password.encode()).hexdigest()

        cur.execute("SELECT * FROM employee WHERE emp_username = ? and emp_password = ?", [username, password])
        results = cur.fetchall()

        if results:
            self.emp_username_entry.delete(0, END)
            self.emp_password_entry.delete(0, END)

            emp_lgn.withdraw()
            global biller
            global biller_pg
            biller = Toplevel()
            biller_pg = BillWindow(biller)
            biller_pg.time()
            biller_pg.c_num.focus_force()
            biller.protocol("WM_DELETE_WINDOW", biller_pg_exit)
            biller.mainloop()

        else:
            messagebox.showerror("Error", "Incorrect username or password.", parent=root)
            self.emp_password_entry.delete(0, END)
            self.emp_password_entry.focus()

class BillWindow:
    def __init__(self, top = None):

        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.resizable(0, 0)
        top.title("Billing Window")
        top.bind("<Escape>", self.handle_escape)

        self.__dict__.update(config_data["store"])
        self.__dict__.update(config_data["billing"])
        self.billing_screen = Label(biller)
        self.billing_screen.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(billing_screen_img, screen_size)
        self.billing_screen.configure(image=img)
        self.billing_screen.image = img

        self.logout_btn = Button(biller)
        self.logout_btn.place(relx=0.9, rely=0.0,width=screen_ratio[0]*140, height=screen_ratio[1]*35)
        self.logout_btn.configure(background="#FFC600", borderwidth="0", cursor="hand2", text="Logout", activebackground="#FFC600",
                                font=Font(family="Segoe UI", size=int(0.5*(screen_ratio[0]+screen_ratio[1])*16), weight="bold"), command=self.logout)

        self.is_new_customer = True
        self.c_num = Entry(biller)
        self.c_num.place(relx=0.112, rely=0.112, width=screen_ratio[0]*200, height=screen_ratio[1]*35)
        self.c_num.configure(font=medium_font, borderwidth=2, relief="groove")
        # self.c_num.focus_set()
        self.c_num.bind("<FocusIn>", lambda Event: self.c_num.select_range(0, END))
        self.c_num.bind("<Return>", self.get_customer_details)
        self.c_num.bind("<Down>", self.get_customer_details)

        self.c_name = Entry(biller)
        self.c_name.place(relx=0.112, rely=0.165, width=screen_ratio[0]*240, height=screen_ratio[1]*35)
        self.c_name.configure(font=medium_font, borderwidth=2, relief="groove")
        self.c_name.bind("<FocusIn>", lambda Event: self.c_name.select_range(0, END))
        self.c_name.bind("<Return>", lambda Event: self.c_mail.focus())
        self.c_name.bind("<Down>", lambda Event: self.c_mail.focus())
        self.c_name.bind("<Up>", lambda Event: self.c_num.focus())

        self.c_mail = Entry(biller)
        self.c_mail.place(relx=0.112, rely=0.218, width=screen_ratio[0]*240, height=screen_ratio[1]*35)
        self.c_mail.configure(font=medium_font, borderwidth=2, relief="groove")
        self.c_mail.bind("<FocusIn>", lambda Event: self.c_mail.select_range(0, END))
        self.c_mail.bind("<Return>", lambda Event: self.product_key_entry.focus())
        self.c_mail.bind("<Down>", lambda Event: self.product_key_entry.focus())
        self.c_mail.bind("<Up>", lambda Event: self.c_name.focus())
        
        cur.execute("SELECT * FROM employee WHERE emp_username = ?", [username])
        results = cur.fetchone()
        
        self.bill_no = Label(biller)
        self.bill_no.place(relx=0.42, rely=0.112, width=screen_ratio[0]*200, height=screen_ratio[1]*35)
        self.bill_no.configure(font=medium_font, foreground="#000000", background="#ffffff", text=get_bill_number(), anchor="w",
                                borderwidth=2, relief="groove")
        self.invoice_path = f"./invoice/{self.bill_no['text']}.pdf"
        makedirs(self.invoice_path.rsplit('/', 1)[0], exist_ok=True)
        
        self.e_name = Label(biller)
        self.e_name.place(relx=0.42, rely=0.165, width=screen_ratio[0]*240, height=screen_ratio[1]*35)
        self.e_name.configure(font=medium_font, foreground="#000000", background="#ffffff", text=results[2], anchor="w",
                                borderwidth=2, relief="groove")
        
        self.e_id = Label(biller)
        self.e_id.place(relx=0.42, rely=0.218, width=screen_ratio[0]*240, height=screen_ratio[1]*35)
        self.e_id.configure(font=medium_font, foreground="#000000", background="#ffffff", text=results[0], anchor="w", 
                            borderwidth=2, relief="groove")

        self.clock = Label(biller)
        self.clock.place(relx=0.9, rely=0.05, width=screen_ratio[0]*102, height=screen_ratio[1]*36)
        self.clock.configure(font=small_font, foreground="#000000", background="#ffffff")
    
        self.product_key_entry = Entry(biller)
        self.multi_match_table = ttk.Treeview(biller)
        self.product_key_entry.place(relx=0.112, rely=0.293, width=screen_ratio[0]*400, height=screen_ratio[1]*40)
        self.product_key_entry.configure(font=medium_font, relief="flat")
        self.product_key_entry.bind("<Return>", lambda Event, product_key=self.product_key_entry.get(): self.get_product_details(Event, self.product_key_entry.get()))
        self.product_key_entry.bind("<Down>", self.focus_bill_table)
        self.product_key_entry.bind("<Up>", lambda Event: self.c_mail.focus())

        style.theme_use("clam")
        style.map("payment_options.TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#000000")], selectforeground=[("readonly", "green")], 
                    selectbackground=[("readonly", "#ffffff")], background=[("readonly", "#ffffff")])
        self.payment_mode = StringVar()
        self.payment_mode.set('Cash')
        self.payment_options = ttk.Combobox(biller, textvariable=self.payment_mode, values=['Cash', 'Card', 'UPI/wallet', 'Split'], state='readonly', style="payment_options.TCombobox")
        self.payment_options.place(relx=0.79, rely=0.52, width=screen_ratio[0]*170, height=screen_ratio[1]*40)
        self.payment_options.configure(font=large_font, background="#ffffff", foreground="green", justify="center")
        self.payment_options.bind("<<ComboboxSelected>>", self.set_payment_mode)

        self.payment_bx_lbl1 = Label(biller, text="Amount Paid", font=medium_font, background="#ffffff", foreground="#000000", anchor="w")
        self.payment_bx_lbl1.place(relx=0.733, rely=0.6, width=screen_ratio[0]*140, height=screen_ratio[1]*30)
        self.payment_bx_lbl2 = Label(biller, text="Return Amount", font=medium_font, background="#ffffff", foreground="#000000", anchor="w")
        self.payment_bx_lbl2.place(relx=0.86, rely=0.6, width=screen_ratio[0]*150, height=screen_ratio[1]*30)

        self.amt_paid = Entry(biller)
        self.amt_paid.place(relx=0.735, rely=0.64, width=screen_ratio[0]*140, height=screen_ratio[1]*36)
        self.amt_paid.configure(font=medium_font, borderwidth=2, relief="groove")
        self.amt_paid.bind("<FocusIn>", lambda Event: self.amt_paid.select_range(0, END))
        # self.amt_paid.insert(0, 0)
        self.amt_paid.bind("<Return>", self.calculate_return)

        self.amt_return = Label(biller)
        self.amt_return.place(relx=0.8625, rely=0.64, width=screen_ratio[0]*150, height=screen_ratio[1]*36)
        self.amt_return.configure(font=medium_font, foreground="#000000", background="#ffffff", text='', anchor="w",
                                borderwidth=2, relief="groove")

        self.temp_payment_options1 = ttk.Combobox(biller, text='Cash', values=['Cash', 'Card', 'UPI/wallet'], state='readonly', 
                                                    foreground="green", justify="center", font=medium_font, style="payment_options.TCombobox")
        self.temp_payment_options1.current(0)
        self.temp_payment_options2 = ttk.Combobox(biller, text='UPI/wallet', values=['Card', 'UPI/wallet'], state='readonly', 
                                                    foreground="green", justify="center", font=medium_font, style="payment_options.TCombobox")
        self.temp_payment_options2.current(1)
        
        self.temp_amt_entry1 = Entry(biller, font=medium_font, borderwidth=2, relief="groove")
        self.temp_amt_entry1.bind("<Return>", self.set_mode2_amt)
        self.temp_amt_entry1.bind("FocusIn", lambda Event: self.temp_amt_entry1.select_range(0, END))

        self.temp_amt_entry2 = Entry(biller, font=medium_font, borderwidth=2, relief="groove", state='disabled')
        self.temp_amt_entry2.bind("FocusIn", lambda Event: self.temp_amt_entry2.select_range(0, END))

        self.total_qty = 0
        self.total_qty_label = Label(biller)
        self.total_qty_label.place(relx=0.82, rely=0.14, width=screen_ratio[0]*80, height=screen_ratio[1]*36)
        self.total_qty_label.configure(font=medium_font, foreground="#000000", background="#ffffff", text=self.total_qty, anchor="w",
                                borderwidth=2, relief="groove")
        self.total = 0.0
        self.total_label = Label(biller)
        self.total_label.place(relx=0.82, rely=0.201, width=screen_ratio[0]*200, height=screen_ratio[1]*36)
        self.total_label.configure(font=medium_font, foreground="#000000", background="#ffffff", text=self.total, anchor="w",
                                borderwidth=2, relief="groove")
        
        self.discount_perc = Entry(biller)
        self.discount_perc.place(relx=0.82, rely=0.262, width=screen_ratio[0]*100, height=screen_ratio[1]*36)
        self.discount_perc.configure(font=medium_font, borderwidth=2, relief="groove")
        self.perc_label = Label(self.discount_perc)
        self.perc_label.place(relx=0.8, rely=-0.1, width=screen_ratio[0]*20, height=screen_ratio[1]*36)
        self.perc_label.configure(font=small_font, foreground="#000000", background="#ffffff", text="%", anchor="w",
                                borderwidth=0, relief="flat")
        self.discount_perc.bind("<Return>", self.update_paid)
        self.discount_perc.bind("<FocusIn>", lambda Event: self.discount_perc.select_range(0, END))

        self.discount_amt = Entry(biller)
        self.discount_amt.place(relx=0.894, rely=0.262, width=screen_ratio[0]*100, height=screen_ratio[1]*36)
        self.discount_amt.configure(font=medium_font, borderwidth=2, relief="groove")
        self.amt_label = Label(self.discount_amt)
        self.amt_label.place(relx=0.8, rely=-0.1, width=screen_ratio[0]*20, height=screen_ratio[1]*36)
        self.amt_label.configure(font=small_font, foreground="#000000", background="#ffffff", text="₹", anchor="w",
                                borderwidth=0, relief="flat")
        self.discount_amt.bind("<Return>", self.update_paid)
        self.discount_amt.bind("<FocusIn>", lambda Event: self.discount_amt.select_range(0, END))

        self.net_total_label = Label(biller)
        self.net_total_label.place(relx=0.82, rely=0.323, width=screen_ratio[0]*200, height=screen_ratio[1]*36)
        self.net_total_label.configure(font=medium_font, foreground="#000000", background="#ffffff", text=0.0, anchor="w",
                                borderwidth=2, relief="groove")
        
        self.print_btn = Button(biller)
        self.print_btn.place(relx=0.78, rely=0.87, width=screen_ratio[0]*215, height=screen_ratio[1]*60)
        img = resize_image(print_img, (int(screen_ratio[0]*215), int(screen_ratio[1]*60)))
        self.print_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.print_bill, background="#ffffff")
        self.print_btn.img = img

        self.a4_printer = IntVar(value=0)
        # self.a4_printer_check = Checkbutton(biller)
        # self.a4_printer_check.place(relx=0.765, rely=0.82)
        # self.a4_printer_check.configure(text="A4 Printer", variable=self.a4_printer, onvalue=1, offvalue=0, font=small_font, background="#ffffff",
        #                                 command=self.set_a4_printer)

        self.a5_printer = IntVar(value=0)
        self.a5_printer_check = Checkbutton(biller)
        self.a5_printer_check.place(relx=0.87, rely=0.82)
        self.a5_printer_check.configure(text="A5 Printer", variable=self.a5_printer, onvalue=1, offvalue=0, font=small_font, background="#ffffff",
                                        command=self.set_a5_printer)
        
        self.thermal_printer = IntVar(value=1)
        self.thermal_printer_check = Checkbutton(biller)
        self.thermal_printer_check.place(relx=0.765, rely=0.82)
        self.thermal_printer_check.configure(text="Thermal Printer", variable=self.thermal_printer, onvalue=1, offvalue=0, font=small_font, background="#ffffff",
                                            command=self.set_thermal_printer)

        style.theme_use("clam")
        style.configure("bill_table.Treeview", highlightthickness=0, bd=0, font=small_font) # Modify the font of the body
        style.configure("bill_table.Treeview.Heading", font=("Segoe UI Semibold", int(0.5*(screen_ratio[0]+screen_ratio[1])*16)), background='#FFDF7F', foreground='black', borderwidth=0) # Modify the font of the headings
        style.layout("bill_table.Treeview", [('bill_table.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders
        style.configure("bill_table.Treeview", rowheight=int(screen_ratio[0]*60))

        self.bill_table = ttk.Treeview(biller, style="bill_table.Treeview")
        self.bill_table.place(relx=0.009, rely=0.3615, width=screen_ratio[0]*1025, height=screen_ratio[1]*506)
        self.bill_table["columns"] = ("product_id", "product_description", "product_qty", "product_price", "product_gst", "product_amount")
        self.btree_d = {col: i for i, col in enumerate(self.bill_table["columns"])}
        self.bill_d = {col: i for i, col in enumerate(self.bill_table["columns"])}
        
        self.bill_table["show"] = "headings"
        self.bill_table.column("product_id", width=int(screen_ratio[0]*100), anchor=W)
        self.bill_table.column("product_description", width=int(screen_ratio[0]*260), anchor=W)
        self.bill_table.column("product_qty", width=int(screen_ratio[0]*100), anchor=W)
        self.bill_table.column("product_price", width=int(screen_ratio[0]*100), anchor=W)
        self.bill_table.column("product_gst", width=int(screen_ratio[0]*100), anchor=W)
        self.bill_table.column("product_amount", width=int(screen_ratio[0]*100), anchor=W)

        self.bill_table.heading("product_id", text="Product ID", anchor=W)
        self.bill_table.heading("product_description", text="Description", anchor=W)
        self.bill_table.heading("product_qty", text="Quantity", anchor=W)
        self.bill_table.heading("product_price", text="Price", anchor=W)
        self.bill_table.heading("product_gst", text="GST%", anchor=W)
        self.bill_table.heading("product_amount", text="Amount", anchor=W)

        self.bill_table.bind("<Button-3>", self.show_context_menu)
        self.bill_table.bind("<Delete>", self.delete_product_details)
        self.bill_table.bind("<FocusOut>", self.clear_selection)
        self.bill_table.bind("<Up>", lambda Event: self.product_key_entry.focus() if len(self.bill_table.selection()) == 1 and self.bill_table.selection()[0] == self.bill_table.get_children()[0] else None)

        self.multi_match_table = ttk.Treeview(biller)
        self.multi_match_table["columns"] = ("product_id", "product", "brand", "color", "size", "mrp")
        self.multi_match_table["show"] = "headings"
        self.multi_match_table.heading("product_id", text="Product ID")
        self.multi_match_table.heading("product", text="Product")
        self.multi_match_table.heading("brand", text="Brand")
        self.multi_match_table.heading("color", text="Color")
        self.multi_match_table.heading("size", text="Size")
        self.multi_match_table.heading("mrp", text="MRP")
        
        self.multi_match_table.column("product_id", width=int(screen_ratio[0]*90), anchor="center")
        self.multi_match_table.column("product", width=int(screen_ratio[0]*200), anchor="center")
        self.multi_match_table.column("brand", width=int(screen_ratio[0]*100), anchor="center")
        self.multi_match_table.column("color", width=int(screen_ratio[0]*60), anchor="center")
        self.multi_match_table.column("size", width=int(screen_ratio[0]*60), anchor="center")
        self.multi_match_table.column("mrp", width=int(screen_ratio[0]*60), anchor="center")

        self.updates_label = Label(biller)
        self.updates_label.configure(font=small_font, foreground="#000000", background="#A6A6A6", anchor="w")

            
    def logout(self):

        sure = messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=biller)
        if sure == True:
            biller.destroy()
            emp_lgn.deiconify()
            emp_login_pg.emp_username_entry.delete(0, END)
            emp_login_pg.emp_password_entry.delete(0, END)
    
    def place_updates_label(self, text):
        self.updates_label.place(relx=0.33, rely=0.049, width=screen_ratio[0]*480, height=screen_ratio[1]*34)
        self.updates_label.configure(text=text, anchor=CENTER, font=small_font)
        self.billing_screen.update()

    def set_mode2_amt(self, Event):
        if self.temp_amt_entry1.get() in ["", "0"]:
            return
        self.temp_amt_entry2.configure(state="normal")
        self.temp_amt_entry2.delete(0, END)
        self.temp_amt_entry2.insert(0, str(round(float(self.net_total_label["text"]) - float(self.temp_amt_entry1.get()), 2)))
        self.temp_amt_entry2.configure(state="readonly")

    def set_payment_mode(self, Event):
        if 'split' in self.payment_mode.get().lower():
            if self.amt_paid.winfo_ismapped():
                self.amt_paid.place_forget()
                self.amt_return.place_forget()
            
            self.payment_bx_lbl1.configure(text="Mode 1", anchor="w")
            self.temp_payment_options1.place(relx=0.735, rely=0.64, width=screen_ratio[0]*140, height=screen_ratio[1]*36)
            self.temp_amt_entry1.place(relx=0.735, rely=0.7, width=screen_ratio[0]*140, height=screen_ratio[1]*36)

            self.payment_bx_lbl2.configure(text="Mode 2", anchor="w")
            self.temp_payment_options2.place(relx=0.8625, rely=0.64, width=screen_ratio[0]*140, height=screen_ratio[1]*36)
            self.temp_amt_entry2.place(relx=0.8625, rely=0.7, width=screen_ratio[0]*140, height=screen_ratio[1]*36)

        else:
            for widget in [self.temp_payment_options1, self.temp_amt_entry1, self.temp_payment_options2, self.temp_amt_entry2]:
                if widget.winfo_ismapped():
                    widget.place_forget()

            self.payment_bx_lbl1.configure(text="Amount Paid", anchor="w")
            self.payment_bx_lbl2.configure(text="Return Amount", anchor="w")
            self.amt_paid.place(relx=0.735, rely=0.64, width=screen_ratio[0]*140, height=screen_ratio[1]*36)
            self.amt_return.place(relx=0.8625, rely=0.64, width=screen_ratio[0]*150, height=screen_ratio[1]*36)

            if 'upi' in self.payment_mode.get().lower() or 'card' in self.payment_mode.get().lower():
                self.amt_paid.delete(0, END)
                self.amt_paid.insert(0, round(float(self.net_total_label["text"]), 2))
                self.amt_paid.configure(state="disabled")
                self.amt_return.configure(text=0.0, state="disabled")
            elif 'cash' in self.payment_mode.get().lower():
                self.amt_paid.configure(state="normal")
                self.amt_paid.delete(0, END)
                self.amt_paid.focus()

    def get_customer_details(self, Event):

        if not valid_phone(self.c_num.get()):
            messagebox.showinfo("Info", "Invalid phone number!", parent=biller)
            # self.c_num.delete(0, END)
            self.c_num.focus()
            return
        
        results = cur.execute(f"SELECT * FROM customer WHERE phone = {self.c_num.get()}").fetchone()

        self.c_name.delete(0, END)
        self.c_mail.delete(0, END)

        if results:
            self.c_name.insert(0, results[1])
            self.c_mail.insert(0, results[2])
            self.product_key_entry.focus()
            self.is_new_customer = False  
        else:
            self.is_new_customer = True
            self.c_name.focus()      

    def calculate_return(self, Event):

        if self.amt_paid.get() in ["", "0", "0.0", "0.00"]:
            return
        try:
            float(self.amt_paid.get())
        except ValueError:
            messagebox.showinfo("Info", "Invalid amount!", parent=biller)
            self.amt_paid.delete(0, END)
            self.amt_paid.insert(0, 0)
            return
        
        if float(self.amt_paid.get()) < self.net_total:
            messagebox.showinfo("Info", "Invalid amount!", parent=biller)
            self.amt_paid.delete(0, END)
            self.amt_paid.insert(0, 0)
            self.amt_return.configure(text=0.0, state="disabled")
            return
        
        self.amt_return.configure(text=round(float(self.amt_paid.get()) - self.net_total, 2), state="disabled")

    def update_paid(self, Event):

        dis_amt = self.discount_amt.get() if self.discount_amt.get() else 0
        dis_perc = self.discount_perc.get() if self.discount_perc.get() else 0

        try:
            float(dis_amt)
        except ValueError:
            messagebox.showinfo("Info", "Invalid discount amount!", parent=biller)
            self.discount_amt.delete(0, END)
            self.discount_amt.focus()
            return
        
        try: 
            float(dis_perc)
        except ValueError:
            messagebox.showinfo("Info", "Invalid discount percentage!", parent=biller)
            self.discount_perc.delete(0, END)
            self.discount_perc.focus()
            return
        
        if float(dis_amt) < 0 or float(dis_amt) > self.total:
            messagebox.showinfo("Info", "Invalid discount amount!", parent=biller)
            self.discount_amt.delete(0, END)
            self.discount_amt.focus()
            return


        if float(dis_perc) < 0 or float(dis_perc) > 100:
            messagebox.showinfo("Info", "Invalid discount percentage!", parent=biller)
            self.discount_perc.delete(0, END)
            self.discount_perc.focus()
            return

        self.net_total = self.total - float(dis_amt) - (self.total * (float(dis_perc)/100))
        if self.net_total < 0:
            messagebox.showinfo("Info", "Invalid discount amount!", parent=biller)
            self.discount_amt.delete(0, END)
            self.discount_perc.delete(0, END)
            self.discount_perc.focus()
            return
        self.net_total_label.configure(text=round(self.net_total, 2))
        if self.amt_paid.winfo_ismapped():
            if self.payment_mode.get().lower() == 'cash':
                self.calculate_return("<Return>")
            elif 'upi' in self.payment_mode.get().lower() or 'card' in self.payment_mode.get().lower():
                self.amt_paid.configure(state="normal")
                self.amt_paid.delete(0, END)
                self.amt_paid.insert(0, round(self.net_total, 2))
                self.amt_paid.configure(state="disabled")
                self.amt_return.configure(text=0.0, state="disabled")
        
        if self.temp_amt_entry1.winfo_ismapped():
            self.set_mode2_amt("<Return>")

        # self.amt_paid.focus_set()
        if Event.widget == self.discount_perc:
            self.discount_amt.focus_set()
        if Event.widget == self.discount_amt:
            self.amt_paid.focus_set()

    def generate_pdf_a5(self):
        pass

    def generate_pdf_a4(self):
        messagebox.showinfo("Info", "A4 printer is not connected!", parent=biller)
        return

    def generate_thermal_bill(self):

        self.place_updates_label("Please wait: Updating database!!")
        try:
            table_data = []
            for item in self.bill_table.get_children():
                p_id = self.bill_table.item(item, 'values')[self.btree_d['product_id']]
                p_desc = f"{self.bill_table.item(item, 'values')[self.btree_d['product_description']]}"
                p_desc = p_desc.replace('\n', '-')
                p_qty = int(self.bill_table.item(item, 'values')[self.btree_d['product_qty']])
                p_price = float(self.bill_table.item(item, 'values')[self.btree_d['product_price']])
                p_gst = float(self.bill_table.item(item, 'values')[self.btree_d['product_gst']])
                p_amt = float(self.bill_table.item(item, 'values')[self.btree_d['product_amount']])
                table_data.append([p_id, p_desc, p_qty, p_price, p_amt, p_gst])

            bill_no = self.bill_no.cget('text')
            emp_id = self.e_id.cget('text')
            total_discount = self.total - self.net_total
            payment_details = ['-'.join([self.payment_mode.get(), str(self.net_total)])] if self.amt_paid.winfo_ismapped() else ['-'.join([self.temp_payment_options1.get(), str(self.temp_amt_entry1.get())]), '-'.join([self.temp_payment_options2.get(), str(self.temp_amt_entry2.get())])]

            esc_pos_generator = EscPosCmdGenerator(bill_no=bill_no, emp_id=emp_id, table_data=table_data, discount=total_discount, payment_details=payment_details)
            esc_pos_cmds = esc_pos_generator.generate_esc_pos_cmds()

            makedirs('./docs', exist_ok=True)
            with open(f"./docs/{bill_no}.txt", 'wb') as f:
                for command in esc_pos_cmds:
                    f.write(command)
                    
            default_printer_name = win32print.GetDefaultPrinter()

            p = win32print.OpenPrinter(default_printer_name, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})

            job = win32print.StartDocPrinter(p, 1, ("test of raw data", None, "RAW"))
            win32print.StartPagePrinter(p)
            for command in esc_pos_cmds:
                win32print.WritePrinter(p, command)
            win32print.EndPagePrinter(p)
            win32print.ClosePrinter(p)
            self.updates_label.place_forget()
            return True

        except Exception as e:
            logging.exception(e)
            messagebox.showinfo("Info", "Something went wrong while generating bill!", parent=biller)
            self.updates_label.place_forget()
            return False
        
    def update_database(self, bill_reloaded=False):

        self.place_updates_label("Please wait: Updating database!!")
        try:
            db = sqlite3.connect("Database/store.db")
            cur = db.cursor() 
            bill_details_str = ''

            for i, item in enumerate(self.bill_table.get_children()):
                # bill_details_dict[self.bill_table.item(item, 'values')[self.btree_d['product_id']]] = self.bill_table.item(item, 'values')[self.btree_d['product_qty']]
                bill_details_str += f"ID-{self.bill_table.item(item, 'values')[self.btree_d['product_id']]}: {self.bill_table.item(item, 'values')[self.btree_d['product_qty']]}, "
    
                cur.execute(f"UPDATE inventory SET product_stock = product_stock - {int(self.bill_table.item(item, 'values')[self.btree_d['product_qty']])} WHERE product_id = '{self.bill_table.item(item, 'values')[self.btree_d['product_id']]}'")
            
            if not len(cur.execute(f"SELECT * FROM customer WHERE phone = {self.c_num.get().strip()}").fetchall()) > 0:
                cur.execute(f"INSERT INTO customer VALUES('{self.c_num.get().strip()}', '{self.c_name.get().strip()}', '{self.c_mail.get().strip()}')")
            else:
                cur.execute(f"UPDATE customer SET name = '{self.c_name.get().strip()}', mail = '{self.c_mail.get().strip()}' WHERE phone = {self.c_num.get().strip()}")

            self.payment_status = "Success"
            bill_details_str = bill_details_str[:-2]

            if self.amt_paid.winfo_ismapped():
                payment_details_str = f"{self.payment_mode.get()}: {round(float(self.net_total),2)}"
            else:
                payment_details_str = f"{self.temp_payment_options1.get()}: {self.temp_amt_entry1.get()}\n{self.temp_payment_options2.get()}: {self.temp_amt_entry2.get()}"
            
            c_name, c_mail = self.c_name.get().strip(), self.c_mail.get().strip()
            if len(cur.execute(f"SELECT * FROM bill WHERE bill_no = '{self.bill_no.cget('text')}'").fetchall()) == 0:
                cur.execute(f"INSERT INTO bill (bill_no, date, e_id, c_num, c_name, c_mail, bill_details, total, net_total, payment_method, payment_status) \
                            VALUES('{self.bill_no.cget('text')}', '{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}', '{self.e_id.cget('text')}', \
                            '{self.c_num.get().strip()}', '{c_name}', '{c_mail}', '{bill_details_str}', '{self.total}', '{round(float(self.net_total),2)}', \
                            '{payment_details_str}', '{self.payment_status}')")
            else:
                cur.execute(f"UPDATE bill SET date = '{datetime.now().strftime('%d-%m-%Y')}', e_id = '{self.e_id.cget('text')}', c_num = '{self.c_num.get().strip()}', c_name = '{c_name}', \
                            c_mail = '{c_mail}', bill_details = '{bill_details_str}', total = '{self.total}', net_total = '{round(float(self.net_total),2)}', \
                            payment_method = '{payment_details_str}', payment_status = '{self.payment_status}' WHERE bill_no = '{self.bill_no.cget('text')}'")
            db.commit()
            self.updates_label.place_forget()
            return True

        except Exception as e:
            db.rollback()
            logging.exception(e)
            messagebox.showinfo("Info", "Something went wrong while updating database!", parent=biller)
            self.updates_label.place_forget()
            return False
        
    def clear_bill(self):

        self.c_num.delete(0, END)
        self.c_name.delete(0, END)
        self.c_mail.delete(0, END)
        self.is_new_customer = False

        self.bill_table.delete(*self.bill_table.get_children())

        self.total, self.total_qty, self.net_total = 0.0, 0, 0.0
        self.total_label.configure(text=self.total)
        self.total_qty_label.configure(text=self.total_qty)
        self.net_total_label.configure(text=self.net_total)

        self.discount_amt.delete(0, END)
        self.discount_perc.delete(0, END) 

        self.amt_paid.delete(0, END)
        self.amt_return.configure(text=0.0, state="disabled")
        self.payment_mode.set("Cash")
        self.set_payment_mode("<Return>")

        self.set_thermal_printer()
        
        self.bill_no.configure(text=get_bill_number())
        self.c_num.focus()

    def print_bill(self):
        
        # when the bill is reloaded make sure to remove the previous bill
        if not self.total:
            messagebox.showinfo("Info", "No items in the bill!", parent=biller)
            self.product_key_entry.focus()
            return False
        
        if not valid_phone(self.c_num.get()):
            messagebox.showinfo("Info", "Invalid phone number!", parent=biller)
            self.c_num.focus()
            return False
        
        db_updated_successfully = self.update_database()

        if self.thermal_printer.get() == 1:
            printed_successfully = self.generate_thermal_bill()
        elif self.a5_printer.get() == 1:
            self.generate_pdf_a5()
        elif self.a4_printer.get() == 1:
            self.generate_pdf_a4()
        else:
            messagebox.showinfo("Info", "Please select a printer!", parent=biller)
            return False
        
        if db_updated_successfully and printed_successfully:
            self.clear_bill()
            self.product_key_entry.focus()
            return True
        else:
            return False
        
    def set_a4_printer(self):
        # self.thermal_printer_check.deselect()
        # self.thermal_printer.set(0)
        self.a5_printer_check.deselect()
        self.a5_printer.set(0)

    def set_thermal_printer(self):
        # self.a4_printer_check.deselect()
        # self.a4_printer.set(0)
        self.a5_printer_check.deselect()
        self.a5_printer.set(0)

    def set_a5_printer(self):
        # self.a4_printer_check.deselect()
        # self.a4_printer.set(0)
        self.thermal_printer_check.deselect()
        self.thermal_printer.set(0)
            

    def handle_escape(self, Event):
        self.clear_selection(Event)
        if self.multi_match_table.winfo_ismapped():
            self.multi_match_table.delete(*self.multi_match_table.get_children())
            self.multi_match_table.place_forget()

    def show_context_menu(self, Event):
        
        item_id = self.bill_table.identify_row(Event.y)
        if item_id:
            # check if you are clicking on the sleected row only
            if item_id not in self.bill_table.selection():
                return
            # open context menu with the following options: Edit, Delete
            self.context_menu = Menu(self.bill_table, tearoff=0)
            self.context_menu.add_command(label="Edit", command=lambda: self.edit_product_details(item_id))
            self.context_menu.add_command(label="Delete", command=lambda Event=Event: self.delete_product_details(Event=Event))
            self.context_menu.tk_popup(Event.x_root, Event.y_root)

    def edit_product_details(self, item_id):
        pass

    def delete_product_details(self, Event=None):
        item_ids = sorted(self.bill_table.selection())

        sure = messagebox.askyesno("Confirm", "Are you sure you want to delete the selected item(s)?", parent=biller)
        if not sure:
            return
        for item_id in item_ids:
            self.total -= float(self.bill_table.item(item_id, "values")[self.bill_d['product_amount']])
            self.total_label.configure(text=self.total)
            self.total_qty -= int(self.bill_table.item(item_id, "values")[self.bill_d['product_qty']])
            self.total_qty_label.configure(text=self.total_qty)
            self.update_paid(Event=Event)
            self.bill_table.delete(item_id)

            self.focus_bill_table(Event=None)

    def focus_bill_table(self, Event):
        if self.multi_match_table.winfo_ismapped():
            self.multi_match_table.focus_set()
            self.multi_match_table.focus(self.multi_match_table.get_children()[0])
            self.multi_match_table.selection_set(self.multi_match_table.get_children()[0])
        elif len(self.bill_table.get_children()) > 0:
            self.bill_table.focus_set()
            self.bill_table.focus(self.bill_table.get_children()[0])
            self.bill_table.selection_set(self.bill_table.get_children()[0])

        else:
            self.product_key_entry.focus()

    def clear_selection(self, Event):
        if self.bill_table.selection():
            self.bill_table.selection_remove(self.bill_table.selection())

    def update_bill_table(self, Event):
        item_id = None
        for item in self.bill_table.get_children():
            if str(self.bill_table.item(item, "values")[self.bill_d['product_id']]) == str(self.product_details["product_id"]):
                item_id = item
                break
        if item_id:
            current_qty = int(self.bill_table.item(item_id, "values")[self.bill_d['product_qty']])
            new_qty = current_qty + 1
            self.bill_table.set(item_id, column="product_qty", value=new_qty)
            self.bill_table.set(item_id, column="product_amount", value=new_qty * self.product_details["product_amount"])
            self.total += self.product_details["product_price"]
        else:
            # Product ID doesn't exist, append a new row
            item_id = self.bill_table.insert("", "end", values=(self.product_details["product_id"], self.product_details["product_description"], self.product_details["product_qty"], 
                                                                self.product_details["product_price"], self.product_details["product_gst"], self.product_details["product_price"]))
        
            self.bill_table.see(item_id)
            self.total += self.product_details["product_price"]

            # self.bill_table.selection_set(item_id)
            # self.bill_table.focus(item_id)
        self.total_label.configure(text=self.total)
        self.total_qty += 1
        self.total_qty_label.configure(text=self.total_qty)
        self.net_total = self.total
        self.net_total_label.configure(text=self.total)
        self.update_paid(Event=Event)
        # self.amount_label.configure(text=self.total)
        

    def get_product_details(self, Event, product_key=None):

        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        if self.multi_match_table.winfo_ismapped():
            self.multi_match_table.delete(*self.multi_match_table.get_children())
            self.multi_match_table.place_forget()

        if product_key in ["", None]:
            return
        
        if match(barcode_patteren, str(product_key)):
            product_key = int(product_key)
            
            cur.execute(f"SELECT * FROM inventory WHERE product_id = '{product_key}'")
            results = cur.fetchall()

            if len(results) == 0:
                messagebox.showinfo("Info", "Product not found!", parent=biller)
                self.product_key_entry.delete(0, END)
                self.product_key_entry.focus()
                return
            
            prod_description = f"{format_name(results[0]['product_brand'])} {format_name(results[0]['product_name'])}\n{format_name(results[0]['product_color'])}/{format_name(results[0]['product_size'])}"
            prod_mrp, prod_discounted_price = results[0]['product_mrp'], results[0]['product_discounted_price']
            if prod_discounted_price in ["", None]:
                prod_discount = prod_mrp
            self.product_details = {'product_id': results[0]['product_id'], 'product_description': prod_description, 'product_qty': 1, 'product_price': prod_discounted_price, 'product_gst': results[0]['product_gst'], 'product_amount': prod_discounted_price}
            self.update_bill_table(Event=Event)
            self.product_key_entry.delete(0, END)
            self.product_key_entry.focus()
            
        else:

            cur.execute(f"SELECT * FROM inventory WHERE product_name like '{product_key}%' OR product_brand like '{product_key}%'")
            results = cur.fetchall()

            if len(results) == 0:
                messagebox.showinfo("Info", "Product not found!", parent=biller)
                self.product_key_entry.delete(0, END)
                self.product_key_entry.focus()
                return
            
            if len(results) == 1:
                self.get_product_details(Event=Event, product_key=str(results[0]['product_id']).zfill(barcode_max_len))
                return

            self.multi_match_table.place(relx=0.112, rely=0.339, width=screen_ratio[0]*800, height=screen_ratio[1]*200)
            for i in results:
                prod_mrp, prod_discounted_price = i['product_mrp'], i['product_discounted_price']
                if prod_discounted_price in ["", None]:
                    prod_discounted_price = prod_mrp
                
                self.multi_match_table.insert("", "end", values=[i['product_id'], i['product_name'], i['product_brand'], i['product_color'], i['product_size'], prod_discounted_price])

            # self.multi_match_table.bind("<Button-1>", lambda Event: self.get_product_details(event=None, product_key="recur"+self.multi_match_table.item(self.multi_match_table.identify_row(Event.y), "values")[0].strip()))
            self.multi_match_table.bind("<Button-1>", self.on_multi_match_select)
            self.multi_match_table.bind("<Return>", self.on_multi_match_select)

    def on_multi_match_select(self, Event):
        selected_item = self.multi_match_table.item(self.multi_match_table.focus(), "values")
        if selected_item:
            self.get_product_details(Event=Event, product_key=str(selected_item[0]).zfill(barcode_max_len))

    def time(self):
        string = strftime("%H:%M:%S %p")
        self.clock.config(text=string)
        self.clock.after(1000, self.time)

      

#########################################################
##################### MAIN WINDOW #######################
#########################################################

class MainScreen:
    def __init__(self, top=None):
        top.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        top.title("Billing System")
        top.resizable(0, 0)
        top.protocol("WM_DELETE_WINDOW", self.root_exit)

        self.label1 = Label(root)
        self.label1.place(relx=0.0, rely=0.0, width=screen_size[0], height=screen_size[1])
        img = resize_image(main_img, screen_size)
        self.label1.configure(image=img)
        self.label1.image = img

        self.admin_login_btn = Button(root)
        self.admin_login_btn.place(relx=0.557, rely=0.565, width=int(screen_ratio[0]*170), height=int(screen_ratio[1]*150))
        img = resize_image(admin_login_icon_img, (int(screen_ratio[0]*170), int(screen_ratio[1]*150)))
        self.admin_login_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.adm, background="#ffffff")
        self.admin_login_btn.img = img

        self.emp_login_btn = Button(root)
        self.emp_login_btn.place(relx=0.76, rely=0.565, width=screen_ratio[0]*170, height=screen_ratio[1]*150)
        img = resize_image(emp_login_icon_img, (int(screen_ratio[0]*170), int(screen_ratio[1]*150)))
        self.emp_login_btn.configure(image=img, borderwidth="0", cursor="hand2", command=self.emp, background="#ffffff")
        self.emp_login_btn.img = img

    def root_exit(self):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=root)
        if sure == True:
            root.destroy()
    
    def login_exits(self, window):
        sure = messagebox.askyesno("Exit","Are you sure you want to exit?", parent=window)
        if sure == True:
            window.destroy()
            root.deiconify()

    def adm(self):
        root.withdraw()
        global admin_lgn
        global admin_login_pg
        admin_lgn = Toplevel()
        admin_login_pg = AdminLoginPage(admin_lgn)
        admin_login_pg.adm_username_entry.focus_set()
        admin_lgn.protocol("WM_DELETE_WINDOW", lambda: self.login_exits(admin_lgn))
        admin_lgn.mainloop()


    def emp(self):
        root.withdraw()
        global emp_lgn
        global emp_login_pg
        emp_lgn = Toplevel()
        emp_login_pg = EmployeeLoginPage(emp_lgn)
        emp_login_pg.emp_username_entry.focus()
        emp_lgn.protocol("WM_DELETE_WINDOW", lambda: self.login_exits(emp_lgn))
        emp_lgn.mainloop()


# check if is root window
if __name__ == "__main__":
    global main_pg
    main_pg = MainScreen(root)
    root.mainloop()
# if __name__ == "__main__":
    # admin_login_pg = AdminLoginPage(root)
    # admin_login_pg.adm_username_entry.focus()
    # root.mainloop()
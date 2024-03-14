# BilledIn
BilledIn is a simple billing system (Desktop application) for small businesses. It is designed to be easy to use and easy to understand. It is completely written in Python and uses the Tkinter library for the GUI and SQLite for the database.

## Features
- **Main Screen**
    - The main screen of the application is where the user will get option to login as admin or as an employee.
    ![Main Screen](images/main_pg.png)

- **Employee Login**
    - The employee can login using their employee id and password, One standout feature of the application is that the employee can only login if the admin has created an account for them and also the password is encrypted, ensuring the security of the employee's account.
    ![Employee Login](images/emp_lgn.png)

- **Admin mode**
    - The admin can login using the default username and password, which is "admin01" and "admin01" respectively.
    ![Admin Login](images/admn_pg.png)
    - List of things the admin can do:
        - Inventory Management
        - Employee Management
        - Invoice Management
        - Settings

- **Inventory Management**
    - The admin can search, add, update, delete and genrate barcode stickers for the products.
    ![Inventory Management](images/inv_mngmnt.png)
    - Update Product
    ![Update Product](images/prod_updt.png)

- **Employee Management**
    - The admin can search, add, update and delete the employee's account.
    ![Employee Management](images/emp_mngmnt.png)
    - Add Employee
    ![Add Employee](images/add_emp.png)

- **Invoice Management**
    - The admin can search invoices and generate bills and sales reports.
    ![Invoice Management](images/invc_mngmnt.png)
    - Sales Report
    ![Sales Report](images/sales_report.png)

- **Billing Screen**
    - The employee can generate bills for the customers.
    ![Billing Screen](images/blng_scrn.png)

- **Barcode Sticker**
    - The admin can generate barcode stickers for the products.
    ![Barcode Sticker](images/prod_stckr.png)

## Installation
- Clone the repository
    ```bash
    git clone https://github.com/mahadev0811/BilledIn.git
    ```

- Install the required packages
    ```bash
    pip install -r requirements.txt
    ```

- Run the application
    ```bash
    python app.py
    ```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



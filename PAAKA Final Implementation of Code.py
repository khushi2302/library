#Importing all required dependencies
import psycopg2 as pg
from psycopg2 import sql
import csv
import bcrypt
from getpass import getpass
from datetime import datetime, timedelta

#To connect to PostgreSQl
def open_db():
    con = pg.connect(
        host="localhost",
        port='5432',
        database="Library_DBMS",
        user="postgres",
        password="12345")
    cur = con.cursor()
    return con, cur

con,cur = open_db()

file = open('Library_data.csv', encoding='latin1')
contents = csv.reader(file)

drop_reference = "DROP TABLE IF EXISTS Reference;"

create_reference = """
CREATE TABLE Reference
                  (
                    Category TEXT,
                    Access_No TEXT Primary Key,
                    Title TEXT,
                    Authors TEXT,
                    Asset_Code TEXT,
                    Department TEXT,
                    Subject TEXT,
                    Edition TEXT,
                    Date_Year TEXT,
                    Call_No TEXT,
                    Publisher TEXT,
                    Place TEXT,
                    ISBN TEXT,
                    Price TEXT,
                    Bill_Date TEXT,
                    Vendor TEXT,
                    Pages TEXT
                  );
"""

cur.execute(drop_reference)
cur.execute(create_reference)
con.commit()

insert_records = """INSERT INTO 
                    Reference(Category, Access_No, Title, Authors, Asset_Code, Department, Subject, Edition, Date_Year, Call_No, Publisher, Place, ISBN, Price, Bill_Date, Vendor, Pages) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                  """

cur.executemany(insert_records, contents)
con.commit()

create_books = """CREATE TABLE IF NOT EXISTS Books
(ISBN TEXT PRIMARY KEY,
Title TEXT,
Author TEXT,
Publisher TEXT,
Subject TEXT,
Edition TEXT,
Year_of_Publication TEXT,
Pages TEXT);"""

cur.execute(create_books)
con.commit()

#Creating a table to store the records of all books that have been issued
create_issued = """CREATE TABLE IF NOT EXISTS Issued_Records
(Member_Id TEXT PRIMARY KEY,
Member_Name TEXT,
Book_Issued TEXT,
Issued_Date TEXT,
Return_Date TEXT,
Status TEXT);"""

cur.execute(create_issued)
con.commit()

#Creating a users table to store all data related to users of the library
create_users = """CREATE TABLE IF NOT EXISTS users (
    USN TEXT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);"""

cur.execute(create_users)
con.commit()

#Creating a remarks table to track whether books have been returned on time or not
create_remarks = """
CREATE TABLE IF NOT EXISTS remarks (
    Remark_ID SERIAL PRIMARY KEY,
    User_ID TEXT,
    ISBN VARCHAR(30),
    Due_Date DATE,
    Return_Date DATE,
    Fine DECIMAL(10, 2),
    FOREIGN KEY (User_ID) REFERENCES users(USN),
    FOREIGN KEY (ISBN) REFERENCES books(ISBN)
    ON DELETE CASCADE
);
"""

cur.execute(create_remarks)
con.commit()

#Creating a feedback table to collect and store remarks related to books from the users
create_feedback = """
CREATE TABLE IF NOT EXISTS feedback (
    Feedback_ID SERIAL PRIMARY KEY,
    User_ID TEXT,
    ISBN VARCHAR(30),
    Rating INTEGER CHECK (Rating >= 1 AND Rating <= 5),
    Comment TEXT,
    FOREIGN KEY (User_ID) REFERENCES users(USN),
    FOREIGN KEY (ISBN) REFERENCES books(ISBN)
    ON DELETE CASCADE
);
"""

cur.execute(create_feedback)
con.commit()

#Creating a member publications table to store publications sent in by library members 
create_publications = """CREATE TABLE IF NOT EXISTS Member_Publications
(Member_Id TEXT PRIMARY KEY,
Author_Name TEXT,
Publication_Title TEXT,
Subject TEXT);"""

cur.execute(create_publications)
con.commit()

insert_books = """
INSERT INTO Books(ISBN, Title, Author, Publisher, Subject, Edition, Year_of_Publication, Pages)
SELECT DISTINCT ON (ISBN) ISBN, Title, Authors, Publisher, Subject, Edition, Date_Year, Pages
FROM Reference
WHERE NOT EXISTS (SELECT * FROM Books);
"""

cur.execute(insert_books)
con.commit()

#Inserting data into feedback table
insert_feedback = """
    INSERT INTO feedback (ISBN)
    SELECT ISBN FROM Books;
    """

cur.execute(insert_feedback)
con.commit()

#Creating view to show all books that have been issued
drop_view = """DROP VIEW IF EXISTS Issued_Books"""
create_view = """CREATE VIEW Issued_Books AS
SELECT DISTINCT ON (ISBN) ISBN, Issued_Records.Book_Issued, Author 
FROM Issued_Records, Books
WHERE Issued_Records.Book_Issued LIKE Books.Title"""

cur.execute(drop_view)
cur.execute(create_view)
con.commit()

#Search for a book using title, Author or Publisher
def search_for_a_book(con, cur):
    while True:
        print("\nChoose an option:")
        print("1. Search Book by Title.")
        print("2. Search Book by Authors Name.")
        print("3. Search Book by Publisher Name.")
        print("4. Search Book by Subject Name.")
        print("5. Quit")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            search_query_input_for_title = input("Enter the Title of the book:")
            create_search_query_title = f"""
            SELECT ISBN, Title
            FROM Books
            WHERE Title ILIKE '{search_query_input_for_title}%';
            """
            print("Search term:", search_query_input_for_title)
            cur.execute(create_search_query_title)
            results = cur.fetchall()
            for row in results:
                print(row)

        elif choice == "2":
            search_query_input_for_author = input("Enter the Author of the book:")
            create_search_query_author = f"""
            SELECT ISBN, Author
            FROM Books
            WHERE Author ILIKE '{search_query_input_for_author}%';
            """
            print("Search term:", search_query_input_for_author)
            cur.execute(create_search_query_author)
            results = cur.fetchall()
            for row in results:
                print(row)

        elif choice == "3":
            search_query_input_for_publisher = input("Enter the Publisher of the book:")
            create_search_query_publisher = f"""
            SELECT ISBN, Publisher
            FROM Books
            WHERE Publisher ILIKE '{search_query_input_for_publisher}%';
            """
            print("Search term:", search_query_input_for_publisher)
            cur.execute(create_search_query_publisher)
            results = cur.fetchall()
            for row in results:
                print(row)

        elif choice == "4":
            search_query_input_for_subject = input("Enter the Subject name:")
            create_search_query_subject = f"""
            SELECT
                ISBN, Subject
            FROM
                Books
            WHERE
                Subject ILIKE '{search_query_input_for_subject}%';
            """
            print("Search term:", search_query_input_for_subject)
            cur.execute(create_search_query_subject)

            results = cur.fetchall()
            for row in results:
                print(row)

        elif choice == "5":
            break

        else:
            print("Invalid choice. Please try again.")


#Login options to create a login or update an exisitng login
def create_user(con, usn, username, password, email):
    """
    Create a new user account.
    """
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor = con.cursor()
        cursor.execute(sql.SQL('''
            INSERT INTO users (usn, username, password, email)
            VALUES (%s, %s, %s, %s)
        '''), (usn, username, hashed_password.decode('utf-8'), email))
        con.commit()
        print("User created successfully!")
        return usn 
    except pg.IntegrityError as e:
        print(f"Error: {e}")
        con.rollback()


def login_user(con, username, password):
    """
    Log in to the system.
    """
    cursor = con.cursor()
    cursor.execute('''
        SELECT usn, password FROM users
        WHERE username = %s
    ''', (username,))

    user_data = cursor.fetchone()

    # Debugging: Print the stored hashed password
    stored_hashed_password = user_data[1] if user_data else None
    print(f"Debug: Stored hashed password: {stored_hashed_password}")

    if user_data and bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
        print(f"Welcome, {username}!")
        return user_data[0]  
    else:
        print("Invalid username or password.")
        return None


def update_email(con, username, new_email):
    """
    Update the email for an existing user.
    """
    cursor = con.cursor()
    try:
        cursor.execute(sql.SQL('''
            UPDATE users
            SET email = %s
            WHERE username = %s
            RETURNING username
        '''), (new_email, username))
        con.commit()

        updated_user = cursor.fetchone()

        if updated_user:
            print(f"Email for user '{updated_user[0]}' updated successfully!")
        else:
            print(f"User '{username}' not found.")
    except pg.Error as e:
        print(f"Error: {e}")
        con.rollback()

def update_name(con, username, new_name):
    """
    Update the username for an existing user.
    """
    cursor = con.cursor()
    try:
        cursor.execute(sql.SQL('''
            UPDATE users
            SET username = %s
            WHERE username = %s
            RETURNING username
        '''), (new_name, username))
        con.commit()

        updated_user = cursor.fetchone()

        if updated_user:
            print(f"Username for user '{updated_user[0]}' updated successfully!")
        else:
            print(f"User '{username}' not found.")
    except pg.Error as e:
        print(f"Error: {e}")
        con.rollback()

def update_user(con, username, new_password, new_email, new_name):
    """
    Update user information (password, email, username) for an existing user.
    """
    cursor = con.cursor()
    try:
        cursor.execute(sql.SQL('''
            UPDATE users
            SET password = crypt(%s, gen_salt('bf')),
                email = %s,
                username = %s
            WHERE username = %s
            RETURNING username
        '''), (new_password, new_email, new_name, username))
        con.commit()

        updated_user = cursor.fetchone()

        if updated_user:
            print(f"User '{updated_user[0]}' updated successfully!")
        else:
            print(f"User '{username}' not found.")
    except pg.Error as e:
        print(f"Error: {e}")
        con.rollback()

def update_password(con, username, new_password):
    """
    Update the password for an existing user.
    """
    cursor = con.cursor()
    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(sql.SQL('''
            UPDATE users
            SET password = %s
            WHERE username = %s
            RETURNING username
        '''), (hashed_password.decode('utf-8'), username))

        con.commit()

        updated_user = cursor.fetchone()

        if updated_user:
            print(f"Password for user '{updated_user[0]}' updated successfully!")
        else:
            print(f"User '{username}' not found.")
    except pg.Error as e:
        print(f"Error: {e}")
        con.rollback()

        
def display_existing_users(con, cursor):
    """
    Display existing users in the database.
    """
    cursor.execute('''
        SELECT usn, username, email FROM users
    ''')

    users = cursor.fetchall()

    if users:
        print("Existing Users:")
        for user in users:
            print(f"USN: {user[0]}, Username: {user[1]}, Email: {user[2]}")
    else:
        print("No users found.")
        
def login_options(con,cur):
    """
    Main program for choosing between sign up, login, and update user information.
    """
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            USN VARCHAR(12) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        )
    ''')
    con.commit()

    while True:
        print("\nChoose an option:")
        print("1. Sign Up")
        print("2. Log In")
        print("3. Update Password")
        print("4. Update Email")
        print("5. Update Name")
        print("6. Display Existing Users")
        print("7. Quit")

        choice = input("Enter the number of your choice: ")

        if choice == '1':
            usn = input("Enter your USN: ")
            username = input("Enter your username: ")
            password = getpass("Enter your password: ")
            email = input("Enter your email: ")

            create_user(con, usn, username, password, email)

        elif choice == '2':
            username = input("Enter your username: ")
            password = getpass("Enter your password: ")
            login_user(con, username, password)

        elif choice == '3':
            username = input("Enter your username: ")
            new_password = getpass("Enter the new password: ")
            update_password(con, username, new_password)

        elif choice == '4':
            username = input("Enter your username: ")
            new_email = input("Enter the new email: ")
            update_email(con, username, new_email)

        elif choice == '5':
            username = input("Enter your username: ")
            new_name = input("Enter the new name: ")
            update_name(con, username, new_name)
            
        elif choice == '6':
            """
            Display existing users in the database.
            """
            cur.execute('''
                SELECT usn, username, email FROM users
            ''')

            users = cur.fetchall()

            if users:
                print("\nExisting Users:")
                for user in users:
                    print(f"User ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
            else:
                print("No existing users found.")

        elif choice == '7':
            break

        else:
            print("Invalid choice. Please try again.")

def delete_user(con, cur, user_id):
    """
    Delete a user by their user ID.
    """
    try:
        cur.execute('''
            DELETE FROM users
            WHERE usn = %s
            RETURNING username
        ''', (user_id,))
        con.commit()

        deleted_user = cur.fetchone()

        if deleted_user:
            print(f"User '{deleted_user[0]}' deleted successfully!")
        else:
            print(f"User with ID '{user_id}' not found.")
    except pg.Error as e:
        print(f"Error: {e}")
        con.rollback()

#To issue a book from the library
def get_issue_details(con, cursor):
    id = input("Enter the member id (USN): ")
    name = input("Enter the member name: ")
    title = input("Enter the book issued: ")
    issue_date = input("Enter the date issued (YYYY-MM-DD): ")
    return_date = input("Enter the return date (YYYY-MM-DD): ")

    insert_record = """
    INSERT INTO Issued_Records (Member_Id, Member_Name, Book_Issued, Issued_Date, Return_Date)
    VALUES(%s, %s, %s, %s, %s);
    """

    try:
        cursor.execute(insert_record, (id, name, title, issue_date, return_date, 'Issued'))
        con.commit()
        print("Book issued successfully!")
    except pg.IntegrityError as e:
        print(f"Error: {e}")
        con.rollback()
        
def check_status(con, cursor):
    id = input("Enter the remark id (USN): ")
    user = input("Enter the user id by who issued the book: ")
    isbn = input("Enter the ISBN of the book issued: ")
    name = input("Enter the title of the book: ")
    date = input("Enter date by when it should have been returned (YYYY-MM-DD): ")
    status = input("Enter the status of the book (returned/pending)")
    
    update_record = "UPDATE Issued_Records SET Status = %s WHERE Book_Issued = %s"
    cursor.execute(update_record, [status, name])
    con.commit()
    
    if(status == "pending"):
        update_remarks = "INSERT INTO Remarks (Remark_ID, User_ID, ISBN, Due_Date, Fine) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(update_remarks, [id, user, isbn, date, 500])
        con.commit()

#To add a new publication to the library
def get_publication_details():
    id = input("Enter the member id (USN): ")
    author = input("Enter the author name: ")
    title = input("Enter the publication title: ")
    subject = input("Enter the subject of the publication: ")

    insert_record = """INSERT INTO Member_Publications
    VALUES(%s, %s, %s, %s);"""

    cur.execute(insert_record, [id, author, title, subject])

#To get feedback from the users regarding books
def add_feedback(con,cur, isbn, rating=None, comment=None, update_existing=False):
    if update_existing:
        update_query = '''
        UPDATE feedback
        SET Rating = %s, Comment = %s
        WHERE ISBN = %s;
        '''
        cur.execute(update_query, (rating, comment, isbn))
        con.commit()
    else:
        insert_query = '''
        INSERT INTO feedback 
        (ISBN, Rating, Comment)
        VALUES (%s, %s, %s);
        '''
        cur.execute(insert_query, (isbn, rating, comment))
        con.commit()
    print("Feedback added/updated successfully.")
    
    display_option = input("Do you want to display the feedback details? (y/n): ")
    if display_option.lower() == 'y':
        display_feedback(isbn,con,cur)
        
def isbn_exists(cursor, isbn):
    search_query = "SELECT EXISTS(SELECT 1 FROM feedback WHERE ISBN = %s);"
    cursor.execute(search_query, (isbn,))
    result = cursor.fetchone()[0]
    return result

def display_feedback(isbn,con,cur):
    try:
        select_query = "SELECT * FROM feedback WHERE ISBN = %s;"
        cur.execute(select_query, (isbn,))
        row = cur.fetchone()

        if row:
            print(f"\nFeedback details for ISBN {isbn}:")
            for column, value in zip(cur.description, row):
                print(f"{column.name}: {value}")
        else:
            print(f"No feedback found for ISBN {isbn}")

    except Exception as e:
        print(f"Error: Unable to retrieve feedback. {e}")

    finally:
        con.commit()
        con.close()

def provide_feedback(con,cur):
    try:
        isbn = input("Enter the ISBN of the book you want to provide feedback for: ")
        if isbn_exists(cur, isbn):
            select_query = "SELECT * FROM feedback WHERE ISBN = %s;"
            cur.execute(select_query, (isbn,))
            row = cur.fetchone()

            print(f"\nExisting details for ISBN {isbn}:")
            for column, value in zip(cur.description, row):
                display_value = "N/A" if value is None else value
                print(f"{column.name}: {display_value}")

            rating = int(input("\nEnter the rating (1-5): "))
            comment = input("Enter your feedback comment: ")

            if not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5.")

            add_feedback(con,cur, isbn, rating=rating, comment=comment, update_existing=True)

        else:
            print(f"Error: Book with ISBN {isbn} not found.")

    except ValueError as ve:
        print(f"Error: {ve}")

    except Exception as e:
        print(f"Error: Unable to provide feedback. {e}")

    finally:
        con.commit()
        con.close()

def main():
    con,cur = open_db()
    while True:
            print("\nEnter your choice:")
            print("1. Login Options")
            print("2. Search for a Book")
            print("3. Enter feedback for a Book")
            print("4. Book Status Update")
            print("5. Enter a Member Publication")
            print("6. Issue a Book")
            print("7. Delete a user")
            print("8. Quit")

            choice = input("Enter the number of your choice: ")

            try:
                if choice == '1':
                    con,cur = open_db()
                    display_existing_users(con, cur)
                    login_options(con, cur)

                elif choice == '2':
                    con,cur = open_db()
                    search_for_a_book(con, cur)
                    
                elif choice == '3':
                    con,cur = open_db()
                    provide_feedback(con,cur)

                elif choice == '4':
                    con,cur = open_db()
                    check_status(con, cur)
                
                elif choice == '5':
                    con,cur = open_db()
                    get_publication_details()

                elif choice == '6':
                    con,cur = open_db()
                    get_issue_details(con, cur)

                elif choice == '7':
                    con,cur = open_db()
                    user_id_to_delete = input("Enter the user ID you want to delete: ")
                    delete_user(con, cur, user_id_to_delete)

                elif choice == '8':
                    print("Exiting program.")
                    break

                else:
                    print("Invalid choice. Please try again.")

            except Exception as e:
                print(f"Error: {e}")

            except Exception as e:
                print(f"Error: Unable to open the database. {e}")

            finally:
                con.close()

main()

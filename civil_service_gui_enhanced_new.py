"""
Enhanced GUI for Civil Service Database Management System
A modern, user-friendly interface with improved design and UX

Features:
- Modern card-based layout
- Color-coded sections
- Better navigation
- Enhanced visual feedback
- Improved error handling
- Status indicators

Run: python civil_service_gui_enhanced.py

Dependencies: tkinter, mysql-connector-python
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import hashlib
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import io
import cv2
from PIL import Image, ImageTk
import re

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'civilservice',
    'user': 'root',
    'password': '[password_placeholder]'
}

# Color Scheme
COLORS = {
    'primary': '#2c3e50',      # Dark blue-gray
    'secondary': '#3498db',    # Blue
    'success': '#27ae60',      # Green
    'danger': '#e74c3c',       # Red
    'warning': '#f39c12',      # Orange
    'info': '#16a085',         # Teal
    'light': '#ecf0f1',        # Light gray
    'dark': '#34495e',         # Dark gray
    'white': '#ffffff',
    'text': '#2c3e50'
}


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True, buffered=True)
                return True
        except Error as e:
            messagebox.showerror('Database Error', f'Failed to connect: {e}')
        return False
    
    def close(self):
        """Close database connection"""
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
    
    def execute(self, query, params=None):
        """Execute a query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return True
        except Error as e:
            messagebox.showerror('Query Error', str(e))
            return False
    
    def fetchall(self):
        """Fetch all results"""
        return self.cursor.fetchall()
    
    def fetchone(self):
        """Fetch one result"""
        return self.cursor.fetchone()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def callproc(self, name, params):
        """Call stored procedure"""
        return self.cursor.callproc(name, params)


class ModernButton(tk.Button):
    """Custom styled button"""
    
    def __init__(self, parent, text, command, style='primary', **kwargs):
        bg_color = COLORS.get(style, COLORS['primary'])
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=COLORS['white'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10,
            **kwargs
        )
        self.bind('<Enter>', lambda e: self.config(bg=self._darken_color(bg_color)))
        self.bind('<Leave>', lambda e: self.config(bg=bg_color))
    
    def _darken_color(self, hex_color):
        """Darken a hex color"""
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        darker = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f'#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}'


class CivilServiceApp(tk.Tk):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        self.title('Civil Service Management System')
        self.geometry('1000x700')
        self.configure(bg=COLORS['light'])
        
        # Database connection
        self.db = Database()
        if not self.db.connect():
            messagebox.showerror('Fatal Error', 'Cannot connect to database. Exiting.')
            self.destroy()
            return
        
        # User session
        self.current_user = None
        self.user_type = None
        
        # Show login screen
        self.show_login_screen()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.winfo_children():
            widget.destroy()
    
    # ==================== LOGIN SCREEN ====================
    
    def show_login_screen(self):
        """Display login screen"""
        self.clear_window()
        self.geometry('500x600')
        
        # Header
        header = tk.Frame(self, bg=COLORS['primary'], height=100)
        header.pack(fill='x')
        
        tk.Label(
            header,
            text='Civil Service Portal',
            font=('Segoe UI', 24, 'bold'),
            bg=COLORS['primary'],
            fg=COLORS['white']
        ).pack(pady=30)
        
        # Login form container
        container = tk.Frame(self, bg=COLORS['white'])
        container.pack(expand=True, fill='both', padx=40, pady=40)
        
        tk.Label(
            container,
            text='Sign In',
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(pady=(20, 30))
        
        # Username
        tk.Label(
            container,
            text='Username',
            font=('Segoe UI', 10),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(anchor='w', padx=40)
        
        username_entry = tk.Entry(
            container,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1
        )
        username_entry.pack(fill='x', padx=40, pady=(5, 15))
        
        # Password
        tk.Label(
            container,
            text='Password',
            font=('Segoe UI', 10),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(anchor='w', padx=40)
        
        password_entry = tk.Entry(
            container,
            font=('Segoe UI', 11),
            relief='solid',
            bd=1,
            show='●'
        )
        password_entry.pack(fill='x', padx=40, pady=(5, 20))
        
        # Login button
        def attempt_login():
            username = username_entry.get().strip()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showwarning('Input Required', 'Please enter both username and password')
                return
            
            password_hash = hash_password(password)
            
            # Try citizen login
            self.db.execute(
                "SELECT c.*, a.name FROM citizens c JOIN aadhar a ON c.UID = a.UID WHERE c.username = %s AND c.password_hash = %s",
                (username, password_hash)
            )
            citizen = self.db.fetchone()
            
            if citizen:
                if citizen['account_status'] != 'Active':
                    messagebox.showerror('Account Inactive', 'Your account is not active. Contact admin.')
                    return
                self.current_user = citizen
                self.user_type = 'citizen'
                self.show_citizen_dashboard()
                return
            
            # Try admin login
            self.db.execute(
                "SELECT * FROM admin WHERE username = %s AND password_hash = %s",
                (username, password_hash)
            )
            admin = self.db.fetchone()
            
            if admin:
                self.current_user = admin
                self.user_type = 'admin'
                self.show_admin_dashboard()
                return
            
            messagebox.showerror('Login Failed', 'Invalid username or password')
        
        ModernButton(
            container,
            text='LOGIN',
            command=attempt_login,
            style='secondary'
        ).pack(pady=10, fill='x', padx=40)
        
        # Register link
        tk.Label(
            container,
            text='Don\'t have an account?',
            font=('Segoe UI', 9),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(pady=(20, 5))
        
        register_btn = tk.Button(
            container,
            text='Create New Account',
            font=('Segoe UI', 9, 'underline'),
            bg=COLORS['white'],
            fg=COLORS['secondary'],
            bd=0,
            cursor='hand2',
            command=self.show_registration_form
        )
        register_btn.pack()
    
    # ==================== REGISTRATION ====================
    
    def show_registration_form(self):
        """Display registration form"""
        win = tk.Toplevel(self)
        win.title('Create New Account')
        win.geometry('500x700')
        win.configure(bg=COLORS['light'])
        
        # Scrollable frame
        canvas = tk.Canvas(win, bg=COLORS['light'])
        scrollbar = ttk.Scrollbar(win, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y')
        
        # Form title
        tk.Label(
            scrollable_frame,
            text='Registration Form',
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(pady=20)
        
        # Form fields
        fields = [
            ('Username', 'username', None),
            ('Password', 'password', '●'),
            ('Confirm Password', 'confirm_password', '●'),
            ('Full Name', 'name', None),
            ('Gender (M/F/O)', 'gender', None),
            ('Date of Birth (YYYY-MM-DD)', 'dob', None),
            ('Aadhar UID (12 digits)', 'uid', None),
            ('Mobile (10 digits)', 'mobile', None),
            ('Email (optional)', 'email', None)
        ]
        
        entries = {}
        
        for label, key, show in fields:
            tk.Label(
                scrollable_frame,
                text=label,
                font=('Segoe UI', 10),
                bg=COLORS['white'],
                fg=COLORS['text'],
                anchor='w'
            ).pack(fill='x', padx=30, pady=(10, 2))
            
            entry = tk.Entry(
                scrollable_frame,
                font=('Segoe UI', 11),
                relief='solid',
                bd=1,
                show=show
            )
            entry.pack(fill='x', padx=30, pady=(0, 5))
            entries[key] = entry
        
        # Submit button
        def submit_registration():
            # Validate inputs
            username = entries['username'].get().strip()
            password = entries['password'].get()
            confirm = entries['confirm_password'].get()
            name = entries['name'].get().strip()
            gender = entries['gender'].get().strip().upper()
            dob = entries['dob'].get().strip()
            uid = entries['uid'].get().strip()
            mobile = entries['mobile'].get().strip()
            email = entries['email'].get().strip() or None
            
            if not all([username, password, confirm, name, gender, dob, uid, mobile]):
                messagebox.showwarning('Required Fields', 'Please fill all required fields')
                return
            
            if password != confirm:
                messagebox.showerror('Password Mismatch', 'Passwords do not match')
                return
            
            if gender not in ['M', 'F', 'O']:
                messagebox.showerror('Invalid Gender', 'Gender must be M, F, or O')
                return
            
            if not mobile.isdigit() or len(mobile) != 10:
                messagebox.showerror('Invalid Mobile', 'Mobile must be 10 digits')
                return
            
            if not uid.isdigit() or len(uid) != 12:
                messagebox.showerror('Invalid UID', 'Aadhar UID must be 12 digits')
                return
            
            try:
                datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror('Invalid Date', 'Date must be in YYYY-MM-DD format')
                return
            
            # Insert into pending_registrations
            try:
                password_hash = hash_password(password)
                self.db.execute(
                    """INSERT INTO pending_registrations 
                       (username, password_hash, UID, name, gender, DOB, mobile, email)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (username, password_hash, uid, name, gender, dob, mobile, email)
                )
                self.db.commit()
                messagebox.showinfo(
                    'Success',
                    'Registration submitted successfully!\nPlease wait for admin approval.'
                )
                win.destroy()
            except Error as e:
                messagebox.showerror('Registration Error', str(e))
        
        ModernButton(
            scrollable_frame,
            text='SUBMIT REGISTRATION',
            command=submit_registration,
            style='success'
        ).pack(pady=30, padx=30, fill='x')
    
    # ==================== CITIZEN DASHBOARD ====================
    
    def show_citizen_dashboard(self):
        """Display citizen dashboard"""
        self.clear_window()
        self.geometry('1200x750')
        
        # Header
        header = tk.Frame(self, bg=COLORS['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"Welcome, {self.current_user['name']}",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['primary'],
            fg=COLORS['white']
        ).pack(side='left', padx=30, pady=20)
        
        ModernButton(
            header,
            text='LOGOUT',
            command=self.logout,
            style='danger'
        ).pack(side='right', padx=30, pady=20)
        
        # Main content area
        content = tk.Frame(self, bg=COLORS['light'])
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Action cards
        actions = [
            ('👤 View Profile', self.view_citizen_profile, COLORS['info']),
            ('📋 View Services', self.view_citizen_services, COLORS['secondary']),
            ('✏️ Update Contact', self.update_citizen_contact, COLORS['warning']),
            ('🔍 Criminal Records', self.check_criminal_records, COLORS['danger']),
            ('💳 Register PAN', self.register_pan, COLORS['success']),
            ('🗳️ Register Voter ID', self.register_voter_id, COLORS['primary']),
            ('📱 Register SIM Card', self.register_sim, COLORS['info']),
            ('🏦 View Bank Accounts', self.view_bank_accounts, COLORS['dark']),
            ('🏦 Add Bank Account', self.register_bank_account, COLORS['success']),
            ('📸 Upload/Capture Photo', self.upload_capture_photo, COLORS['secondary']),
            ('🖼️ View My Photo', self.view_my_photo, COLORS['info'])
        ]
        
        for i, (text, command, color) in enumerate(actions):
            row = i // 4
            col = i % 4
            
            card = tk.Frame(content, bg=color, relief='raised', bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            btn = tk.Button(
                card,
                text=text,
                font=('Segoe UI', 12, 'bold'),
                bg=color,
                fg=COLORS['white'],
                relief='flat',
                cursor='hand2',
                command=command,
                padx=20,
                pady=30
            )
            btn.pack(fill='both', expand=True)
            
            content.grid_rowconfigure(row, weight=1)
            content.grid_columnconfigure(col, weight=1)
    
    def view_citizen_profile(self):
        """View citizen profile with all details"""
        uid = self.current_user['UID']
        
        try:
            # Get basic profile
            self.db.cursor.callproc('get_citizen_dashboard', [uid])
            results = list(self.db.cursor.stored_results())
            
            text = '=' * 80 + '\n'
            text += 'CITIZEN PROFILE - COMPLETE DETAILS\n'
            text += '=' * 80 + '\n\n'
            
            # Basic Information
            if results:
                profile = results[0].fetchone()
                if profile:
                    text += '📋 BASIC INFORMATION\n'
                    text += '-' * 80 + '\n'
                    text += f"UID (Aadhar Number): {profile['UID']}\n"
                    text += f"Full Name: {profile['name']}\n"
                    text += f"Gender: {profile['gender']}\n"
                    text += f"Date of Birth: {profile['DOB']}\n"
                    text += f"Age: {profile['age']} years\n"
                    text += f"Mobile Number: {profile['mobile']}\n"
                    text += f"Email Address: {profile['email'] or 'Not provided'}\n"
                    text += f"Account Status: {profile['account_status']}\n"
                    text += f"Account Created: {profile['account_created']}\n"
                    text += f"Last Login: {profile['last_login'] or 'Never'}\n\n"
                
                # Services Summary
                if len(results) > 1:
                    services = results[1].fetchone()
                    if services:
                        text += '📊 SERVICES SUMMARY\n'
                        text += '-' * 80 + '\n'
                        text += f"Total PAN Cards: {services['pan_count']}\n"
                        text += f"Total Voter IDs: {services['voter_id_count']}\n"
                        text += f"Total SIM Cards: {services['sim_count']}\n"
                        text += f"Total Bank Accounts: {services['bank_account_count']}\n"
                        text += f"Criminal Cases: {services['criminal_cases']}\n\n"
            
            # Get PAN Details
            self.db.execute("SELECT * FROM PAN WHERE UID = %s", (uid,))
            pans = self.db.fetchall()
            text += '💳 PAN CARD DETAILS\n'
            text += '-' * 80 + '\n'
            if pans:
                for i, pan in enumerate(pans, 1):
                    text += f"\nPAN #{i}:\n"
                    text += f"  PAN Number: {pan['panNumber']}\n"
                    text += f"  Issue Date: {pan['IssueDate']}\n"
                    text += f"  Status: {pan['Status']}\n"
            else:
                text += "No PAN cards registered\n"
            
            # Get Voter ID Details
            text += '\n🗳️ VOTER ID DETAILS\n'
            text += '-' * 80 + '\n'
            self.db.execute("SELECT * FROM votedID WHERE UID = %s", (uid,))
            voters = self.db.fetchall()
            if voters:
                for i, voter in enumerate(voters, 1):
                    text += f"\nVoter ID #{i}:\n"
                    text += f"  EPIC Number: {voter['EPIC']}\n"
                    text += f"  Name: {voter['name']}\n"
                    text += f"  Address: {voter['address']}\n"
                    text += f"  Registration Type: {voter['registration_type']}\n"
                    text += f"  Issue Date: {voter['IssueDate'] or 'Not specified'}\n"
                    text += f"  Status: {voter['Status']}\n"
                    text += f"  Primary: {'Yes' if voter['is_primary'] else 'No'}\n"
                    text += f"  Created On: {voter['created_on']}\n"
            else:
                text += "No Voter IDs registered\n"
            
            # Get SIM Details
            text += '\n📱 SIM CARD DETAILS\n'
            text += '-' * 80 + '\n'
            self.db.execute("SELECT * FROM simCard WHERE UID = %s", (uid,))
            sims = self.db.fetchall()
            if sims:
                for i, sim in enumerate(sims, 1):
                    text += f"\nSIM #{i}:\n"
                    text += f"  SIM Number: {sim['simNo']}\n"
                    text += f"  Provider: {sim['provider']}\n"
                    text += f"  Status: {sim['status']}\n"
            else:
                text += "No SIM cards registered\n"
            
            # Get Bank Account Details
            text += '\n🏦 BANK ACCOUNT DETAILS\n'
            text += '-' * 80 + '\n'
            self.db.execute("SELECT * FROM bankAccount WHERE UID = %s", (uid,))
            accounts = self.db.fetchall()
            if accounts:
                for i, acc in enumerate(accounts, 1):
                    text += f"\nBank Account #{i}:\n"
                    text += f"  Account Number: {acc['AccNo']}\n"
                    text += f"  Bank Name: {acc['bankName']}\n"
                    text += f"  Account Type: {acc['type']}\n"
                    text += f"  IFSC Code: {acc['IFSC']}\n"
            else:
                text += "No bank accounts registered\n"
            
            # Get Biometric Status
            text += '\n📸 BIOMETRIC INFORMATION\n'
            text += '-' * 80 + '\n'
            self.db.execute("SELECT has_photo, photo_type FROM biometrics WHERE UID = %s", (uid,))
            bio = self.db.fetchone()
            if bio:
                text += f"Photo Uploaded: {'Yes ✓' if bio['has_photo'] else 'No ✗'}\n"
                if bio['has_photo']:
                    text += f"Photo Type: {bio['photo_type'].upper()}\n"
            else:
                text += "No biometric data\n"
            
            text += '\n' + '=' * 80 + '\n'
            
            self.show_text_window('Complete Profile Details', text)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def view_citizen_services(self):
        """View all services"""
        uid = self.current_user['UID']
        
        try:
            text = '=' * 80 + '\n'
            text += 'YOUR SERVICES\n'
            text += '=' * 80 + '\n\n'
            
            # PAN
            self.db.execute("SELECT * FROM PAN WHERE UID = %s", (uid,))
            pans = self.db.fetchall()
            text += '--- PAN CARDS ---\n'
            if pans:
                for pan in pans:
                    text += f"  PAN: {pan['panNumber']}, Issue Date: {pan['IssueDate']}, Status: {pan['Status']}\n"
            else:
                text += "  No PAN cards registered\n"
            text += '\n'
            
            # Voter ID
            self.db.execute("SELECT * FROM votedID WHERE UID = %s", (uid,))
            voters = self.db.fetchall()
            text += '--- VOTER IDs ---\n'
            if voters:
                for v in voters:
                    text += f"  EPIC: {v['EPIC']}, Name: {v['name']}, Address: {v['address']}\n"
                    text += f"  Type: {v['registration_type']}, Status: {v['Status']}\n\n"
            else:
                text += "  No Voter IDs registered\n"
            text += '\n'
            
            # SIM Cards
            self.db.execute("SELECT * FROM simCard WHERE UID = %s", (uid,))
            sims = self.db.fetchall()
            text += '--- SIM CARDS ---\n'
            if sims:
                for sim in sims:
                    text += f"  SIM: {sim['simNo']}, Provider: {sim['provider']}, Status: {sim['status']}\n"
            else:
                text += "  No SIM cards registered\n"
            text += '\n'
            
            # Bank Accounts
            self.db.execute("SELECT * FROM bankAccount WHERE UID = %s", (uid,))
            banks = self.db.fetchall()
            text += '--- BANK ACCOUNTS ---\n'
            if banks:
                for bank in banks:
                    text += f"  Account: {bank['AccNo']}, Bank: {bank['bankName']}\n"
                    text += f"  Type: {bank['type']}, IFSC: {bank['IFSC']}\n\n"
            else:
                text += "  No bank accounts registered\n"
            
            self.show_text_window('Your Services', text)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def update_citizen_contact(self):
        """Update contact information"""
        uid = self.current_user['UID']
        
        win = tk.Toplevel(self)
        win.title('Update Contact Information')
        win.geometry('400x300')
        win.configure(bg=COLORS['white'])
        
        tk.Label(
            win,
            text='Update Contact',
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['white'],
            fg=COLORS['text']
        ).pack(pady=20)
        
        tk.Label(
            win,
            text='New Mobile (10 digits)',
            font=('Segoe UI', 10),
            bg=COLORS['white']
        ).pack(pady=(10, 5))
        
        mobile_entry = tk.Entry(win, font=('Segoe UI', 11))
        mobile_entry.pack(pady=5)
        
        tk.Label(
            win,
            text='New Email (optional)',
            font=('Segoe UI', 10),
            bg=COLORS['white']
        ).pack(pady=(10, 5))
        
        email_entry = tk.Entry(win, font=('Segoe UI', 11))
        email_entry.pack(pady=5)
        
        def submit():
            mobile = mobile_entry.get().strip()
            email = email_entry.get().strip() or None
            
            if not mobile:
                messagebox.showwarning('Required', 'Mobile number is required')
                return
            
            if not mobile.isdigit() or len(mobile) != 10:
                messagebox.showerror('Invalid', 'Mobile must be 10 digits')
                return
            
            try:
                self.db.cursor.callproc('update_citizen_profile', [uid, mobile, email])
                self.db.commit()
                messagebox.showinfo('Success', 'Contact information updated successfully')
                win.destroy()
            except Error as e:
                messagebox.showerror('Error', str(e))
        
        ModernButton(win, text='UPDATE', command=submit, style='success').pack(pady=20)
    
    def check_criminal_records(self):
        """Check criminal records"""
        uid = self.current_user['UID']
        
        try:
            self.db.execute(
                """SELECT cr.CaseNo, cr.offenceType 
                   FROM criminalRecord cr 
                   JOIN criminalRecord_Aadhar cra ON cr.CaseNo = cra.CaseNo 
                   WHERE cra.UID = %s""",
                (uid,)
            )
            records = self.db.fetchall()
            
            if records:
                text = '=' * 60 + '\n'
                text += 'CRIMINAL RECORDS\n'
                text += '=' * 60 + '\n\n'
                for rec in records:
                    text += f"Case No: {rec['CaseNo']}\n"
                    text += f"Offence Type: {rec['offenceType']}\n"
                    text += '-' * 60 + '\n'
            else:
                text = 'No criminal records found. You have a clean record!'
            
            self.show_text_window('Criminal Records', text)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def register_pan(self):
        """Register PAN card"""
        uid = self.current_user['UID']
        
        win = tk.Toplevel(self)
        win.title('Register PAN Card')
        win.geometry('400x300')
        win.configure(bg=COLORS['white'])
        
        tk.Label(
            win,
            text='Register PAN',
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['white']
        ).pack(pady=20)
        
        tk.Label(win, text='PAN Number (Format: ABCDE1234F)', bg=COLORS['white']).pack(pady=5)
        pan_entry = tk.Entry(win, font=('Segoe UI', 11))
        pan_entry.pack(pady=5)
        tk.Label(win, text='5 letters + 4 digits + 1 letter', font=('Segoe UI', 8), bg=COLORS['white'], fg='gray').pack()
        
        tk.Label(win, text='Issue Date (YYYY-MM-DD)', bg=COLORS['white']).pack(pady=5)
        date_entry = tk.Entry(win, font=('Segoe UI', 11))
        date_entry.pack(pady=5)
        
        def submit():
            pan = pan_entry.get().strip().upper()
            issue_date = date_entry.get().strip()
            
            if not pan or not issue_date:
                messagebox.showwarning('Required', 'All fields are required')
                return
            
            # Validate PAN format: 5 uppercase letters, 4 digits, 1 uppercase letter
            # Example: ABCDE1234F
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
            if not re.match(pan_pattern, pan):
                messagebox.showerror(
                    'Invalid PAN Format',
                    'PAN must be in format: ABCDE1234F\n\n'
                    '• 5 uppercase letters\n'
                    '• 4 digits\n'
                    '• 1 uppercase letter\n\n'
                    'Example: ABCDE1234F'
                )
                return
            
            # Validate date format
            try:
                datetime.strptime(issue_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror('Invalid Date', 'Date must be in format YYYY-MM-DD')
                return
            
            try:
                # Check if PAN already exists in the system
                self.db.execute("SELECT panNumber, UID FROM PAN WHERE panNumber = %s", (pan,))
                existing_pan = self.db.fetchone()
                
                if existing_pan:
                    messagebox.showerror(
                        'PAN Already Exists',
                        f'The PAN {pan} is already registered in the system.\n\n'
                        f'PAN numbers must be unique.\n'
                        f'Please verify your PAN number.'
                    )
                    return
                
                self.db.execute(
                    "INSERT INTO PAN (panNumber, IssueDate, Status, UID) VALUES (%s, %s, %s, %s)",
                    (pan, issue_date, 'Active', uid)
                )
                self.db.commit()
                messagebox.showinfo('Success', f'PAN card {pan} registered successfully')
                win.destroy()
            except Error as e:
                messagebox.showerror('Error', str(e))
        
        ModernButton(win, text='REGISTER', command=submit, style='success').pack(pady=20)
    
    def register_voter_id(self):
        """Register Voter ID"""
        uid = self.current_user['UID']
        
        win = tk.Toplevel(self)
        win.title('Register Voter ID')
        win.geometry('400x400')
        win.configure(bg=COLORS['white'])
        
        tk.Label(
            win,
            text='Register Voter ID',
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['white']
        ).pack(pady=20)
        
        fields = [
            ('EPIC (VOTERXXX, enter your number in place of XXX)', 'epic'),
            ('Address', 'address'),
            ('Type (City/Village/Rural/Urban)', 'reg_type')
        ]
        
        entries = {}
        for label, key in fields:
            tk.Label(win, text=label, bg=COLORS['white']).pack(pady=5)
            entry = tk.Entry(win, font=('Segoe UI', 11))
            entry.pack(pady=5)
            entries[key] = entry
        
        def submit():
            epic = entries['epic'].get().strip().upper()
            address = entries['address'].get().strip()
            reg_type = entries['reg_type'].get().strip()
            
            if not all([epic, address, reg_type]):
                messagebox.showwarning('Required', 'All fields are required')
                return
            
            # Validate EPIC format: Must start with "VOTER" followed by any characters
            # Total length must be exactly 10 characters
            # Examples: VOTER001, VOTER123, VOTERA01, etc.
            if len(epic) != 8:
                messagebox.showerror(
                    'Invalid EPIC Length',
                    'EPIC must be exactly 10 characters\n\n'
                    'Format: VOTERXXX\n'
                    'Example: VOTER001, VOTER123'
                )
                return
            
            if not epic.startswith('VOTER'):
                messagebox.showerror(
                    'Invalid EPIC Format',
                    'EPIC must start with "VOTER"\n\n'
                    'Format: VOTERXXX\n'
                    'Where XXX can be any 5 characters\n\n'
                    'Examples:\n'
                    '• VOTER001\n'
                    '• VOTER123\n'
                    '• VOTERA01\n'
                    '• VOTER99X'
                )
                return
            
            # Validate registration type
            valid_types = ['City', 'Village', 'Rural', 'Urban', 'Other']
            if reg_type not in valid_types:
                messagebox.showerror(
                    'Invalid Type',
                    f'Registration type must be one of:\n' + '\n'.join(f'• {t}' for t in valid_types)
                )
                return
            
            try:
                # Check if EPIC already exists in votedID table
                self.db.execute("SELECT EPIC, name FROM votedID WHERE EPIC = %s", (epic,))
                existing_epic = self.db.fetchone()
                
                if existing_epic:
                    messagebox.showerror(
                        'EPIC Already Exists',
                        f'The EPIC {epic} is already registered in the system.\n\n'
                        f'Please use a different EPIC number.'
                    )
                    return
                
                # Insert into votedID if EPIC doesn't exist
                self.db.execute(
                    """INSERT INTO votedID (EPIC, UID, name, address, registration_type) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (epic, uid, self.current_user['name'], address, reg_type)
                )
                self.db.commit()
                messagebox.showinfo('Success', f'Voter ID {epic} registered successfully')
                win.destroy()
            except Error as e:
                messagebox.showerror('Error', str(e))
        
        ModernButton(win, text='REGISTER', command=submit, style='success').pack(pady=20)
    
    def register_sim(self):
        """Register SIM card"""
        uid = self.current_user['UID']
        
        win = tk.Toplevel(self)
        win.title('Register SIM Card')
        win.geometry('400x300')
        win.configure(bg=COLORS['white'])
        
        tk.Label(
            win,
            text='Register SIM Card',
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['white']
        ).pack(pady=20)
        
        tk.Label(win, text='SIM Number (10 digits)', bg=COLORS['white']).pack(pady=5)
        sim_entry = tk.Entry(win, font=('Segoe UI', 11))
        sim_entry.pack(pady=5)
        
        tk.Label(win, text='Provider', bg=COLORS['white']).pack(pady=5)
        provider_entry = tk.Entry(win, font=('Segoe UI', 11))
        provider_entry.pack(pady=5)
        
        def submit():
            sim = sim_entry.get().strip()
            provider = provider_entry.get().strip()
            
            if not sim or not provider:
                messagebox.showwarning('Required', 'All fields are required')
                return
            
            try:
                self.db.execute(
                    "INSERT INTO simCard (simNo, provider, status, UID) VALUES (%s, %s, %s, %s)",
                    (sim, provider, 'Active', uid)
                )
                self.db.commit()
                messagebox.showinfo('Success', 'SIM card registered successfully')
                win.destroy()
            except Error as e:
                messagebox.showerror('Error', str(e))
        
        ModernButton(win, text='REGISTER', command=submit, style='success').pack(pady=20)
    
    def view_bank_accounts(self):
        """View bank accounts"""
        uid = self.current_user['UID']
        
        try:
            self.db.execute("SELECT * FROM bankAccount WHERE UID = %s", (uid,))
            accounts = self.db.fetchall()
            
            if accounts:
                text = '=' * 80 + '\n'
                text += 'YOUR BANK ACCOUNTS\n'
                text += '=' * 80 + '\n\n'
                for acc in accounts:
                    text += f"Account Number: {acc['AccNo']}\n"
                    text += f"Bank Name: {acc['bankName']}\n"
                    text += f"Account Type: {acc['type']}\n"
                    text += f"IFSC Code: {acc['IFSC']}\n"
                    text += '-' * 80 + '\n\n'
            else:
                text = 'No bank accounts registered'
            
            self.show_text_window('Bank Accounts', text)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def register_bank_account(self):
        """Register a new bank account"""
        uid = self.current_user['UID']
        
        win = tk.Toplevel(self)
        win.title('Register Bank Account')
        win.geometry('450x450')
        win.configure(bg=COLORS['white'])
        
        tk.Label(
            win,
            text='Register Bank Account',
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['white']
        ).pack(pady=20)
        
        # Account Number
        tk.Label(win, text='Account Number', bg=COLORS['white']).pack(pady=5)
        acc_entry = tk.Entry(win, font=('Segoe UI', 11))
        acc_entry.pack(pady=5)
        
        # Bank Name
        tk.Label(win, text='Bank Name', bg=COLORS['white']).pack(pady=5)
        bank_entry = tk.Entry(win, font=('Segoe UI', 11))
        bank_entry.pack(pady=5)
        
        # Account Type
        tk.Label(win, text='Account Type (Savings/Current/Other)', bg=COLORS['white']).pack(pady=5)
        type_entry = tk.Entry(win, font=('Segoe UI', 11))
        type_entry.pack(pady=5)
        
        # IFSC Code
        tk.Label(win, text='IFSC Code', bg=COLORS['white']).pack(pady=5)
        ifsc_entry = tk.Entry(win, font=('Segoe UI', 11))
        ifsc_entry.pack(pady=5)
        
        def submit():
            acc_no = acc_entry.get().strip()
            bank_name = bank_entry.get().strip()
            acc_type = type_entry.get().strip()
            ifsc = ifsc_entry.get().strip().upper()
            
            if not all([acc_no, bank_name, acc_type, ifsc]):
                messagebox.showwarning('Required', 'All fields are required')
                return
            
            # Validate IFSC format (11 characters: 4 letters + 7 alphanumeric)
            ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
            if not re.match(ifsc_pattern, ifsc):
                messagebox.showerror(
                    'Invalid IFSC Code',
                    'IFSC must be 11 characters:\n\n'
                    '• 4 uppercase letters (bank code)\n'
                    '• 1 zero (reserved)\n'
                    '• 6 alphanumeric (branch code)\n\n'
                    'Example: SBIN0001234'
                )
                return
            
            try:
                # Check if account number already exists
                self.db.execute("SELECT AccNo FROM bankAccount WHERE AccNo = %s", (acc_no,))
                existing = self.db.fetchone()
                
                if existing:
                    messagebox.showerror('Duplicate Account', f'Account number {acc_no} already exists in the system')
                    return
                
                self.db.execute(
                    "INSERT INTO bankAccount (AccNo, bankName, type, IFSC, UID) VALUES (%s, %s, %s, %s, %s)",
                    (acc_no, bank_name, acc_type, ifsc, uid)
                )
                self.db.commit()
                messagebox.showinfo('Success', f'Bank account {acc_no} registered successfully')
                win.destroy()
            except Error as e:
                messagebox.showerror('Error', str(e))
        
        ModernButton(win, text='REGISTER', command=submit, style='success').pack(pady=20)
    
    def upload_capture_photo(self):
        """Upload or capture photo using webcam"""
        uid = self.current_user['UID']
        
        # Ask user: Upload or Capture
        choice = messagebox.askquestion(
            'Photo Upload',
            'Do you want to CAPTURE photo using webcam?\n\n'
            'Click YES to capture from webcam\n'
            'Click NO to cancel',
            icon='question'
        )
        
        if choice == 'no':
            return
        
        # Capture from webcam
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                messagebox.showerror('Error', 'Cannot open webcam')
                return
            
            # Create window for camera preview
            capture_window = tk.Toplevel(self)
            capture_window.title('Capture Photo')
            capture_window.geometry('750x750')
            capture_window.configure(bg=COLORS['light'])
            
            # Header
            header = tk.Frame(capture_window, bg=COLORS['primary'], height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text='📸 Webcam Capture',
                font=('Segoe UI', 16, 'bold'),
                bg=COLORS['primary'],
                fg=COLORS['white']
            ).pack(pady=15)
            
            # Video frame
            video_frame = tk.Label(capture_window, bg=COLORS['light'])
            video_frame.pack(pady=10)
            
            # Button frame - placed BEFORE instructions so it's higher up
            btn_frame = tk.Frame(capture_window, bg=COLORS['light'])
            btn_frame.pack(pady=15)
            
            # Instructions
            tk.Label(
                capture_window,
                text='Position yourself in the frame and click Capture when ready',
                font=('Segoe UI', 10),
                bg=COLORS['light'],
                fg=COLORS['dark']
            ).pack(pady=5)
            
            captured_image = [None]  # Use list to allow modification in nested function
            
            def update_frame():
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        # Convert BGR to RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # Resize for display
                        frame_rgb = cv2.resize(frame_rgb, (640, 480))
                        # Convert to PhotoImage
                        img = Image.fromarray(frame_rgb)
                        imgtk = ImageTk.PhotoImage(image=img)
                        video_frame.imgtk = imgtk
                        video_frame.configure(image=imgtk)
                    
                    if captured_image[0] is None:
                        capture_window.after(10, update_frame)
            
            def capture_photo():
                ret, frame = cap.read()
                if ret:
                    captured_image[0] = frame
                    cap.release()
                    
                    # Show preview of captured image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_rgb = cv2.resize(frame_rgb, (640, 480))
                    img = Image.fromarray(frame_rgb)
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_frame.imgtk = imgtk
                    video_frame.configure(image=imgtk)
                    
                    # Update buttons
                    capture_btn.configure(state='disabled')
                    save_btn.configure(state='normal')
                    retake_btn.configure(state='normal')
            
            def retake_photo():
                captured_image[0] = None
                # Reopen camera
                nonlocal cap
                cap = cv2.VideoCapture(0)
                capture_btn.configure(state='normal')
                save_btn.configure(state='disabled')
                retake_btn.configure(state='disabled')
                update_frame()
            
            def save_photo():
                if captured_image[0] is not None:
                    try:
                        # Convert to JPEG bytes
                        success, buffer = cv2.imencode('.jpg', captured_image[0])
                        if success:
                            photo_data = buffer.tobytes()
                            
                            # Update database
                            query = """
                                UPDATE biometrics 
                                SET photo = %s, photo_type = 'jpg', has_photo = 1 
                                WHERE UID = %s
                            """
                            self.db.cursor.execute(query, (photo_data, uid))
                            self.db.conn.commit()
                            
                            messagebox.showinfo('Success', 'Photo uploaded successfully!')
                            cap.release()
                            capture_window.destroy()
                        else:
                            messagebox.showerror('Error', 'Failed to encode image')
                    except Error as e:
                        messagebox.showerror('Database Error', str(e))
            
            def close_window():
                cap.release()
                capture_window.destroy()
            
            # Buttons - using standard tk.Button for better visibility
            capture_btn = tk.Button(
                btn_frame,
                text='📸 CAPTURE PHOTO',
                command=capture_photo,
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['success'],
                fg='white',
                padx=20,
                pady=10,
                relief='raised',
                bd=3,
                cursor='hand2'
            )
            capture_btn.pack(side='left', padx=10)
            
            retake_btn = tk.Button(
                btn_frame,
                text='🔄 RETAKE',
                command=retake_photo,
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['warning'],
                fg='white',
                padx=20,
                pady=10,
                relief='raised',
                bd=3,
                cursor='hand2',
                state='disabled'
            )
            retake_btn.pack(side='left', padx=10)
            
            save_btn = tk.Button(
                btn_frame,
                text='💾 SAVE TO DATABASE',
                command=save_photo,
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['primary'],
                fg='white',
                padx=20,
                pady=10,
                relief='raised',
                bd=3,
                cursor='hand2',
                state='disabled'
            )
            save_btn.pack(side='left', padx=10)
            
            tk.Button(
                btn_frame,
                text='❌ CANCEL',
                command=close_window,
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['danger'],
                fg='white',
                padx=20,
                pady=10,
                relief='raised',
                bd=3,
                cursor='hand2'
            ).pack(side='left', padx=10)
            
            # Start video feed
            update_frame()
            
            capture_window.protocol("WM_DELETE_WINDOW", close_window)
            
        except Exception as e:
            messagebox.showerror('Error', f'Webcam error: {str(e)}')
    
    def view_my_photo(self):
        """View citizen's uploaded photo"""
        uid = self.current_user['UID']
        
        try:
            self.db.cursor.execute(
                "SELECT has_photo, photo, photo_type FROM biometrics WHERE UID = %s",
                (uid,)
            )
            result = self.db.cursor.fetchone()
            
            if not result:
                messagebox.showinfo('No Data', 'No biometric record found')
                return
            
            if not result['has_photo'] or not result['photo']:
                messagebox.showinfo(
                    'No Photo',
                    'You have not uploaded a photo yet.\n\n'
                    'Use "Upload/Capture Photo" to add your photo.'
                )
                return
            
            # Display photo
            photo_data = result['photo']
            img = Image.open(io.BytesIO(photo_data))
            
            # Create window to display photo
            photo_window = tk.Toplevel(self)
            photo_window.title('My Photo')
            photo_window.configure(bg=COLORS['light'])
            
            # Header
            header = tk.Frame(photo_window, bg=COLORS['info'], height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text=f'🖼️ Photo - {self.current_user["name"]}',
                font=('Segoe UI', 16, 'bold'),
                bg=COLORS['info'],
                fg=COLORS['white']
            ).pack(pady=15)
            
            # Resize image to fit window
            img.thumbnail((600, 600))
            photo = ImageTk.PhotoImage(img)
            
            # Display image
            img_label = tk.Label(photo_window, image=photo, bg=COLORS['light'])
            img_label.image = photo  # Keep reference
            img_label.pack(pady=20, padx=20)
            
            # Info
            tk.Label(
                photo_window,
                text=f'UID: {uid} | Type: {result["photo_type"].upper()}',
                font=('Segoe UI', 10),
                bg=COLORS['light'],
                fg=COLORS['dark']
            ).pack(pady=10)
            
            # Close button
            ModernButton(
                photo_window,
                text='CLOSE',
                command=photo_window.destroy,
                style='primary'
            ).pack(pady=20)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load photo: {str(e)}')
    
    # ==================== ADMIN DASHBOARD ====================
    
    def show_admin_dashboard(self):
        """Display admin dashboard"""
        self.clear_window()
        self.geometry('1200x750')
        
        # Header
        header = tk.Frame(self, bg=COLORS['dark'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"Admin Panel - {self.current_user['full_name']}",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['dark'],
            fg=COLORS['white']
        ).pack(side='left', padx=30, pady=20)
        
        ModernButton(
            header,
            text='LOGOUT',
            command=self.logout,
            style='danger'
        ).pack(side='right', padx=30, pady=20)
        
        # Main content
        content = tk.Frame(self, bg=COLORS['light'])
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Admin actions
        actions = [
            ('📋 Pending Registrations', self.view_pending_registrations, COLORS['warning']),
            ('✅ Approve/Reject', self.approve_reject_registration, COLORS['success']),
            ('🔍 Search Citizen', self.search_citizen, COLORS['info']),
            ('👥 View All Citizens', self.view_all_citizens, COLORS['secondary']),
            ('📊 Database Statistics', self.view_statistics, COLORS['primary']),
            ('📜 Audit Logs', self.view_audit_logs, COLORS['dark']),
            ('🗳️ Multiple Voter IDs', self.admin_add_voter_id, COLORS['info']),
            ('🏦 Multiple Bank Accounts', self.admin_view_bank_accounts, COLORS['success']),
            ('⚠️ Criminal Records', self.admin_criminal_mgmt, COLORS['danger']),
            ('🖼️ View Citizen Photos', self.admin_view_photos, COLORS['secondary'])
        ]
        
        for i, (text, command, color) in enumerate(actions):
            row = i // 4
            col = i % 4
            
            card = tk.Frame(content, bg=color, relief='raised', bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            btn = tk.Button(
                card,
                text=text,
                font=('Segoe UI', 12, 'bold'),
                bg=color,
                fg=COLORS['white'],
                relief='flat',
                cursor='hand2',
                command=command,
                padx=20,
                pady=30
            )
            btn.pack(fill='both', expand=True)
            
            content.grid_rowconfigure(row, weight=1)
            content.grid_columnconfigure(col, weight=1)
    
    def view_pending_registrations(self):
        """View pending registrations"""
        try:
            self.db.execute("SELECT * FROM pending_registrations_summary")
            rows = self.db.fetchall()
            self.show_table_window('Pending Registrations', rows)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def approve_reject_registration(self):
        """Approve or reject registration with UID conflict check"""
        request_id = simpledialog.askinteger('Request ID', 'Enter Request ID:', parent=self)
        if not request_id:
            return
        
        admin_id = self.current_user['admin_id']
        
        try:
            # Fetch registration details
            self.db.execute(
                """SELECT request_id, username, UID, name, email, mobile, request_date 
                   FROM pending_registrations WHERE request_id = %s AND status = 'Pending'""",
                (request_id,)
            )
            registration = self.db.fetchone()
            
            if not registration:
                messagebox.showerror('Not Found', f'Pending registration request ID {request_id} not found')
                return
            
            # Check if UID already exists in aadhar table
            self.db.execute("SELECT UID, name FROM aadhar WHERE UID = %s", (registration['UID'],))
            existing_uid = self.db.fetchone()
            
            # If UID conflict exists, automatically reject
            if existing_uid:
                conflict_reason = f"UID {registration['UID']} already exists in the system (Name: {existing_uid['name']})"
                try:
                    self.db.cursor.callproc('reject_registration', [request_id, admin_id, conflict_reason])
                    self.db.commit()
                    messagebox.showwarning(
                        'Conflict Detected - Auto Rejected',
                        f'Registration has been automatically REJECTED due to:\n\n'
                        f'{conflict_reason}\n\n'
                        f'Applicant: {registration["name"]}\n'
                        f'UID: {registration["UID"]}'
                    )
                except Error as e:
                    messagebox.showerror('Error', f'Failed to reject registration: {str(e)}')
                return
            
            # Create approval/rejection dialog with buttons
            review_window = tk.Toplevel(self)
            review_window.title('Review Registration Request')
            review_window.geometry('600x500')
            review_window.configure(bg=COLORS['white'])
            review_window.resizable(False, False)
            
            # Header
            header = tk.Frame(review_window, bg=COLORS['primary'], height=70)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text='Registration Review',
                font=('Segoe UI', 18, 'bold'),
                bg=COLORS['primary'],
                fg=COLORS['white']
            ).pack(pady=20)
            
            # Details frame
            details_frame = tk.Frame(review_window, bg=COLORS['light'])
            details_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Request details
            tk.Label(
                details_frame,
                text='REQUEST DETAILS',
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['light'],
                fg=COLORS['text']
            ).pack(anchor='w', pady=(0, 15))
            
            details_text = f"""
Request ID: {registration['request_id']}
Applicant Name: {registration['name']}
Username: {registration['username']}
UID (Aadhar): {registration['UID']}
Mobile: {registration['mobile']}
Email: {registration['email'] or 'Not provided'}
Request Date: {registration['request_date']}
UID Status: ✓ NOT FOUND IN SYSTEM (Safe to approve)
            """
            
            details_label = tk.Label(
                details_frame,
                text=details_text,
                font=('Segoe UI', 10),
                bg=COLORS['white'],
                fg=COLORS['text'],
                justify='left',
                relief='solid',
                bd=1,
                padx=15,
                pady=15
            )
            details_label.pack(fill='both', expand=True, pady=(0, 20))
            
            # Rejection reason section
            tk.Label(
                details_frame,
                text='Rejection Reason (if applicable)',
                font=('Segoe UI', 10),
                bg=COLORS['light'],
                fg=COLORS['text']
            ).pack(anchor='w', pady=(10, 5))
            
            reason_text = tk.Text(
                details_frame,
                height=4,
                font=('Segoe UI', 9),
                relief='solid',
                bd=1,
                wrap='word'
            )
            reason_text.pack(fill='x', pady=(0, 20))
            
            # Button frame
            btn_frame = tk.Frame(details_frame, bg=COLORS['light'])
            btn_frame.pack(fill='x', pady=10)
            
            def approve():
                try:
                    self.db.cursor.callproc('approve_registration', [request_id, admin_id])
                    self.db.commit()
                    messagebox.showinfo(
                        'Success',
                        f'Registration APPROVED successfully!\n\n'
                        f'Applicant: {registration["name"]}\n'
                        f'UID: {registration["UID"]}\n\n'
                        f'Account activation pending admin action.'
                    )
                    review_window.destroy()
                except Error as e:
                    messagebox.showerror('Error', f'Failed to approve: {str(e)}')
            
            def reject():
                reason = reason_text.get('1.0', 'end-1c').strip()
                if not reason:
                    messagebox.showwarning('Required', 'Please enter rejection reason')
                    return
                
                try:
                    self.db.cursor.callproc('reject_registration', [request_id, admin_id, reason])
                    self.db.commit()
                    messagebox.showinfo(
                        'Success',
                        f'Registration REJECTED successfully!\n\n'
                        f'Applicant: {registration["name"]}\n'
                        f'Reason: {reason}'
                    )
                    review_window.destroy()
                except Error as e:
                    messagebox.showerror('Error', f'Failed to reject: {str(e)}')
            
            def cancel():
                review_window.destroy()
            
            # Approve button (green)
            ModernButton(
                btn_frame,
                text='✅ APPROVE',
                command=approve,
                style='success'
            ).pack(side='left', padx=10, fill='x', expand=True)
            
            # Reject button (red)
            ModernButton(
                btn_frame,
                text='❌ REJECT',
                command=reject,
                style='danger'
            ).pack(side='left', padx=10, fill='x', expand=True)
            
            # Cancel button (gray)
            ModernButton(
                btn_frame,
                text='🚫 CANCEL',
                command=cancel,
                style='secondary'
            ).pack(side='left', padx=10, fill='x', expand=True)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
    
    def search_citizen(self):
        """Search citizen by UID with service counts"""
        uid = simpledialog.askstring('Search', 'Enter Aadhar UID (12 digits):', parent=self)
        if not uid:
            return
        
        try:
            # Fetch basic citizen information
            self.db.execute(
                """SELECT a.*, c.username, c.account_status 
                   FROM aadhar a 
                   LEFT JOIN citizens c ON a.UID = c.UID 
                   WHERE a.UID = %s""",
                (uid,)
            )
            citizen = self.db.fetchone()
            
            if not citizen:
                messagebox.showinfo('Not Found', 'No citizen found with this UID')
                return
            
            # Fetch service counts using SQL functions
            self.db.execute(
                """SELECT 
                    get_sim_count(%s) AS sim_count,
                    get_pan_count(%s) AS pan_count,
                    get_voterid_count(%s) AS voter_id_count,
                    get_bankaccount_count(%s) AS bank_account_count,
                    get_criminal_record_count(%s) AS criminal_record_count""",
                (uid, uid, uid, uid, uid)
            )
            counts = self.db.fetchone()
            
            # Format and display citizen details
            text = '=' * 80 + '\n'
            text += 'CITIZEN PROFILE - DETAILED VIEW\n'
            text += '=' * 80 + '\n\n'
            
            # Basic Information
            text += '📋 BASIC INFORMATION\n'
            text += '-' * 80 + '\n'
            text += f"UID (Aadhar Number): {citizen['UID']}\n"
            text += f"Full Name: {citizen['name']}\n"
            text += f"Gender: {citizen['gender']}\n"
            text += f"Date of Birth: {citizen['DOB']}\n"
            text += f"Mobile Number: {citizen['mobile']}\n"
            text += f"Email: {citizen['email'] or 'Not provided'}\n"
            
            if citizen['username']:
                text += f"Username: {citizen['username']}\n"
                text += f"Account Status: {citizen['account_status']}\n"
            else:
                text += "Account Status: Not Yet Registered\n"
            
            text += '\n'
            
            # Service Counts using SQL Functions
            text += '📊 SERVICE SUMMARY (Using SQL Functions)\n'
            text += '-' * 80 + '\n'
            text += f"✓ SIM Cards Registered: {counts['sim_count']}\n"
            text += f"✓ PAN Cards Registered: {counts['pan_count']}\n"
            text += f"✓ Voter IDs Registered: {counts['voter_id_count']}\n"
            text += f"✓ Bank Accounts Linked: {counts['bank_account_count']}\n"
            text += f"⚠️  Criminal Records: {counts['criminal_record_count']}\n"
            
            text += '\n' + '=' * 80 + '\n'
            
            self.show_text_window('Citizen Details', text)
            
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def view_all_citizens(self):
        """View all citizens"""
        try:
            self.db.execute(
                """SELECT a.UID, a.name, a.gender, a.mobile, c.username, c.account_status 
                   FROM aadhar a 
                   JOIN citizens c ON a.UID = c.UID 
                   ORDER BY a.name"""
            )
            rows = self.db.fetchall()
            self.show_table_window('All Citizens', rows)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def view_statistics(self):
        """View database statistics"""
        try:
            queries = [
                ('Total Citizens', 'SELECT COUNT(*) as count FROM aadhar'),
                ('Active Accounts', "SELECT COUNT(*) as count FROM citizens WHERE account_status='Active'"),
                ('Pending Registrations', "SELECT COUNT(*) as count FROM pending_registrations WHERE status='Pending'"),
                ('Total PANs', 'SELECT COUNT(*) as count FROM PAN'),
                ('Total Voter IDs', 'SELECT COUNT(*) as count FROM votedID'),
                ('Total SIM Cards', 'SELECT COUNT(*) as count FROM simCard'),
                ('Total Bank Accounts', 'SELECT COUNT(*) as count FROM bankAccount'),
                ('Total Criminal Cases', 'SELECT COUNT(*) as count FROM criminalRecord')
            ]
            
            text = '=' * 60 + '\n'
            text += 'DATABASE STATISTICS\n'
            text += '=' * 60 + '\n\n'
            
            for label, query in queries:
                self.db.execute(query)
                result = self.db.fetchone()
                text += f"{label}: {result['count']}\n"
            
            self.show_text_window('Statistics', text)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def view_audit_logs(self):
        """View audit logs"""
        try:
            self.db.execute("SELECT * FROM recent_audit_log LIMIT 100")
            rows = self.db.fetchall()
            self.show_table_window('Audit Logs', rows)
        except Error as e:
            messagebox.showerror('Error', str(e))
    
    def admin_add_voter_id(self):
        """Check citizens with minimum voter ID count"""
        min_count = simpledialog.askinteger(
            'Voter ID Count',
            'Enter minimum number of Voter IDs:\n\n'
            'Example: Enter 3 to find all citizens with 3 or MORE Voter IDs',
            parent=self,
            minvalue=1,
            maxvalue=100
        )
        
        if min_count is None:
            return
        
        try:
            # Call stored procedure
            self.db.cursor.callproc('get_citizens_minimum_voterids', [min_count])
            results = list(self.db.cursor.stored_results())
            
            if not results or not results[0]:
                messagebox.showinfo(
                    'No Results',
                    f'No citizens found with {min_count} or more Voter IDs in the system'
                )
                return
            
            rows = results[0].fetchall()
            
            # Create display window
            display_window = tk.Toplevel(self)
            display_window.title(f'Citizens with ≥{min_count} Voter IDs')
            display_window.geometry('1200x700')
            display_window.configure(bg=COLORS['light'])
            
            # Header
            header = tk.Frame(display_window, bg=COLORS['info'], height=80)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text=f'🗳️ Citizens with {min_count} or More Voter IDs',
                font=('Segoe UI', 20, 'bold'),
                bg=COLORS['info'],
                fg=COLORS['white']
            ).pack(side='left', padx=30, pady=20)
            
            tk.Label(
                header,
                text=f'Total Found: {len(rows)}',
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['info'],
                fg=COLORS['white']
            ).pack(side='right', padx=30, pady=20)
            
            # Content area with scrollbar
            canvas = tk.Canvas(display_window, bg=COLORS['white'])
            scrollbar = ttk.Scrollbar(display_window, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
            
            scrollable_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
            scrollbar.pack(side='right', fill='y')
            
            # Display each citizen's information
            for idx, row in enumerate(rows, 1):
                # Citizen card
                card_frame = tk.Frame(scrollable_frame, bg=COLORS['light'], relief='solid', bd=1)
                card_frame.pack(fill='x', pady=10)
                
                # Header with count badge
                header_frame = tk.Frame(card_frame, bg=COLORS['info'], height=50)
                header_frame.pack(fill='x')
                header_frame.pack_propagate(False)
                
                tk.Label(
                    header_frame,
                    text=f"{idx}. {row['name']}",
                    font=('Segoe UI', 14, 'bold'),
                    bg=COLORS['info'],
                    fg=COLORS['white']
                ).pack(side='left', padx=15, pady=10)
                
                tk.Label(
                    header_frame,
                    text=f"Voter IDs: {row['total_voter_ids']}",
                    font=('Segoe UI', 12, 'bold'),
                    bg=COLORS['success'],
                    fg=COLORS['white'],
                    padx=15,
                    pady=5,
                    relief='raised',
                    bd=2
                ).pack(side='right', padx=15, pady=10)
                
                # Details
                details_frame = tk.Frame(card_frame, bg=COLORS['white'])
                details_frame.pack(fill='x', padx=20, pady=15)
                
                # Basic info
                info_text = f"UID: {row['UID']}     |     Mobile: {row['mobile']}"
                tk.Label(
                    details_frame,
                    text=info_text,
                    font=('Segoe UI', 10),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(0, 10))
                
                # Voter details
                tk.Label(
                    details_frame,
                    text='Voter ID Details:',
                    font=('Segoe UI', 10, 'bold'),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(5, 5))
                
                # Parse and display voter details
                voter_details = row['voter_details'].split(' || ')
                for i, detail in enumerate(voter_details, 1):
                    detail_label = tk.Label(
                        details_frame,
                        text=f"  {i}. {detail}",
                        font=('Segoe UI', 9),
                        bg=COLORS['light'],
                        fg=COLORS['text'],
                        justify='left',
                        wraplength=1100
                    )
                    detail_label.pack(anchor='w', pady=2, padx=20)
            
            # Close button
            btn_frame = tk.Frame(display_window, bg=COLORS['light'])
            btn_frame.pack(fill='x', pady=20)
            
            ModernButton(
                btn_frame,
                text='❌ CLOSE',
                command=display_window.destroy,
                style='danger'
            ).pack(padx=20)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
        except Exception as e:
            messagebox.showerror('Error', f'An error occurred: {str(e)}')
    
    def admin_view_bank_accounts(self):
        """View citizens with minimum number of bank accounts"""
        min_count = simpledialog.askinteger(
            'Bank Account Count',
            'Enter minimum number of Bank Accounts:\n\n'
            'Example: Enter 2 to find all citizens with 2 or MORE Bank Accounts',
            parent=self,
            minvalue=1,
            maxvalue=100
        )
        
        if min_count is None:
            return
        
        try:
            # Query to get citizens with at least min_count bank accounts
            self.db.execute(
                """SELECT a.UID, a.name, a.mobile, COUNT(ba.AccNo) as total_accounts,
                   GROUP_CONCAT(
                       CONCAT('AccNo: ', ba.AccNo, ' | Bank: ', ba.bankName, ' | Type: ', ba.type, ' | IFSC: ', ba.IFSC)
                       SEPARATOR ' || '
                   ) as account_details
                   FROM aadhar a
                   JOIN bankAccount ba ON a.UID = ba.UID
                   GROUP BY a.UID, a.name, a.mobile
                   HAVING COUNT(ba.AccNo) >= %s
                   ORDER BY total_accounts DESC, a.name""",
                (min_count,)
            )
            rows = self.db.fetchall()
            
            if not rows:
                messagebox.showinfo(
                    'No Results',
                    f'No citizens found with {min_count} or more Bank Accounts in the system'
                )
                return
            
            # Create display window
            display_window = tk.Toplevel(self)
            display_window.title(f'Citizens with ≥{min_count} Bank Accounts')
            display_window.geometry('1200x700')
            display_window.configure(bg=COLORS['light'])
            
            # Header
            header = tk.Frame(display_window, bg=COLORS['success'], height=80)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text=f'🏦 Citizens with {min_count} or More Bank Accounts',
                font=('Segoe UI', 20, 'bold'),
                bg=COLORS['success'],
                fg=COLORS['white']
            ).pack(side='left', padx=30, pady=20)
            
            tk.Label(
                header,
                text=f'Total Found: {len(rows)}',
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['success'],
                fg=COLORS['white']
            ).pack(side='right', padx=30, pady=20)
            
            # Content area with scrollbar
            canvas = tk.Canvas(display_window, bg=COLORS['white'])
            scrollbar = ttk.Scrollbar(display_window, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
            
            scrollable_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
            scrollbar.pack(side='right', fill='y')
            
            # Display each citizen's information
            for idx, row in enumerate(rows, 1):
                # Citizen card
                card_frame = tk.Frame(scrollable_frame, bg=COLORS['light'], relief='solid', bd=1)
                card_frame.pack(fill='x', pady=10)
                
                # Header with count badge
                header_frame = tk.Frame(card_frame, bg=COLORS['success'], height=50)
                header_frame.pack(fill='x')
                header_frame.pack_propagate(False)
                
                tk.Label(
                    header_frame,
                    text=f"{idx}. {row['name']}",
                    font=('Segoe UI', 14, 'bold'),
                    bg=COLORS['success'],
                    fg=COLORS['white']
                ).pack(side='left', padx=15, pady=10)
                
                tk.Label(
                    header_frame,
                    text=f"Bank Accounts: {row['total_accounts']}",
                    font=('Segoe UI', 12, 'bold'),
                    bg=COLORS['primary'],
                    fg=COLORS['white'],
                    padx=15,
                    pady=5,
                    relief='raised',
                    bd=2
                ).pack(side='right', padx=15, pady=10)
                
                # Details
                details_frame = tk.Frame(card_frame, bg=COLORS['white'])
                details_frame.pack(fill='x', padx=20, pady=15)
                
                # Basic info
                info_text = f"UID: {row['UID']}     |     Mobile: {row['mobile']}"
                tk.Label(
                    details_frame,
                    text=info_text,
                    font=('Segoe UI', 10),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(0, 10))
                
                # Account details
                tk.Label(
                    details_frame,
                    text='Bank Account Details:',
                    font=('Segoe UI', 10, 'bold'),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(5, 5))
                
                # Parse and display account details
                account_details = row['account_details'].split(' || ')
                for i, detail in enumerate(account_details, 1):
                    detail_label = tk.Label(
                        details_frame,
                        text=f"  {i}. {detail}",
                        font=('Segoe UI', 9),
                        bg=COLORS['light'],
                        fg=COLORS['text'],
                        justify='left',
                        wraplength=1100
                    )
                    detail_label.pack(anchor='w', pady=2, padx=20)
            
            # Close button
            btn_frame = tk.Frame(display_window, bg=COLORS['light'])
            btn_frame.pack(fill='x', pady=20)
            
            ModernButton(
                btn_frame,
                text='❌ CLOSE',
                command=display_window.destroy,
                style='danger'
            ).pack(padx=20)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
        except Exception as e:
            messagebox.showerror('Error', f'An error occurred: {str(e)}')
    
    def admin_criminal_mgmt(self):
        """Criminal record management with check and register options"""
        # Create action selection window
        action_window = tk.Toplevel(self)
        action_window.title('Criminal Record Management')
        action_window.geometry('500x300')
        action_window.configure(bg=COLORS['white'])
        action_window.resizable(False, False)
        
        # Header
        header = tk.Frame(action_window, bg=COLORS['danger'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text='⚠️ Criminal Record Management',
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['danger'],
            fg=COLORS['white']
        ).pack(pady=20)
        
        # Content frame
        content_frame = tk.Frame(action_window, bg=COLORS['light'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        tk.Label(
            content_frame,
            text='Select an Action:',
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['light'],
            fg=COLORS['text']
        ).pack(pady=(0, 30))
        
        def check_records():
            action_window.destroy()
            self.check_criminal_case()
        
        def register_records():
            action_window.destroy()
            self.register_criminal_case()
        
        # Check button
        ModernButton(
            content_frame,
            text='🔍 CHECK CASE',
            command=check_records,
            style='info'
        ).pack(fill='x', pady=10)
        
        # Register button
        ModernButton(
            content_frame,
            text='📝 REGISTER CASE',
            command=register_records,
            style='warning'
        ).pack(fill='x', pady=10)
        
        # Cancel button
        ModernButton(
            content_frame,
            text='❌ CANCEL',
            command=action_window.destroy,
            style='danger'
        ).pack(fill='x', pady=10)
    
    def check_criminal_case(self):
        """Check criminal case by CaseNo"""
        case_no = simpledialog.askstring('Check Case', 'Enter Case Number:', parent=self)
        if not case_no:
            return
        
        try:
            # Fetch case details
            self.db.execute(
                "SELECT CaseNo, offenceType FROM criminalRecord WHERE CaseNo = %s",
                (case_no,)
            )
            case = self.db.fetchone()
            
            if not case:
                messagebox.showinfo('Not Found', f'Case Number {case_no} not found in the system')
                return
            
            # Fetch all UIDs linked to this case
            self.db.execute(
                """SELECT cra.UID, a.name, a.mobile 
                   FROM criminalRecord_Aadhar cra 
                   JOIN aadhar a ON cra.UID = a.UID 
                   WHERE cra.CaseNo = %s""",
                (case_no,)
            )
            linked_uids = self.db.fetchall()
            
            # Format display text
            text = '=' * 80 + '\n'
            text += 'CRIMINAL CASE DETAILS\n'
            text += '=' * 80 + '\n\n'
            
            text += '📋 CASE INFORMATION\n'
            text += '-' * 80 + '\n'
            text += f"Case Number: {case['CaseNo']}\n"
            text += f"Offence Type: {case['offenceType']}\n"
            text += f"Total Accused: {len(linked_uids)}\n\n"
            
            text += '👥 LINKED CITIZENS\n'
            text += '-' * 80 + '\n'
            
            if linked_uids:
                for i, uid_record in enumerate(linked_uids, 1):
                    text += f"\n{i}. UID: {uid_record['UID']}\n"
                    text += f"   Name: {uid_record['name']}\n"
                    text += f"   Mobile: {uid_record['mobile']}\n"
            else:
                text += "No citizens linked to this case\n"
            
            text += '\n' + '=' * 80 + '\n'
            
            self.show_text_window('Case Details', text)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
    
    def register_criminal_case(self):
        """Register or update criminal case with multiple UIDs"""
        case_no = simpledialog.askstring('Case Number', 'Enter Case Number (leave blank for new case):', parent=self)
        if case_no == '':
            case_no = None
        
        try:
            # Check if case already exists
            if case_no:
                self.db.execute(
                    "SELECT CaseNo, offenceType FROM criminalRecord WHERE CaseNo = %s",
                    (case_no,)
                )
                existing_case = self.db.fetchone()
            else:
                existing_case = None
            
            # Create registration window
            reg_window = tk.Toplevel(self)
            reg_window.title('Register Criminal Case')
            reg_window.geometry('600x700')
            reg_window.configure(bg=COLORS['white'])
            
            # Header
            header = tk.Frame(reg_window, bg=COLORS['warning'], height=70)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text='Register Criminal Case',
                font=('Segoe UI', 18, 'bold'),
                bg=COLORS['warning'],
                fg=COLORS['white']
            ).pack(pady=20)
            
            # Content frame with scrollbar
            canvas = tk.Canvas(reg_window, bg=COLORS['white'])
            scrollbar = ttk.Scrollbar(reg_window, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
            
            scrollable_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
            scrollbar.pack(side='right', fill='y')
            
            # Case information section
            if existing_case:
                tk.Label(
                    scrollable_frame,
                    text='📌 EXISTING CASE',
                    font=('Segoe UI', 12, 'bold'),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(0, 10))
                
                tk.Label(
                    scrollable_frame,
                    text=f"Case No: {existing_case['CaseNo']}\nOffence: {existing_case['offenceType']}",
                    font=('Segoe UI', 10),
                    bg=COLORS['light'],
                    fg=COLORS['text'],
                    relief='solid',
                    bd=1,
                    padx=15,
                    pady=10
                ).pack(fill='x', pady=(0, 20))
                
                offence_entry = None
            else:
                tk.Label(
                    scrollable_frame,
                    text='Case Number',
                    font=('Segoe UI', 10),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(0, 5))
                
                case_entry = tk.Entry(scrollable_frame, font=('Segoe UI', 11))
                case_entry.pack(fill='x', pady=(0, 15))
                
                tk.Label(
                    scrollable_frame,
                    text='Offence Type',
                    font=('Segoe UI', 10),
                    bg=COLORS['white'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(0, 5))
                
                offence_entry = tk.Entry(scrollable_frame, font=('Segoe UI', 11))
                offence_entry.pack(fill='x', pady=(0, 20))
            
            # Multiple UIDs section
            tk.Label(
                scrollable_frame,
                text='Add Citizen UIDs (12 digits each)',
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['white'],
                fg=COLORS['text']
            ).pack(anchor='w', pady=(10, 10))
            
            tk.Label(
                scrollable_frame,
                text='Enter UIDs one by one. Click "Add UID" for each citizen.',
                font=('Segoe UI', 9),
                bg=COLORS['white'],
                fg='gray'
            ).pack(anchor='w', pady=(0, 10))
            
            # UID input frame - PLACED BEFORE LISTBOX
            input_frame = tk.Frame(scrollable_frame, bg=COLORS['white'])
            input_frame.pack(fill='x', pady=(0, 5))
            
            tk.Label(
                input_frame,
                text='Enter UID:',
                font=('Segoe UI', 10),
                bg=COLORS['white']
            ).pack(side='left', padx=(0, 10))
            
            uid_entry = tk.Entry(input_frame, font=('Segoe UI', 11), width=18)
            uid_entry.pack(side='left', padx=5)
            
            def add_uid():
                uid = uid_entry.get().strip()
                
                if not uid:
                    messagebox.showwarning('Required', 'Please enter a UID')
                    return
                
                if not uid.isdigit() or len(uid) != 12:
                    messagebox.showerror('Invalid UID', 'UID must be exactly 12 digits')
                    return
                
                # Check if UID already exists in list
                existing_uids = [item.split(' - ')[0] for item in uids_listbox.get(0, tk.END)]
                if uid in existing_uids:
                    messagebox.showwarning('Duplicate', f'UID {uid} already added')
                    return
                
                # Verify UID exists in aadhar
                self.db.execute("SELECT name FROM aadhar WHERE UID = %s", (uid,))
                citizen = self.db.fetchone()
                
                if not citizen:
                    messagebox.showerror('Not Found', f'UID {uid} not found in the system')
                    return
                
                # Add to list with citizen name
                uids_listbox.insert(tk.END, f"{uid} - {citizen['name']}")
                uid_entry.delete(0, tk.END)
                uid_entry.focus()
            
            def remove_uid():
                selection = uids_listbox.curselection()
                if selection:
                    uids_listbox.delete(selection[0])
                else:
                    messagebox.showwarning('Select', 'Please select a UID to remove')
            
            # Add/Remove buttons frame - placed immediately after input
            btn_frame = tk.Frame(scrollable_frame, bg=COLORS['white'])
            btn_frame.pack(fill='x', pady=(0, 15))
            
            tk.Button(
                btn_frame,
                text='➕ Add UID',
                command=add_uid,
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['success'],
                fg='white',
                padx=15,
                pady=8,
                relief='raised',
                cursor='hand2'
            ).pack(side='left', padx=5)
            
            tk.Button(
                btn_frame,
                text='❌ Remove UID',
                command=remove_uid,
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['danger'],
                fg='white',
                padx=15,
                pady=8,
                relief='raised',
                cursor='hand2'
            ).pack(side='left', padx=5)
            
            # UIDs list frame - PLACED AFTER BUTTONS
            uids_frame = tk.Frame(scrollable_frame, bg=COLORS['light'], relief='solid', bd=1, height=120)
            uids_frame.pack(fill='both', expand=True, pady=(0, 15))
            uids_frame.pack_propagate(False)
            
            # Scrollbar for UIDs list
            uids_scrollbar = ttk.Scrollbar(uids_frame)
            uids_scrollbar.pack(side='right', fill='y')
            
            uids_listbox = tk.Listbox(
                uids_frame,
                font=('Segoe UI', 10),
                yscrollcommand=uids_scrollbar.set,
                bg=COLORS['white']
            )
            uids_listbox.pack(side='left', fill='both', expand=True)
            uids_scrollbar.config(command=uids_listbox.yview)
            
            # Submit button in main window
            def submit_case():
                uids = [uid.split(' - ')[0] for uid in uids_listbox.get(0, tk.END)]
                
                if not uids:
                    messagebox.showwarning('Required', 'Please add at least one UID')
                    return
                
                try:
                    if existing_case:
                        # Add UIDs to existing case
                        case_id = existing_case['CaseNo']
                        added_count = 0
                        skipped_count = 0
                        
                        for uid in uids:
                            # Check if UID already linked to this case
                            self.db.execute(
                                "SELECT * FROM criminalRecord_Aadhar WHERE CaseNo = %s AND UID = %s",
                                (case_id, uid)
                            )
                            existing = self.db.fetchone()
                            
                            if not existing:
                                self.db.execute(
                                    "INSERT INTO criminalRecord_Aadhar (CaseNo, UID) VALUES (%s, %s)",
                                    (case_id, uid)
                                )
                                added_count += 1
                            else:
                                skipped_count += 1
                        
                        self.db.commit()
                        
                        messagebox.showinfo(
                            'Success',
                            f'Case Updated Successfully!\n\n'
                            f'Case No: {case_id}\n'
                            f'UIDs Added: {added_count}\n'
                            f'UIDs Already Linked: {skipped_count}'
                        )
                    else:
                        # Create new case
                        case_id = case_entry.get().strip()
                        offence_type = offence_entry.get().strip()
                        
                        if not case_id or not offence_type:
                            messagebox.showwarning('Required', 'Case No and Offence Type are required for new case')
                            return
                        
                        if not case_id.isdigit():
                            messagebox.showerror('Invalid', 'Case No must be numeric')
                            return
                        
                        # Insert new case
                        self.db.execute(
                            "INSERT INTO criminalRecord (CaseNo, offenceType) VALUES (%s, %s)",
                            (case_id, offence_type)
                        )
                        
                        # Link UIDs to case
                        for uid in uids:
                            self.db.execute(
                                "INSERT INTO criminalRecord_Aadhar (CaseNo, UID) VALUES (%s, %s)",
                                (case_id, uid)
                            )
                        
                        self.db.commit()
                        
                        messagebox.showinfo(
                            'Success',
                            f'New Case Registered Successfully!\n\n'
                            f'Case No: {case_id}\n'
                            f'Offence Type: {offence_type}\n'
                            f'Citizens Linked: {len(uids)}'
                        )
                    
                    reg_window.destroy()
                    
                except Error as e:
                    messagebox.showerror('Database Error', str(e))
            
            ModernButton(
                scrollable_frame,
                text='✅ SUBMIT CASE',
                command=submit_case,
                style='success'
            ).pack(fill='x', pady=10)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
    
    def admin_view_photos(self):
        """Admin view all citizen photos"""
        try:
            self.db.execute(
                """SELECT a.UID, a.name, b.has_photo 
                   FROM aadhar a 
                   JOIN biometrics b ON a.UID = b.UID 
                   ORDER BY a.name"""
            )
            citizens = self.db.fetchall()
            
            if not citizens:
                messagebox.showinfo('No Data', 'No citizens found')
                return
            
            # Create window
            photo_window = tk.Toplevel(self)
            photo_window.title('Citizen Photos')
            photo_window.geometry('900x600')
            photo_window.configure(bg=COLORS['light'])
            
            # Header
            header = tk.Frame(photo_window, bg=COLORS['dark'], height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(
                header,
                text='🖼️ Citizen Photos Management',
                font=('Segoe UI', 16, 'bold'),
                bg=COLORS['dark'],
                fg=COLORS['white']
            ).pack(pady=15)
            
            # Table frame
            table_frame = tk.Frame(photo_window, bg=COLORS['white'])
            table_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(table_frame)
            scrollbar.pack(side='right', fill='y')
            
            # Treeview
            columns = ('UID', 'Name', 'Has Photo')
            tree = ttk.Treeview(
                table_frame,
                columns=columns,
                show='headings',
                yscrollcommand=scrollbar.set
            )
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=250)
            
            # Add data
            for citizen in citizens:
                tree.insert(
                    '',
                    'end',
                    values=(
                        citizen['UID'],
                        citizen['name'],
                        'Yes ✓' if citizen['has_photo'] else 'No ✗'
                    )
                )
            
            scrollbar.config(command=tree.yview)
            tree.pack(fill='both', expand=True)
            
            # Button frame
            btn_frame = tk.Frame(photo_window, bg=COLORS['light'])
            btn_frame.pack(fill='x', pady=20)
            
            def view_selected_photo():
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning('Select', 'Please select a citizen first')
                    return
                
                item = tree.item(selection[0])
                uid = item['values'][0]
                has_photo = item['values'][2]
                
                if 'No' in has_photo:
                    messagebox.showinfo('No Photo', 'This citizen has not uploaded a photo')
                    return
                
                try:
                    self.db.execute(
                        "SELECT photo, photo_type FROM biometrics WHERE UID = %s",
                        (uid,)
                    )
                    result = self.db.fetchone()
                    
                    if not result or not result['photo']:
                        messagebox.showerror('Error', 'Photo data not found')
                        return
                    
                    # Get citizen name
                    self.db.execute("SELECT name FROM aadhar WHERE UID = %s", (uid,))
                    citizen = self.db.fetchone()
                    citizen_name = citizen['name'] if citizen else 'Unknown'
                    
                    # Display photo
                    photo_data = result['photo']
                    img = Image.open(io.BytesIO(photo_data))
                    
                    # Create photo display window
                    display_window = tk.Toplevel(self)
                    display_window.title(f'Photo - {citizen_name}')
                    display_window.configure(bg=COLORS['light'])
                    
                    # Header
                    header = tk.Frame(display_window, bg=COLORS['info'], height=60)
                    header.pack(fill='x')
                    header.pack_propagate(False)
                    
                    tk.Label(
                        header,
                        text=f'🖼️ {citizen_name} (UID: {uid})',
                        font=('Segoe UI', 14, 'bold'),
                        bg=COLORS['info'],
                        fg=COLORS['white']
                    ).pack(pady=15)
                    
                    # Resize and display image
                    img.thumbnail((600, 600))
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = tk.Label(display_window, image=photo, bg=COLORS['light'])
                    img_label.image = photo
                    img_label.pack(pady=20, padx=20)
                    
                    # Info
                    tk.Label(
                        display_window,
                        text=f'Type: {result["photo_type"].upper()}',
                        font=('Segoe UI', 10),
                        bg=COLORS['light'],
                        fg=COLORS['dark']
                    ).pack(pady=10)
                    
                    # Close button
                    ModernButton(
                        display_window,
                        text='CLOSE',
                        command=display_window.destroy,
                        style='primary'
                    ).pack(pady=20)
                    
                except Error as e:
                    messagebox.showerror('Database Error', str(e))
                except Exception as e:
                    messagebox.showerror('Error', f'Failed to load photo: {str(e)}')
            
            def refresh_list():
                photo_window.destroy()
                self.admin_view_photos()
            
            # Buttons
            ModernButton(
                btn_frame,
                text='👁️ VIEW PHOTO',
                command=view_selected_photo,
                style='primary'
            ).pack(side='left', padx=10)
            
            ModernButton(
                btn_frame,
                text='🔄 REFRESH',
                command=refresh_list,
                style='secondary'
            ).pack(side='left', padx=10)
            
            ModernButton(
                btn_frame,
                text='❌ CLOSE',
                command=photo_window.destroy,
                style='danger'
            ).pack(side='right', padx=10)
            
        except Error as e:
            messagebox.showerror('Database Error', str(e))
    
    # ==================== UTILITY METHODS ====================
    
    def show_text_window(self, title, text):
        """Display text in a new window"""
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry('700x500')
        win.configure(bg=COLORS['white'])
        
        # Header
        header = tk.Frame(win, bg=COLORS['primary'])
        header.pack(fill='x')
        
        tk.Label(
            header,
            text=title,
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['primary'],
            fg=COLORS['white']
        ).pack(pady=15)
        
        # Text area
        text_widget = scrolledtext.ScrolledText(
            win,
            font=('Consolas', 10),
            wrap='word',
            bg=COLORS['white'],
            fg=COLORS['text']
        )
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
    
    def show_table_window(self, title, rows):
        """Display table in a new window"""
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry('1000x600')
        win.configure(bg=COLORS['white'])
        
        # Header
        header = tk.Frame(win, bg=COLORS['primary'])
        header.pack(fill='x')
        
        tk.Label(
            header,
            text=title,
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['primary'],
            fg=COLORS['white']
        ).pack(pady=15)
        
        if not rows:
            tk.Label(
                win,
                text='No data found',
                font=('Segoe UI', 12),
                bg=COLORS['white'],
                fg=COLORS['text']
            ).pack(pady=50)
            return
        
        # Table frame
        table_frame = tk.Frame(win)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient='vertical')
        hsb = ttk.Scrollbar(table_frame, orient='horizontal')
        
        # Treeview
        cols = list(rows[0].keys())
        tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # Configure columns
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, minwidth=80)
        
        # Insert data
        for row in rows:
            tree.insert('', 'end', values=list(row.values()))
        
        # Pack
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def logout(self):
        """Logout user"""
        self.current_user = None
        self.user_type = None
        self.show_login_screen()


if __name__ == '__main__':
    app = CivilServiceApp()
    app.mainloop()

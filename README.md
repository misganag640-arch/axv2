# Business Payment System - Version 2

## New features added
1. **Admin sets exact payment amount and routine**: monthly, every 2 months, or every 3 months.
2. **Automatic payment schedule** is generated from the assigned plan start date.
3. **Exact amount validation**: payment confirmation rejects a different amount.
4. **Due-date rule**: this version does not allow confirming a payment date before the scheduled due date.
5. **Unpaid and Overdue are separated**:
   - Unpaid = not paid yet, due date has not passed.
   - Overdue = person should have paid but the due date passed.
6. Dashboard now focuses on Active People, Unpaid, Overdue, and Total Paid.
7. Overdue people are listed by name, ID, amount, and due date.
8. Overdue notifications are automatically stored and visible in Notifications.
9. Payment plans are hidden from normal users. Only superuser/admin can see Admin Plans and assign plans.

## Important security recommendation for 3-4 computers
Do NOT try to identify computers only by IP address. The safer design is:
- Computer 1: login with Administrator account.
- Computer 2: login with Administrator account if needed.
- Other computers: login with Staff accounts.

Staff users cannot see the admin payment-plan menu or assign payment plans. Django admin should only be used by the administrator.

If you want strict computer-based access later, add Windows device authentication or a trusted-device system. User permissions are safer for the first version.

## Install
1. Extract ZIP.
2. Open folder in VS Code.
3. Terminal:
   py -m venv .venv
4. Activate:
   .venv\Scripts\Activate.ps1
5. Install:
   pip install -r requirements.txt
6. Create migrations:
   py manage.py makemigrations
7. Apply:
   py manage.py migrate
8. Create admin:
   py manage.py createsuperuser
9. Run:
   py manage.py runserver

Open http://127.0.0.1:8000/

## Local network
After testing, on the server computer:
py manage.py runserver 0.0.0.0:8000

Other computers on the same LAN can use the server computer IPv4 address, for example:
http://192.168.1.20:8000/

For production, replace SQLite with PostgreSQL and use a proper production server.

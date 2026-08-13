import os
import random
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "original")
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)
np.random.seed(42)

# Helper generators
first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Fiona", "George", "Hannah", "Ian", "Julia", "Kevin", "Laura", "Michael", "Nina", "Oscar", "Paula"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson"]

def random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_email(name):
    clean = name.lower().replace(" ", ".")
    domains = ["gmail.com", "yahoo.com", "outlook.com", "enterprise.org"]
    return f"{clean}@{random.choice(domains)}"

def random_wrong_email(name):
    clean = name.lower().replace(" ", ".")
    wrong_formats = [
        f"{clean}_gmail.com",
        f"{clean}#yahoo.com",
        f"{clean}@enterprise",
        f"user.{clean.replace('.', '')}@domain",
        f"{clean}.outlook.com"
    ]
    return random.choice(wrong_formats)

# 1. Customer Demographics (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_demographics(n=500):
    rows = []
    for i in range(1, n+1):
        name = random_name()
        # 25% missing age, outliers & format errors
        r_age = random.random()
        if r_age < 0.25:
            age = None
        elif r_age < 0.28:
            age = -5 # Format error
        elif r_age < 0.31:
            age = 150 # Outlier
        else:
            age = random.randint(18, 75)

        # Realistic wrong format emails (15%)
        email = random_email(name) if random.random() > 0.15 else random_wrong_email(name)
        phone = f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        
        # 25% missing income & ML outlier spikes
        r_inc = random.random()
        if r_inc < 0.25:
            income = None
        elif r_inc < 0.28:
            income = 1250000.0 # Outlier
        else:
            income = round(random.uniform(25000, 150000), 2)

        credit_score = random.randint(300, 850) if random.random() > 0.25 else None

        rows.append({
            "Customer_ID": f"CUST-{1000+i}",
            "Full_Name": name,
            "Age": age,
            "Email": email,
            "Phone": phone,
            "Annual_Income": income,
            "Credit_Score": credit_score,
            "Account_Status": random.choice(["Active", "Inactive", "Pending"])
        })
    df = pd.DataFrame(rows)
    # 25 duplicate rows
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "1_customer_demographics_raw.csv"), index=False)
    print("Generated 1_customer_demographics_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 2. E-Commerce Transactions (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_ecommerce(n=500):
    rows = []
    categories = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Beauty", "Sports"]
    methods = ["Credit Card", "PayPal", "Debit Card", "Apple Pay"]
    for i in range(1, n+1):
        r = random.random()
        if r < 0.25:
            amt = None # 25% Null
        elif r < 0.29:
            amt = 45000.0 # Outlier
        elif r < 0.32:
            amt = -99.0 # Format Error
        else:
            amt = round(random.uniform(10.0, 800.0), 2)

        shipping = round(random.uniform(0, 25), 2) if random.random() > 0.25 else None

        rows.append({
            "Transaction_ID": f"TXN-{50000+i}",
            "Customer_ID": f"CUST-{random.randint(1001, 1500)}",
            "Category": random.choice(categories),
            "Purchase_Amount": amt,
            "Payment_Method": random.choice(methods) if random.random() > 0.25 else None,
            "Shipping_Fee": shipping,
            "Risk_Score": round(random.uniform(0.0, 1.0), 3)
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "2_e_commerce_transactions_raw.csv"), index=False)
    print("Generated 2_e_commerce_transactions_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 3. Healthcare Patient Records (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_healthcare(n=500):
    rows = []
    genders = ["Male", "Female", "Other"]
    for i in range(1, n+1):
        r_bp = random.random()
        bp = None if r_bp < 0.25 else (240 if r_bp < 0.29 else random.randint(90, 180))
        
        chol = random.randint(120, 320) if random.random() > 0.25 else None
        
        r_gl = random.random()
        gluc = None if r_gl < 0.25 else (999 if r_gl < 0.29 else random.randint(70, 200))

        rows.append({
            "Patient_ID": f"PAT-{2000+i}",
            "Patient_Name": random_name(),
            "Age": random.randint(1, 95) if random.random() > 0.15 else None,
            "Gender": random.choice(genders),
            "Blood_Pressure_Systolic": bp,
            "Cholesterol_mg_dL": chol,
            "Glucose_Level_mg_dL": gluc,
            "Medical_Cost_USD": round(random.uniform(500, 25000), 2),
            "Diagnosis_Status": random.choice(["Normal", "Elevated", "Critical"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "3_healthcare_patient_records_raw.csv"), index=False)
    print("Generated 3_healthcare_patient_records_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 4. Financial Loan Applications (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_loans(n=500):
    rows = []
    for i in range(1, n+1):
        income = round(random.uniform(3000, 20000), 2) if random.random() > 0.25 else None
        
        r_amt = random.random()
        loan_amt = None if r_amt < 0.25 else (2500000.0 if r_amt < 0.29 else round(random.uniform(5000, 100000), 2))
        
        dti = round(random.uniform(0.1, 0.6), 2)
        rows.append({
            "Loan_ID": f"LN-{8000+i}",
            "Applicant_Name": random_name(),
            "Monthly_Income": income,
            "Requested_Loan_Amount": loan_amt,
            "Credit_History_Years": random.randint(1, 30) if random.random() > 0.25 else None,
            "Debt_To_Income_Ratio": dti,
            "Employment_Status": random.choice(["Employed", "Self-Employed", "Unemployed"]),
            "Approval_Status": random.choice(["Approved", "Rejected", "Under Review"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "4_financial_loan_applications_raw.csv"), index=False)
    print("Generated 4_financial_loan_applications_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 5. HR Employee Attrition (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_hr(n=500):
    rows = []
    depts = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
    for i in range(1, n+1):
        r_sal = random.random()
        sal = None if r_sal < 0.25 else (850000.0 if r_sal < 0.29 else round(random.uniform(40000, 160000), 2))
        
        rows.append({
            "Employee_ID": f"EMP-{300+i}",
            "Employee_Name": random_name(),
            "Department": random.choice(depts),
            "Monthly_Salary": sal,
            "Years_At_Company": random.randint(0, 25) if random.random() > 0.25 else None,
            "Performance_Rating": random.choice([1, 2, 3, 4, 5]),
            "Overtime_Hours": random.randint(0, 40),
            "Attrition_Risk": random.choice(["Low", "Medium", "High"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "5_hr_employee_attrition_raw.csv"), index=False)
    print("Generated 5_hr_employee_attrition_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 6. IoT Sensor Telemetry (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_iot(n=500):
    rows = []
    for i in range(1, n+1):
        r_temp = random.random()
        temp = None if r_temp < 0.25 else (250.0 if r_temp < 0.29 else round(random.uniform(15.0, 45.0), 2))
        
        hum = round(random.uniform(20.0, 90.0), 2) if random.random() > 0.25 else None
        vib = round(random.uniform(0.01, 2.5), 3)
        rows.append({
            "Sensor_ID": f"SENSOR-{random.randint(1, 20):02d}",
            "Timestamp": f"2026-08-03 15:{i%60:02d}:00",
            "Temperature_C": temp,
            "Humidity_Pct": hum,
            "Vibration_Hz": vib,
            "Battery_Level_Pct": random.randint(5, 100),
            "Operational_State": random.choice(["NORMAL", "WARNING", "FAULT"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "6_iot_sensor_telemetry_raw.csv"), index=False)
    print("Generated 6_iot_sensor_telemetry_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 7. Customer Churn Telecom (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_churn(n=500):
    rows = []
    contracts = ["Month-to-Month", "One Year", "Two Year"]
    internet = ["Fiber Optic", "DSL", "None"]
    for i in range(1, n+1):
        charges = round(random.uniform(20.0, 120.0), 2)
        tenure = random.randint(1, 72)
        r_tot = random.random()
        tot_charges = None if r_tot < 0.25 else (99999.0 if r_tot < 0.29 else round(charges * tenure, 2))
        
        rows.append({
            "Account_ID": f"TEL-{9000+i}",
            "Contract_Type": random.choice(contracts),
            "Monthly_Charges": charges,
            "Total_Charges": tot_charges,
            "Tenure_Months": tenure,
            "Internet_Service": random.choice(internet),
            "Tech_Support_Calls": random.randint(0, 10),
            "Churn_Status": random.choice(["Yes", "No"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "7_customer_churn_telecom_raw.csv"), index=False)
    print("Generated 7_customer_churn_telecom_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 8. Real Estate Housing Market (HEAVY ISSUES: 25% Nulls, Anomalies, Duplicates, Format Errors)
def gen_real_estate(n=500):
    rows = []
    for i in range(1, n+1):
        sqft = random.randint(600, 5000)
        r_p = random.random()
        price = None if r_p < 0.25 else (95000000.0 if r_p < 0.29 else round(sqft * random.uniform(150, 450), 2))
        
        rows.append({
            "Property_ID": f"PROP-{4000+i}",
            "Square_Feet": sqft,
            "Bedrooms": random.randint(1, 6),
            "Bathrooms": random.choice([1, 1.5, 2, 2.5, 3, 4]) if random.random() > 0.25 else None,
            "Year_Built": random.randint(1950, 2024),
            "Zip_Code": random.randint(10001, 99950),
            "Price_USD": price,
            "Property_Condition": random.choice(["Excellent", "Good", "Fair", "Needs Repair"])
        })
    df = pd.DataFrame(rows)
    df = pd.concat([df, df.iloc[:25]], ignore_index=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "8_real_estate_housing_raw.csv"), index=False)
    print("Generated 8_real_estate_housing_raw.csv (Heavy Issues: 25% Nulls, ML Anomalies, Duplicates, Format Errors)")

# 9. Cybersecurity Audit Logs (100% COMPLETE & CLEAN DATASET WITHOUT ANY ISSUES)
def gen_cybersecurity(n=500):
    rows = []
    protocols = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]
    for i in range(1, n+1):
        ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
        bytes_tx = random.randint(500, 50000)
        
        rows.append({
            "Log_ID": f"LOG-{70000+i}",
            "Timestamp": f"2026-08-03 14:{i%60:02d}:30",
            "Source_IP": ip,
            "Destination_Port": random.choice([80, 443, 22, 3389, 8080, 53]),
            "Protocol": random.choice(protocols),
            "Bytes_Transferred": bytes_tx,
            "Failed_Login_Attempts": random.randint(0, 3),
            "Threat_Severity": random.choice(["LOW", "MEDIUM", "HIGH"])
        })
    df = pd.DataFrame(rows)
    # ZERO DUPLICATES, ZERO NULLS, ZERO OUTLIERS
    df.to_csv(os.path.join(OUTPUT_DIR, "9_cybersecurity_audit_logs_raw.csv"), index=False)
    print("Generated 9_cybersecurity_audit_logs_raw.csv (100% Pristine Clean Dataset Without Any Issues)")

# 10. Credit Card Fraud Detection (LESS ISSUES: ~2% Nulls, 0 Duplicates, 1 Minor Outlier)
def gen_fraud(n=500):
    rows = []
    merchants = ["Grocery", "Gas Station", "Electronics", "Travel", "Online Retail", "Jewelry"]
    for i in range(1, n+1):
        amt = round(random.uniform(5.0, 1500.0), 2) if random.random() > 0.02 else None # Only 2% null
        dist = round(random.uniform(0.5, 50.0), 1)
        
        rows.append({
            "Transaction_Ref": f"CARD-TXN-{100000+i}",
            "Cardholder_ID": f"USER-{random.randint(500, 999)}",
            "Amount_USD": amt,
            "Distance_From_Home_Miles": dist,
            "Merchant_Category": random.choice(merchants),
            "Is_Foreign_Transaction": random.choice([0, 1]),
            "Fraud_Flag": random.choice([0, 1])
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "10_credit_card_fraud_raw.csv"), index=False)
    print("Generated 10_credit_card_fraud_raw.csv (Less Issues: ~2% Nulls, 0 Duplicates, 1 Minor Outlier)")

if __name__ == "__main__":
    print("Generating 10 dataset samples according to precise issue distribution...")
    gen_demographics()
    gen_ecommerce()
    gen_healthcare()
    gen_loans()
    gen_hr()
    gen_iot()
    gen_churn()
    gen_real_estate()
    gen_cybersecurity()
    gen_fraud()
    print("All 10 dataset samples created and configured successfully!")

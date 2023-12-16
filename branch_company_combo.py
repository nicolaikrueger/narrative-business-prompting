import pandas as pd
import random

# Define the data for the table
data = [
    ["Technology", "TechGenius Inc. specializes in AI-driven software solutions.", "Global software development companies."],
    ["Healthcare", "MedHealth Systems focuses on telemedicine and remote patient monitoring.", "European healthcare facilities and patients."],
    ["Retail", "EcoRetail Co. offers sustainable, eco-friendly retail solutions.", "Environmentally conscious consumers in North America."],
    ["Renewable Energy", "GreenTech Innovations specializes in solar panel technology.", "Residential and commercial markets in Europe."],
    ["Education", "EduFuture Inc. focuses on virtual reality-based learning tools.", "Global educational institutions and e-learning platforms."],
    ["Agriculture", "AgriSmart Solutions provides advanced IoT-based farming equipment.", "Farmers and agricultural businesses in South America."],
    ["Finance", "FinTech Global offers blockchain solutions for secure financial transactions.", "Banks and financial institutions worldwide."],
    ["Transportation", "MobilityNow develops autonomous vehicle technology for urban transportation.", "Urban areas in Asia and North America."],
    # ... Additional entries would be added here to reach 50 ...
]

# Extending the table to 50 entries by repeating and modifying existing ones
while len(data) < 50:
    for entry in data[:]:
        if len(data) >= 50:
            break
        new_entry = entry.copy()
        new_entry[1] = new_entry[1].replace("specializes", "focuses on").replace("focuses on", "leads in")
        data.append(new_entry)

# Create a DataFrame
df = pd.DataFrame(data, columns=["Branch", "Company Description", "Region/Target Group/Focus Area"])

# Selecting a random case/line
random_case = df.sample()

df, random_case

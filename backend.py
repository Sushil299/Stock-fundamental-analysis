# -*- coding: utf-8 -*-
"""backend

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1UMPFrnSiYVrOpvw5fv4SMpnmB-e-CE9z
"""

import os
import psycopg2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF for PDF text extraction
import google.generativeai as genai

# ✅ Initialize FastAPI
app = FastAPI(title="AI Equity Research API")

# ✅ PostgreSQL Database Connection
DATABASE_URL = os.getenv("DATABASE_URL")  # Set this in Render's environment variables
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# ✅ Ensure Tables Exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS final_analysis (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    analysis_quarter TEXT NOT NULL,
    final_summary TEXT NOT NULL,
    UNIQUE(company_name, analysis_quarter)
);
""")
conn.commit()

# ✅ Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set in Render's environment variables
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Extract Text from PDF Without Storing the File
async def extract_text_from_pdf(file: UploadFile):
    file_bytes = await file.read()  # Read the file asynchronously
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join([page.get_text("text") for page in doc])

# ✅ API: Upload & Process Files
@app.post("/upload/")
async def upload_files(
    company_name: str = Form(...),
    analysis_quarter: str = Form(...),
    quarterly_report: UploadFile = File(None),
    investor_presentation: UploadFile = File(None),
    earnings_call_transcript: UploadFile = File(None)
):
    try:
        # ✅ Open a new connection for this request
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # ✅ Extract text from uploaded PDFs
        report_text = await extract_text_from_pdf(quarterly_report)
        presentation_text = await extract_text_from_pdf(investor_presentation)
        transcript_text = await extract_text_from_pdf(earnings_call_transcript)

        if not any([report_text, presentation_text, transcript_text]):
            raise HTTPException(status_code=400, detail="At least one document must be uploaded.")

        # ✅ Combine all extracted text
        combined_text = f"""
        Quarterly Report:
        {report_text}

        Investor Presentation:
        {presentation_text}

        Earnings Call Transcript:
        {transcript_text}
        """


        # ✅ Generate AI Analysis
        ai_prompt = f"""

        ""You are an AI equity analyst specializing in professional financial research. Given the earnings call transcript, investor presentation, and quarterly results of {company_name}, generate a well-structured, professional-grade equity research report similar to those published by JP Morgan, Goldman Sachs, and Motilal Oswal.
        Your report should be investor-focused, data-driven, and presentable, using Markdown formatting, tables, and charts where applicable to improve readability.

        📊 Investment Research Report: {company_name}
        Analysis Quarter: {analysis_quarter}
        Analyst Rating: (Buy/Hold/Sell) – Provide a clear investment recommendation with justification

        🔹 1. Executive Summary
        Brief overview of the company, its business segments, and industry.
        Key takeaways from the analysis.
        1-line investment recommendation (Buy, Hold, or Sell) with key justification.

        📈 2. Financial Performance Summary
        Present financial metrics like Revenue, EBITDA, Net Profit, EPS, and margins.
        Use a table to show YoY (Year-over-Year) and QoQ (Quarter-over-Quarter) trends.
        Include a bar chart or line graph if a trend is evident.
        📊 Example Table Format:

        Metric	Q3FY25	Q2FY25	YoY Growth (%)	QoQ Growth (%)
        Revenue ($M)	5,000	4,800	+10%	+4%
        EBITDA ($M)	1,200	1,150	+8.7%	+4.3%
        Net Profit ($M)	800	750	+12%	+6.7%
        EPS ($)	3.25	3.10	+15%	+4.8%

        🔑 3. Key Highlights from the Earnings Call
        Major takeaways from management’s commentary.
        Growth drivers, strategic plans, and operational updates.
        Forward-looking guidance or revised outlook provided by management.

        🌍 4. Industry & Macroeconomic Trends
        Current market trends affecting the company’s industry.
        Impact of inflation, interest rates, raw material costs, demand-supply dynamics.
        Competitive positioning and any regulatory updates affecting the company.

        ⚠️ 5. Risks & Challenges
        Company-specific risks: Competition, supply chain disruptions, regulatory challenges.
        Macroeconomic risks: Inflation, global recession fears, geopolitical risks.
        Financial risks: High debt levels, margin pressures, declining sales.

        📊 6. Valuation & Peer Comparison
        Compare the company’s valuation multiples with industry peers.
        Use a table to show P/E, P/B, EV/EBITDA, and PEG ratio comparisons.
        📊 Example Valuation Table:

        Valuation Metric	{company_name}	Industry Average	Top Peer
        P/E Ratio	18.5x	22.3x	20.1x
        P/B Ratio	3.2x	3.5x	3.4x
        EV/EBITDA	12.4x	14.2x	13.1x
        EPS Growth (%)	12%	10%	11%

        🔮 7. Future Growth Outlook & AI-Powered Forecasting
        AI-estimated revenue & profit growth based on historical data and management guidance.
        Future business expansions, product launches, and cost-cutting strategies.
        Projected financial trends (Revenue, EPS, Margins) for the next 1-2 years.
        If possible, generate a line chart to visualize projected growth.

        📌 8. Investment Recommendation & Final Verdict
        Clear Buy / Hold / Sell recommendation based on analysis.
        Justification using financials, valuation, and future growth potential.
        Key catalysts that could drive stock price movement.

        📌 Ensure the analysis is formatted professionally with proper markdown, headings, tables, and charts where applicable.
        📊 Use financial data and structured insights to create a high-quality investment research report."

        **Data Sources:**
        {combined_text}
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(ai_prompt)
        final_analysis = response.text

        # ✅ Store AI-generated report in `final_analysis` table
        cursor.execute("""
            INSERT INTO final_analysis (company_name, analysis_quarter, final_summary)
            VALUES (%s, %s, %s)
            ON CONFLICT (company_name, analysis_quarter) DO UPDATE
            SET final_summary = EXCLUDED.final_summary
        """, (company_name, analysis_quarter, final_analysis))
        conn.commit()

        return {"message": "✅ Files uploaded & AI analysis updated successfully."}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process files: {str(e)}")

# ✅ API: Fetch Precomputed AI Report
@app.get("/summary/{company_name}")
async def get_summary(company_name: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT final_summary FROM final_analysis WHERE company_name = %s", (company_name,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return JSONResponse(content={"final_summary": result[0]})
        else:
            return JSONResponse(content={"error": "No analysis found for this company"}, status_code=404)

    except Exception as e:
        return JSONResponse(content={"error": f"Database error: {str(e)}"}, status_code=500)

# ✅ API: Fetch All Companies
@app.get("/companies")
async def get_companies():
    try:
        conn = psycopg2.connect(DATABASE_URL)  # Open new DB connection
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT company_name FROM final_analysis")
        companies = [row[0] for row in cursor.fetchall()]

        cursor.close()  # Close the cursor properly
        conn.close()  # Close the connection properly

        return {"companies": companies} if companies else {"message": "No companies found."}

    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

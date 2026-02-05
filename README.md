# mobility-credit-indicators

Income mobility and economic context indicators from Census data to identify creditworthy borrowers underserved by traditional credit models.

---

## Overview

This project develops **alternative creditworthiness indicators** using longitudinal Census data and mortgage performance records. The goal is to identify borrowers who appear high-risk under traditional FICO-based criteria but demonstrate strong repayment capacity through income mobility, earnings stability, and favorable local economic conditions.

**Current Status:** Proof-of-concept phase using SQL analysis

**Future Plans:** Automated shell-based data pipeline

---

## Problem Statement

Traditional credit scoring models rely heavily on:
- Current income snapshots
- Credit history length
- Static demographic factors

This approach systematically overlooks creditworthy borrowers with:
- Recent income growth (nonlinear earnings paths)
- Shorter credit histories (young professionals, recent immigrants)
- High geographic mobility
- Strong local economic conditions despite lower current income

---

## Methodology

### Six-Step Framework

#### **Step 1: Define the "Overlooked" Population**
Identify demographic groups likely to score poorly under FICO-based criteria using ACS 5-Year data:
- Lower current income percentiles
- Younger age cohorts (shorter credit history proxy)
- Recent immigrants / high geographic mobility
- Nonlinear income trajectories

#### **Step 2: Construct Longitudinal Economic Context**
Track income and economic changes over time:
- Income mobility (growth, stability, volatility)
- Local labor market trends
- Regional economic trajectories
- Industry mix and employment conditions

#### **Step 3: Engineer Interpretable Indicators**
Translate longitudinal data into transparent creditworthiness signals:
- Income growth consistency
- Earnings stability within local markets
- Exposure to resilient vs. declining regional economies

#### **Step 4: Link Indicators to Mortgage Performance**
Associate demographic/geographic indicators with observed loan outcomes using HMDA and GSE datasets:
- Default and delinquency rates
- Performance comparison across similar FICO proxies
- Validation of alternative indicators

#### **Step 5: Identify Creditworthy but Underserved Groups**
Systematically identify populations that:
- Appear high-risk under FICO-like proxies
- Exhibit strong income mobility and favorable trends
- Demonstrate comparable or better mortgage performance

#### **Step 6: Evaluate Incremental Value**
Assess whether alternative indicators:
- Add explanatory power beyond traditional variables
- Reduce borrower misclassification
- Improve inclusion without increasing default risk

---

## Data Sources

### Primary Datasets
- **American Community Survey (ACS) 5-Year Estimates** (2010-2023)
  - PUMS microdata for individual-level analysis
  - Multiple vintages for longitudinal tracking
- **Home Mortgage Disclosure Act (HMDA)** loan-level data
- **GSE Performance Data** (Fannie Mae/Freddie Mac)
  - Loan performance and default records

### Supplementary Data
- Bureau of Labor Statistics local area unemployment
- Census Bureau County Business Patterns
- HUD Fair Market Rents (housing cost context)

---

## Repository Structure
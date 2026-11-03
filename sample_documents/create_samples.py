import os
from pathlib import Path
import docx
import pypdf

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

# 1. Create Employee Leave Policy (DOCX)
def create_leave_policy_docx():
    doc = docx.Document()
    doc.add_heading("Global Enterprise Employee Leave Policy", level=0)

    doc.add_heading("1. Purpose and Scope", level=1)
    doc.add_paragraph("This policy outlines the guidelines, entitlement, and procedures for taking leave for all full-time and part-time enterprise staff.")

    doc.add_heading("2. Paid Time Off (PTO) and Vacation", level=1)
    doc.add_paragraph("Employees are allocated 20 paid vacation days per calendar year. Vacation balances accrue on a monthly pro-rata basis.")
    doc.add_paragraph("Employees can request paid time off through the HR portal. Requests exceeding three consecutive days must be submitted at least two weeks in advance.")

    doc.add_heading("3. Sick Leave and Medical Care", level=1)
    doc.add_paragraph("Staff members are entitled to 10 days of paid sick leave annually. Medical certificates are mandatory for consecutive absences exceeding two days.")

    doc.add_heading("4. Parental and Bereavement Leave", level=1)
    doc.add_paragraph("Eligible primary caregivers receive up to 16 weeks of paid parental leave. The enterprise grants 5 days of paid bereavement leave for immediate family members.")

    path = SAMPLE_DIR / "Employee_Leave_Policy.docx"
    doc.save(str(path))
    print(f"Created {path}")

# 2. Create Security Guidelines (TXT)
def create_security_txt():
    content = """ENTERPRISE CYBERSECURITY AND ACCESS CONTROL GUIDELINES
Document Version: 2.4 | Classification: Enterprise-Internal

1. Authentication & Multi-Factor Security
All employees, contractors, and partners must authenticate through the centralized Single Sign-On (SSO) gateway. Multi-factor authentication (MFA) using hardware security keys or authenticator apps is mandatory for all access. SMS-based authentication is strictly prohibited.

2. Hardware and Device Encryption
All corporate laptops and mobile endpoints must have full disk encryption enabled via BitLocker (Windows) or FileVault (macOS). Unencrypted USB flash drives are strictly prohibited on corporate networks.

3. Incident Response and Reporting
If an employee suspects a phishing attack, credential compromise, or device theft, they must immediately contact the Security Operations Center (SOC) at security@enterprise.ai or dial the urgent hotline at extension 9110 within 30 minutes.

4. Data Retention and Privacy
Customer identifiable information (PII) must be stored in encrypted database clusters with automated 90-day key rotation. Exporting raw customer datasets to local machines without DPO authorization violates enterprise governance."""

    path = SAMPLE_DIR / "Enterprise_Security_Guidelines.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")

# 3. Create Project Apollo Technical Spec (TXT)
def create_apollo_txt():
    content = """PROJECT APOLLO: CLOUD-NATIVE ARCHITECTURE SPECIFICATION
Engineering Team: Core Systems | Release Target: October 15, 2026

1. Executive Summary & Main Objectives
Project Apollo re-engineers our legacy enterprise backend into a high-throughput, distributed event-driven platform. The primary objectives are reducing search query latency to under 50ms, achieving 99.99% uptime, and providing real-time vector indexing for organizational knowledge assets.

2. Architecture Methodology
Apollo adheres to Domain-Driven Design (DDD) with asynchronous microservices built on Python and Go. Inter-service messaging is facilitated via Apache Kafka with schema validation provided by Protobuf.

3. Search and Semantic Retrieval
The search tier utilizes hybrid retrieval combining FAISS dense vector search with BM25 Okapi lexical indexing. Candidate passages undergo reciprocal rank fusion (RRF) and cross-encoder reranking prior to large language model context ingestion.

4. Deployment and DevOps
Continuous integration and continuous deployment (CI/CD) pipelines deploy containers to Kubernetes clusters across multiple availability zones. Canary releases ensure zero downtime during production updates."""

    path = SAMPLE_DIR / "Project_Apollo_Architecture.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")

if __name__ == "__main__":
    create_leave_policy_docx()
    create_security_txt()
    create_apollo_txt()

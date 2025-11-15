-- ============================================
-- SQL Query: Person with Maximum Bank Accounts AND Criminal Records
-- ============================================
-- This query finds citizens with the highest combined count of bank accounts and criminal records
-- ============================================

-- OPTION 1: Person with MOST bank accounts + criminal records combined
SELECT 
    a.UID,
    a.name,
    a.mobile,
    COUNT(DISTINCT ba.AccNo) as total_bank_accounts,
    COUNT(DISTINCT cra.CaseNo) as total_criminal_cases,
    (COUNT(DISTINCT ba.AccNo) + COUNT(DISTINCT cra.CaseNo)) as combined_count
FROM aadhar a
LEFT JOIN bankAccount ba ON a.UID = ba.UID
LEFT JOIN criminalRecord_Aadhar cra ON a.UID = cra.UID
GROUP BY a.UID, a.name, a.mobile
HAVING total_bank_accounts > 0 AND total_criminal_cases > 0
ORDER BY combined_count DESC, total_bank_accounts DESC, total_criminal_cases DESC
LIMIT 1;


-- OPTION 2: Using subquery to find maximum counts
SELECT 
    a.UID,
    a.name,
    a.mobile,
    bank_count,
    crime_count,
    (bank_count + crime_count) as total_count
FROM aadhar a
JOIN (
    SELECT UID, COUNT(*) as bank_count
    FROM bankAccount
    GROUP BY UID
) ba ON a.UID = ba.UID
JOIN (
    SELECT UID, COUNT(*) as crime_count
    FROM criminalRecord_Aadhar
    GROUP BY UID
) cr ON a.UID = cr.UID
ORDER BY total_count DESC, bank_count DESC, crime_count DESC
LIMIT 1;


-- OPTION 3: Find person with BOTH maximum bank accounts AND maximum criminal records
-- (Person who has the highest in BOTH categories)
SELECT 
    a.UID,
    a.name,
    a.mobile,
    ba.bank_count,
    cr.crime_count
FROM aadhar a
JOIN (
    SELECT UID, COUNT(*) as bank_count
    FROM bankAccount
    GROUP BY UID
    HAVING COUNT(*) = (
        SELECT MAX(account_count)
        FROM (
            SELECT COUNT(*) as account_count
            FROM bankAccount
            GROUP BY UID
        ) AS max_accounts
    )
) ba ON a.UID = ba.UID
JOIN (
    SELECT UID, COUNT(*) as crime_count
    FROM criminalRecord_Aadhar
    GROUP BY UID
    HAVING COUNT(*) = (
        SELECT MAX(crime_count)
        FROM (
            SELECT COUNT(*) as crime_count
            FROM criminalRecord_Aadhar
            GROUP BY UID
        ) AS max_crimes
    )
) cr ON a.UID = cr.UID;


-- OPTION 4: Multiple rows if there's a tie (all people with max combined count)
SELECT 
    a.UID,
    a.name,
    a.mobile,
    COUNT(DISTINCT ba.AccNo) as total_bank_accounts,
    COUNT(DISTINCT cra.CaseNo) as total_criminal_cases,
    (COUNT(DISTINCT ba.AccNo) + COUNT(DISTINCT cra.CaseNo)) as combined_count
FROM aadhar a
LEFT JOIN bankAccount ba ON a.UID = ba.UID
LEFT JOIN criminalRecord_Aadhar cra ON a.UID = cra.UID
GROUP BY a.UID, a.name, a.mobile
HAVING combined_count = (
    SELECT MAX(total)
    FROM (
        SELECT (COUNT(DISTINCT ba2.AccNo) + COUNT(DISTINCT cra2.CaseNo)) as total
        FROM aadhar a2
        LEFT JOIN bankAccount ba2 ON a2.UID = ba2.UID
        LEFT JOIN criminalRecord_Aadhar cra2 ON a2.UID = cra2.UID
        GROUP BY a2.UID
        HAVING COUNT(DISTINCT ba2.AccNo) > 0 AND COUNT(DISTINCT cra2.CaseNo) > 0
    ) AS max_combined
);


-- OPTION 5: With detailed account and crime information
SELECT 
    a.UID,
    a.name,
    a.mobile,
    COUNT(DISTINCT ba.AccNo) as total_bank_accounts,
    COUNT(DISTINCT cra.CaseNo) as total_criminal_cases,
    GROUP_CONCAT(DISTINCT ba.bankName ORDER BY ba.bankName SEPARATOR ', ') as banks,
    GROUP_CONCAT(DISTINCT cr.offenceType ORDER BY cr.offenceType SEPARATOR ', ') as offences
FROM aadhar a
LEFT JOIN bankAccount ba ON a.UID = ba.UID
LEFT JOIN criminalRecord_Aadhar cra ON a.UID = cra.UID
LEFT JOIN criminalRecord cr ON cra.CaseNo = cr.CaseNo
GROUP BY a.UID, a.name, a.mobile
HAVING total_bank_accounts > 0 AND total_criminal_cases > 0
ORDER BY (total_bank_accounts + total_criminal_cases) DESC
LIMIT 1;


-- ============================================
-- RECOMMENDED: OPTION 1 (Simplest and most efficient)
-- Use this if you want the person with the highest combined total
-- ============================================

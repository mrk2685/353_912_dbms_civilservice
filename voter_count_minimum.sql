-- ============================================
-- Stored Procedure: Get Citizens with Minimum Voter ID Count
-- ============================================
-- Purpose: Retrieve citizens who have equal to or more than a specified number of Voter IDs
-- Parameters: min_count (INT) - Minimum number of Voter IDs
-- Returns: UID, Name, Total Voter IDs, and all their Voter Details (EPIC, Address)
-- ============================================

DELIMITER $$

CREATE PROCEDURE get_citizens_minimum_voterids(IN min_count INT)
READS SQL DATA
BEGIN
    SELECT 
        a.UID,
        a.name,
        a.mobile,
        COUNT(v.EPIC) as total_voter_ids,
        GROUP_CONCAT(
            CONCAT('EPIC: ', v.EPIC, ' | Address: ', v.address, ' | Status: ', v.Status)
            SEPARATOR ' || '
        ) as voter_details
    FROM aadhar a
    JOIN votedID v ON a.UID = v.UID
    GROUP BY a.UID, a.name, a.mobile
    HAVING COUNT(v.EPIC) >= min_count
    ORDER BY total_voter_ids DESC, a.name ASC;
END$$

DELIMITER ;

-- ============================================
-- Testing the Procedure
-- ============================================
-- To test, run this query:
-- CALL get_citizens_minimum_voterids(2);
-- This will return all citizens with 2 or more Voter IDs

-- ============================================
-- Notes
-- ============================================
-- 1. Change min_count to any number to filter by minimum voter IDs
-- 2. The procedure shows: UID, Name, Mobile, Total Count, and all voter details
-- 3. GROUP_CONCAT combines all voter information for easy viewing
-- 4. Results are sorted by total voter IDs (descending) then by name
-- 5. Only shows active relationships (joined tables guarantee voter IDs exist)


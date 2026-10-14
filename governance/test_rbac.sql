\echo === 1. TelcoCo tenant: only its own rows ===
SET ROLE u_telcoco;
SELECT client, count(*) FROM gold.fct_telemetry GROUP BY 1;
SELECT DISTINCT client FROM gold.dim_asset;
\echo --- masked schema (expect permission denied) ---
SELECT * FROM masked.dim_asset_owner_masked LIMIT 1;
RESET ROLE;

\echo === 2. EnergyCo tenant ===
SET ROLE u_energyco;
SELECT client, count(*) FROM gold.fct_telemetry GROUP BY 1;
RESET ROLE;

\echo === 3. Analyst: all clients, masked data, no restricted ===
SET ROLE u_analyst;
SELECT client, count(*) FROM gold.fct_telemetry GROUP BY 1 ORDER BY 1;
SELECT count(*) AS masked_rows FROM masked.dim_asset_owner_masked;
\echo --- restricted schema (expect permission denied) ---
SELECT * FROM restricted.asset_owner_restricted LIMIT 1;
RESET ROLE;

\echo === 4. Governance: sees restricted PII ===
SET ROLE u_governance;
SELECT count(*) AS restricted_rows FROM restricted.asset_owner_restricted;
RESET ROLE;

-- ===== 1) Roles =====
DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY[
    'role_governance','role_analyst','role_tenant',
    'u_governance','u_analyst','u_telcoco','u_energyco','u_govnet'
  ]
  LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN', r);
    END IF;
  END LOOP;
END $$;

GRANT role_analyst TO role_governance;
GRANT role_governance TO u_governance;
GRANT role_analyst TO u_analyst;
GRANT role_tenant TO u_telcoco, u_energyco, u_govnet;

-- ===== 2) Schema and table privileges =====
GRANT USAGE ON SCHEMA gold TO role_analyst, role_tenant;
GRANT USAGE ON SCHEMA masked TO role_analyst;
GRANT USAGE ON SCHEMA restricted TO role_governance;

GRANT SELECT ON ALL TABLES IN SCHEMA gold TO role_analyst, role_tenant;
GRANT SELECT ON ALL TABLES IN SCHEMA masked TO role_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA restricted TO role_governance;

-- ===== 3) Row-Level Security on the Gold tables =====
ALTER TABLE gold.dim_asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.fct_telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.fct_asset_health_5min ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  t text;
  tenant record;
BEGIN
  FOREACH t IN ARRAY ARRAY['dim_asset','fct_telemetry','fct_asset_health_5min']
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS analyst_all ON gold.%I', t);
    EXECUTE format(
      'CREATE POLICY analyst_all ON gold.%I FOR SELECT TO role_analyst USING (true)', t);

    FOR tenant IN
      SELECT * FROM (VALUES
        ('u_telcoco','TelcoCo'),
        ('u_energyco','EnergyCo'),
        ('u_govnet','GovNet')
      ) AS v(usr, client)
    LOOP
      EXECUTE format('DROP POLICY IF EXISTS tenant_%s ON gold.%I', tenant.usr, t);
      EXECUTE format(
        'CREATE POLICY tenant_%s ON gold.%I FOR SELECT TO %I USING (client = %L)',
        tenant.usr, t, tenant.usr, tenant.client);
    END LOOP;
  END LOOP;
END $$;
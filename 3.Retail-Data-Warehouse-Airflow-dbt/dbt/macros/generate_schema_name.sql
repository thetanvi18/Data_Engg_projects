-- macros/generate_schema_name.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Overrides dbt's default schema naming to use the custom_schema_name directly
-- (without prepending the target schema / project name).
--
-- This ensures:
--   +schema: gold   → creates models in 'gold' schema
--   +schema: silver → creates models in 'silver' schema
--   (Not 'retail_user_gold' or 'silver_retail_user')
-- ─────────────────────────────────────────────────────────────────────────────

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

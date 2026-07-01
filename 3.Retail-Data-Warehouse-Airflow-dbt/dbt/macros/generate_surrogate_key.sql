-- macros/generate_surrogate_key.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Generates a consistent MD5-based surrogate key from one or more columns.
-- Usage: {{ generate_surrogate_key(['col1', 'col2']) }}
-- ─────────────────────────────────────────────────────────────────────────────

{% macro generate_surrogate_key(field_list) %}
    md5(
        CAST(
            CONCAT_WS(
                '||',
                {% for field in field_list %}
                    COALESCE(CAST({{ field }} AS VARCHAR), '_null_')
                    {%- if not loop.last %}, {% endif %}
                {% endfor %}
            ) AS VARCHAR
        )
    )
{% endmacro %}

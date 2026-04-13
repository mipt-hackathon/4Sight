/*
Purpose:
  Build notebook-backed ABC/XYZ customer classifications and retention strategies.

Expected inputs:
  - clean.orders
  - clean.order_items

Expected outputs:
  - mart.abc_xyz

Grain:
  - one row per user_id
*/

DROP TABLE IF EXISTS mart.abc_xyz;

CREATE TABLE mart.abc_xyz AS
WITH analysis_source AS (
    SELECT
        oi.order_item_id,
        oi.user_id,
        oi.order_id,
        oi.product_id,
        oi.category,
        COALESCE(oi.sale_price, 0)::NUMERIC(14, 2) AS sale_price,
        COALESCE(oi.cost, 0)::NUMERIC(14, 2) AS cost,
        o.created_at,
        o.returned_at
    FROM clean.order_items AS oi
    JOIN clean.orders AS o
        ON o.order_id = oi.order_id
),
snapshot AS (
    SELECT MAX(created_at) AS current_date
    FROM analysis_source
),
abc_ranked AS (
    SELECT
        user_id,
        total_value,
        SUM(total_value) OVER (
            ORDER BY total_value DESC, user_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_value,
        100.0 * SUM(total_value) OVER (
            ORDER BY total_value DESC, user_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / NULLIF(SUM(total_value) OVER (), 0) AS cumulative_percent
    FROM (
        SELECT
            user_id,
            SUM(sale_price)::NUMERIC(14, 2) AS total_value
        FROM analysis_source
        GROUP BY user_id
    ) AS totals
),
abc_results AS (
    SELECT
        user_id,
        total_value AS total_revenue,
        cumulative_value AS abc_cumulative_revenue,
        ROUND(cumulative_percent::NUMERIC, 2) AS abc_cumulative_percent,
        CASE
            WHEN cumulative_percent <= 20 THEN 'A'
            WHEN cumulative_percent <= 50 THEN 'B'
            ELSE 'C'
        END AS abc_category
    FROM abc_ranked
),
purchase_freq AS (
    SELECT
        source.user_id,
        COUNT(DISTINCT source.order_id) AS order_count,
        COALESCE(SUM(source.sale_price), 0)::NUMERIC(14, 2) AS total_revenue,
        COALESCE(SUM(source.sale_price - source.cost), 0)::NUMERIC(14, 2) AS total_profit,
        MIN(source.created_at) AS first_purchase,
        MAX(source.created_at) AS last_purchase,
        (MAX(source.created_at)::date - MIN(source.created_at)::date) AS customer_lifetime_days,
        CASE
            WHEN COUNT(DISTINCT source.order_id) > 1 THEN ROUND(
                (
                    (MAX(source.created_at)::date - MIN(source.created_at)::date)::NUMERIC
                    / (COUNT(DISTINCT source.order_id) - 1)
                ),
                2
            )
            ELSE NULL
        END AS avg_days_between_orders,
        CASE
            WHEN COUNT(DISTINCT source.order_id) = 0 THEN 0::NUMERIC(14, 2)
            ELSE ROUND(SUM(source.sale_price) / COUNT(DISTINCT source.order_id), 2)
        END AS avg_order_value,
        COUNT(*) FILTER (WHERE source.returned_at IS NOT NULL) AS return_count,
        CASE
            WHEN COUNT(DISTINCT source.order_id) = 0 THEN 0::NUMERIC(10, 4)
            ELSE ROUND(
                (COUNT(*) FILTER (WHERE source.returned_at IS NOT NULL))::NUMERIC
                / COUNT(DISTINCT source.order_id),
                4
            )
        END AS return_rate,
        (snapshot.current_date::date - MAX(source.created_at)::date) AS recency_days,
        COUNT(DISTINCT source.category) AS category_diversity,
        abc.abc_category,
        abc.abc_cumulative_revenue,
        abc.abc_cumulative_percent
    FROM analysis_source AS source
    CROSS JOIN snapshot
    JOIN abc_results AS abc
        ON abc.user_id = source.user_id
    GROUP BY
        source.user_id,
        snapshot.current_date,
        abc.abc_category,
        abc.abc_cumulative_revenue,
        abc.abc_cumulative_percent
),
order_timing AS (
    SELECT
        user_id,
        CASE
            WHEN COUNT(day_gap) = 0 THEN 0::NUMERIC(14, 4)
            ELSE ROUND(
                COALESCE(STDDEV_SAMP(day_gap), 0)
                / NULLIF(AVG(day_gap), 0),
                4
            )
        END AS purchase_regularity
    FROM (
        SELECT
            user_id,
            EXTRACT(
                DAY FROM (
                    created_at - LAG(created_at) OVER (
                        PARTITION BY user_id
                        ORDER BY created_at, order_item_id
                    )
                )
            ) AS day_gap
        FROM analysis_source
    ) AS timed_orders
    GROUP BY user_id
),
user_monthly_avg AS (
    SELECT
        user_id,
        EXTRACT(MONTH FROM created_at)::INT AS month_created,
        AVG(sale_price)::NUMERIC(14, 4) AS avg_sale_price
    FROM analysis_source
    GROUP BY user_id, EXTRACT(MONTH FROM created_at)::INT
),
trend_by_user AS (
    SELECT
        user_id,
        COALESCE(ROUND(AVG(trend)::NUMERIC, 4), 0::NUMERIC(14, 4)) AS avg_trend
    FROM (
        SELECT
            user_id,
            (
                avg_sale_price - LAG(avg_sale_price) OVER (
                    PARTITION BY user_id
                    ORDER BY month_created
                )
            ) / NULLIF(
                LAG(avg_sale_price) OVER (
                    PARTITION BY user_id
                    ORDER BY month_created
                ),
                0
            ) AS trend
        FROM user_monthly_avg
    ) AS monthly_trends
    GROUP BY user_id
),
purchase_freq_enriched AS (
    SELECT
        purchase_freq.*,
        COALESCE(order_timing.purchase_regularity, 0::NUMERIC(14, 4)) AS purchase_regularity,
        COALESCE(trend_by_user.avg_trend, 0::NUMERIC(14, 4)) AS avg_trend,
        CASE
            WHEN order_count >= 10 THEN 'Очень частые (10+)'
            WHEN order_count >= 5 THEN 'Частые (5-9)'
            WHEN order_count >= 2 THEN 'Регулярные (2-4)'
            ELSE 'Разовые (1)'
        END AS frequency_category,
        CASE
            WHEN recency_days > 60 THEN 1
            ELSE 0
        END AS churn
    FROM purchase_freq
    LEFT JOIN order_timing
        ON order_timing.user_id = purchase_freq.user_id
    LEFT JOIN trend_by_user
        ON trend_by_user.user_id = purchase_freq.user_id
),
user_monthly_sales AS (
    SELECT
        user_id,
        date_trunc('month', created_at)::date AS year_month,
        SUM(sale_price)::NUMERIC(14, 2) AS sale_price,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(sale_price - cost)::NUMERIC(14, 2) AS profit
    FROM analysis_source
    GROUP BY user_id, date_trunc('month', created_at)::date
),
active_users AS (
    SELECT
        user_id,
        COUNT(*) AS month_count
    FROM user_monthly_sales
    GROUP BY user_id
    HAVING COUNT(*) >= 3
),
xyz_stats AS (
    SELECT
        user_monthly_sales.user_id,
        active_users.month_count,
        ROUND(AVG(user_monthly_sales.sale_price), 2) AS avg_sales,
        ROUND(COALESCE(STDDEV_SAMP(user_monthly_sales.sale_price), 0)::NUMERIC, 2) AS std_sales,
        ROUND(AVG(user_monthly_sales.order_count::NUMERIC), 2) AS avg_orders,
        ROUND(COALESCE(STDDEV_SAMP(user_monthly_sales.order_count::NUMERIC), 0)::NUMERIC, 2) AS std_orders,
        ROUND(AVG(user_monthly_sales.profit), 2) AS avg_profit,
        ROUND(COALESCE(STDDEV_SAMP(user_monthly_sales.profit), 0)::NUMERIC, 2) AS std_profit,
        COALESCE(
            COALESCE(STDDEV_SAMP(user_monthly_sales.sale_price), 0)
            / NULLIF(AVG(user_monthly_sales.sale_price), 0),
            0
        ) AS cv_sales,
        COALESCE(
            COALESCE(STDDEV_SAMP(user_monthly_sales.order_count::NUMERIC), 0)
            / NULLIF(AVG(user_monthly_sales.order_count::NUMERIC), 0),
            0
        ) AS cv_orders,
        CASE
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(user_monthly_sales.sale_price), 0)
                / NULLIF(AVG(user_monthly_sales.sale_price), 0),
                0
            ) < 0.3 THEN 'X (стабильные)'
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(user_monthly_sales.sale_price), 0)
                / NULLIF(AVG(user_monthly_sales.sale_price), 0),
                0
            ) < 0.7 THEN 'Y (средние)'
            ELSE 'Z (нестабильные)'
        END AS xyz_sales_category,
        CASE
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(user_monthly_sales.order_count::NUMERIC), 0)
                / NULLIF(AVG(user_monthly_sales.order_count::NUMERIC), 0),
                0
            ) < 0.3 THEN 'X (стабильные)'
            WHEN COALESCE(
                COALESCE(STDDEV_SAMP(user_monthly_sales.order_count::NUMERIC), 0)
                / NULLIF(AVG(user_monthly_sales.order_count::NUMERIC), 0),
                0
            ) < 0.7 THEN 'Y (средние)'
            ELSE 'Z (нестабильные)'
        END AS xyz_orders_category
    FROM user_monthly_sales
    JOIN active_users
        ON active_users.user_id = user_monthly_sales.user_id
    GROUP BY user_monthly_sales.user_id, active_users.month_count
),
combined AS (
    SELECT
        purchase_freq_enriched.user_id,
        purchase_freq_enriched.order_count,
        purchase_freq_enriched.total_revenue,
        purchase_freq_enriched.total_profit,
        purchase_freq_enriched.first_purchase,
        purchase_freq_enriched.last_purchase,
        purchase_freq_enriched.customer_lifetime_days,
        purchase_freq_enriched.avg_days_between_orders,
        purchase_freq_enriched.avg_order_value,
        purchase_freq_enriched.return_count,
        purchase_freq_enriched.return_rate,
        purchase_freq_enriched.recency_days,
        purchase_freq_enriched.purchase_regularity,
        purchase_freq_enriched.avg_trend,
        purchase_freq_enriched.category_diversity,
        purchase_freq_enriched.frequency_category,
        purchase_freq_enriched.churn,
        purchase_freq_enriched.abc_category,
        purchase_freq_enriched.abc_cumulative_revenue,
        purchase_freq_enriched.abc_cumulative_percent,
        COALESCE(xyz_stats.month_count, 0) AS month_count,
        xyz_stats.avg_sales,
        xyz_stats.std_sales,
        xyz_stats.avg_orders,
        xyz_stats.std_orders,
        xyz_stats.avg_profit,
        xyz_stats.std_profit,
        ROUND(COALESCE(xyz_stats.cv_sales, 0)::NUMERIC, 4) AS cv_sales,
        ROUND(COALESCE(xyz_stats.cv_orders, 0)::NUMERIC, 4) AS cv_orders,
        COALESCE(xyz_stats.xyz_sales_category, 'Z (нестабильные)') AS xyz_sales_category,
        xyz_stats.xyz_orders_category
    FROM purchase_freq_enriched
    LEFT JOIN xyz_stats
        ON xyz_stats.user_id = purchase_freq_enriched.user_id
)
SELECT
    user_id,
    order_count,
    total_revenue,
    total_profit,
    first_purchase,
    last_purchase,
    customer_lifetime_days,
    avg_days_between_orders,
    avg_order_value,
    return_count,
    return_rate,
    recency_days,
    purchase_regularity,
    avg_trend,
    category_diversity,
    frequency_category,
    churn,
    abc_category,
    abc_cumulative_revenue,
    abc_cumulative_percent,
    month_count,
    avg_sales,
    std_sales,
    avg_orders,
    std_orders,
    avg_profit,
    std_profit,
    cv_sales,
    cv_orders,
    xyz_sales_category,
    xyz_orders_category,
    CONCAT(abc_category, '|', xyz_sales_category) AS strategy_key,
    CASE
        WHEN abc_category = 'A' AND xyz_sales_category = 'X (стабильные)' THEN
            E'🔒 Элитные лояльные клиенты\n• VIP программа\n• Персональный менеджер\n• Эксклюзивные предложения'
        WHEN abc_category = 'A' AND xyz_sales_category = 'Y (средние)' THEN
            E'📈 Ценные, но нестабильные\n• Апсейл и кросс-продажи\n• Программа лояльности\n• Регулярные коммуникации'
        WHEN abc_category = 'A' AND xyz_sales_category = 'Z (нестабильные)' THEN
            E'⚠️ Высокий риск потери VIP\n• Срочная реактивация\n• Персональные скидки\n• Анализ причин нестабильности'
        WHEN abc_category = 'B' AND xyz_sales_category = 'X (стабильные)' THEN
            E'📊 Надежный средний сегмент\n• Увеличение среднего чека\n• Кросс-продажи\n• Автоматические рекомендации'
        WHEN abc_category = 'B' AND xyz_sales_category = 'Y (средние)' THEN
            E'🎯 Перспективные клиенты\n• Таргетированные акции\n• Email-маркетинг\n• Тестирование офферов'
        WHEN abc_category = 'B' AND xyz_sales_category = 'Z (нестабильные)' THEN
            E'🔄 Нестабильные средние\n• Анализ поведения\n• Вовлекающие кампании\n• Сезонные предложения'
        WHEN abc_category = 'C' AND xyz_sales_category = 'X (стабильные)' THEN
            E'💎 Стабильные, но с низким чеком\n• Upsell до категории B\n• Пакетные предложения\n• Экономия ресурсов'
        WHEN abc_category = 'C' AND xyz_sales_category = 'Y (средние)' THEN
            E'📧 Низкий чек, средняя стабильность\n• Email-маркетинг\n• Автоматизация\n• Минимальные инвестиции'
        WHEN abc_category = 'C' AND xyz_sales_category = 'Z (нестабильные)' THEN
            E'❌ Одноразовые/хаотичные\n• Не тратить ресурсы\n• Только массовые акции\n• Анализ целесообразности'
        ELSE '❓ Стратегия не определена'
    END AS recommended_strategy
FROM combined
ORDER BY user_id;

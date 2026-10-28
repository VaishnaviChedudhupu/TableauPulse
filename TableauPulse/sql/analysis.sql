-- 1. Sales and profit by category

USE tableaupulse;
SELECT COUNT(*) AS total_rows
FROM superstore;
SELECT
    Category,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY Category
ORDER BY Total_Profit DESC;

-- 2. Sales and profit by region
SELECT
    Region,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY Region
ORDER BY Total_Profit DESC;

-- 3. Sales and profit by shipping mode
SELECT
    Ship_Mode,
    COUNT(*) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY Ship_Mode
ORDER BY Profit_Margin_Percent DESC;
USE tableaupulse;

-- 4. Profit analysis by subcategory
SELECT
    Sub_Category,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY Sub_Category
ORDER BY Total_Profit ASC;
-- 5. Analyze how discounts affect profit
SELECT
    Discount,
    COUNT(*) AS Total_Records,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(AVG(Profit), 2) AS Avg_Profit_Per_Record
FROM superstore
GROUP BY Discount
ORDER BY Discount;
6. Identify best and worst performing subcategories
SELECT
    Sub_Category,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(AVG(Discount), 2) AS Avg_Discount
FROM superstore
GROUP BY Sub_Category
ORDER BY Total_Profit;
USE tableaupulse;

-- 7. Monthly sales and profit trends
SELECT
    DATE_FORMAT(Order_Date, '%Y-%m') AS Order_Month,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY DATE_FORMAT(Order_Date, '%Y-%m')
ORDER BY Order_Month;
USE tableaupulse;

-- 8. Top 10 most profitable customers
SELECT
    Customer_ID,
    Customer_Name,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit
FROM superstore
GROUP BY Customer_ID, Customer_Name
ORDER BY Total_Profit DESC
LIMIT 10;
-- 9. Top 10 loss-making products
SELECT
    Product_ID,
    Product_Name,
    SUM(Quantity) AS Total_Quantity,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit
FROM superstore
GROUP BY Product_ID, Product_Name
HAVING SUM(Profit) < 0
ORDER BY Total_Profit ASC
LIMIT 10;
USE tableaupulse;

-- 10. Discount levels and profitability
SELECT
    Discount,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(AVG(Profit), 2) AS Avg_Profit_Per_Record
FROM superstore
GROUP BY Discount
ORDER BY Discount;
USE tableaupulse;

-- 11. Sales and profit by customer segment
SELECT
    Segment,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY Segment
ORDER BY Total_Profit DESC;
USE tableaupulse;

-- 12. Sales and profit by state
SELECT
    State,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    ROUND(SUM(Sales), 2) AS Total_Sales,
    ROUND(SUM(Profit), 2) AS Total_Profit,
    ROUND(
        SUM(Profit) / NULLIF(SUM(Sales), 0) * 100,
        2
    ) AS Profit_Margin_Percent
FROM superstore
GROUP BY State
ORDER BY Total_Profit DESC;
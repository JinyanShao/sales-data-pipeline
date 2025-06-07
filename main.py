# -*- coding: utf-8 -*-
# Python Foundational Project: Data Operations & Workflow Concepts
# This project demonstrates basic data handling and analytical workflow using Python.

# 第一步：导入必要的库
# Step 1: Import necessary libraries
import pandas as pd # 导入pandas库，通常简称为pd
import io # 导入io模块，用于处理内存中的数据流，模拟文件读取

print("--- Python 数据操作与工作流概念项目 ---")
print("--- Python Data Operations & Workflow Concepts Project ---")

# 第二步：模拟一个小型数据集 (可以理解为从Excel或数据库读取的数据)
# Step 2: Simulate a small dataset (imagine reading from Excel or a database)
# 这里我们用一个字符串来模拟CSV文件的内容
csv_data = """
OrderID,CustomerID,Product,Quantity,Price
1001,C001,Laptop,1,1200
1002,C002,Mouse,2,25
1003,C001,Keyboard,1,75
1004,C003,Monitor,1,300
1005,C002,Laptop,1,1200
"""
# 使用io.StringIO将字符串数据转换为类文件对象，pandas可以直接读取
df = pd.read_csv(io.StringIO(csv_data)) # 使用pandas的read_csv函数读取模拟数据，并存储到DataFrame中

print("\n原始数据 (Original Data):")
print(df) # 打印原始DataFrame的内容

# 第三步：数据清洗与转换 (Data Cleaning & Transformation)
# Step 3: Data Cleaning & Transformation
# 计算每一行的总销售额 (Total Sales for each row)
df['Total Sales'] = df['Quantity'] * df['Price'] # 创建一个新列'Total Sales'

print("\n添加了总销售额列后的数据 (Data with 'Total Sales' column):")
print(df) # 打印添加新列后的DataFrame

# 第四步：基本数据分析 (Basic Data Analysis)
# Step 4: Basic Data Analysis
# 找出总销售额最高的订单 (Find the order with the highest total sales)
highest_sales_order = df.loc[df['Total Sales'].idxmax()] # idxmax() 返回最大值的索引，loc用于按索引获取行
print("\n总销售额最高的订单 (Order with highest total sales):")
print(highest_sales_order) # 打印最高销售额订单的信息

# 统计每个客户的总购买金额 (Calculate total purchase amount per customer)
customer_total_purchase = df.groupby('CustomerID')['Total Sales'].sum().reset_index() # 按CustomerID分组，对'Total Sales'求和
customer_total_purchase.rename(columns={'Total Sales': 'Total Spent'}, inplace=True) # 重命名列
print("\n每个客户的总购买金额 (Total purchase amount per customer):")
print(customer_total_purchase) # 打印每个客户的总购买金额

# 第五步：简单的数据导出模拟 (Simulate simple data export)
# Step 5: Simulate simple data export
output_filename = "customer_purchase_summary.csv"
customer_total_purchase.to_csv(output_filename, index=False) # 将结果导出到CSV文件，不包含索引

print(f"\n数据已导出至 {output_filename}") # 打印导出成功信息
print("项目执行完毕。") # 项目结束提示

# 个人目标声明 (Personal Goal Statement - from previous version)
goal = "我的目标是在IT领域不断学习和成长，未来成为一名优秀的软件工程师或数据科学家。"
print(f"\n我的目标是：{goal}")
print("--- 项目结束 ---")

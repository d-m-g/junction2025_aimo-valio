# Valio Aimo Junction 2025 data set

## Sales orders

File `valio_aimo_sales_and_deliveries_junction_2025.csv` contains a set of sales order rows with delivery and picking information for a period of 1 year. It is to be noted that a sales order row might have several deliveries and a delivery might have several transfer orders. A delivery groups all qualifying orders together for logistics purposes (picking, shipment) and a transfer order represent a picking list. Typically these are 1:1:1 but in some cases not. Field delivered_qty has the total delivered quantity of a sales order row.

## Replacement orders

File `valio_aimo_replacement_orders_junction_2025.csv` has a set of replacement orders for the duration of 1 year. These represent orders manually created by staff to cover shortages occurred in picking. A row might contain a replacement product for something that we were not able to deliver or in some cases the same product as new order row if it became available again after picking was already confirmed as zero. It is to be noted that these orders do not have a relation to the original sales orders but the product codes and customer numbers match the sales order data. Delivery and picking fields are present in this file as well, showing that sometimes even the replacement orders fall short of requested quantities.

## Purchase orders

File `valio_aimo_purchases_junction_2025.csv` contains a set purchase order rows and their received quantities for the duration of 1 year. Product codes match the ones in sales order & replacement order data. Some order rows are received in multiple batches in which case the same purchase order row appears several times in the data.

## Product data

File `valio_aimo_product_data_junction_2025.json` contains extensive product information that can be used to find related / replacing products. This data set is separate from the others so these products can't be linked to purchase / sales data. Data originates from manufacturers and quantity / quality varies: for example factory-made meals with a GTIN code will typically contain precise nutritional and allergen information but for example fruits and vegetables are lacking most of this